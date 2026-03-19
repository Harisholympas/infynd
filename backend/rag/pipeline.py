"""RAG Pipeline - Retrieval Augmented Generation using FAISS + local embeddings"""
import json
import logging
import pickle
from pathlib import Path
from typing import List, Optional, Dict, Any
from core.config import settings
from core.llm import llm_client

logger = logging.getLogger(__name__)

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    logger.warning("NumPy not available, RAG disabled")

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    logger.warning("FAISS not available, using simple vector search")


class SimpleVectorStore:
    """Fallback vector store when FAISS is unavailable"""
    
    def __init__(self):
        self.vectors = []
        self.documents = []
    
    def add(self, vector: list, doc: dict):
        self.vectors.append(np.array(vector, dtype=np.float32))
        self.documents.append(doc)
    
    def search(self, query_vector: list, k: int = 5) -> List[Dict]:
        if not self.vectors:
            return []
        q = np.array(query_vector, dtype=np.float32)
        scores = []
        for i, v in enumerate(self.vectors):
            # Cosine similarity
            norm = np.linalg.norm(q) * np.linalg.norm(v)
            score = float(np.dot(q, v) / norm) if norm > 0 else 0.0
            scores.append((score, i))
        scores.sort(reverse=True)
        return [{"score": s, **self.documents[i]} for s, i in scores[:k]]
    
    def save(self, path: str):
        with open(path, "wb") as f:
            pickle.dump({"vectors": self.vectors, "documents": self.documents}, f)
    
    def load(self, path: str):
        with open(path, "rb") as f:
            data = pickle.load(f)
            self.vectors = data["vectors"]
            self.documents = data["documents"]


class RAGPipeline:
    """Full RAG pipeline for department knowledge augmentation"""
    
    def __init__(self):
        self.vector_db_path = Path(settings.VECTOR_DB_PATH)
        self.kb_path = Path(settings.KNOWLEDGE_BASE_PATH)
        self.store = None
        self.index_path = self.vector_db_path / "index.pkl"
    
    async def initialize(self):
        """Initialize the RAG pipeline"""
        self.vector_db_path.mkdir(parents=True, exist_ok=True)
        self.kb_path.mkdir(parents=True, exist_ok=True)
        
        self.store = SimpleVectorStore()
        
        if self.index_path.exists():
            try:
                self.store.load(str(self.index_path))
                logger.info(f"Loaded {len(self.store.documents)} documents from index")
            except Exception as e:
                logger.error(f"Failed to load index: {e}")
        
        # Index any new documents in knowledge base
        await self._index_knowledge_base()
    
    async def _index_knowledge_base(self):
        """Index all documents in the knowledge base directory"""
        docs_added = 0
        for doc_file in self.kb_path.glob("*.json"):
            try:
                with open(doc_file) as f:
                    docs = json.load(f)
                if isinstance(docs, list):
                    for doc in docs:
                        await self._add_document(doc)
                        docs_added += 1
                elif isinstance(docs, dict):
                    await self._add_document(docs)
                    docs_added += 1
            except Exception as e:
                logger.error(f"Error indexing {doc_file}: {e}")
        
        if docs_added > 0:
            self.store.save(str(self.index_path))
            logger.info(f"Indexed {docs_added} documents")
    
    async def _add_document(self, doc: dict):
        """Add a single document to the vector store"""
        text = self._doc_to_text(doc)
        embedding = await llm_client.embed(text)
        self.store.add(embedding, {
            "id": doc.get("id", str(len(self.store.documents))),
            "title": doc.get("title", ""),
            "department": doc.get("department", ""),
            "type": doc.get("type", "document"),
            "content": text[:500],
            "full_content": text
        })
    
    def _doc_to_text(self, doc: dict) -> str:
        """Convert document to searchable text"""
        parts = []
        for key in ["title", "department", "role", "description", "content", 
                    "steps", "tools", "workflow", "best_practices"]:
            if key in doc:
                val = doc[key]
                if isinstance(val, list):
                    parts.append(f"{key}: {', '.join(str(v) for v in val)}")
                elif val:
                    parts.append(f"{key}: {val}")
        return " | ".join(parts)
    
    async def query(self, query: str, department: Optional[str] = None, 
                    top_k: int = 5) -> List[Dict[str, Any]]:
        """Query the vector store"""
        if not self.store or not self.store.documents:
            return []
        
        embedding = await llm_client.embed(query)
        results = self.store.search(embedding, k=top_k)
        
        # Filter by department if specified
        if department:
            dept_results = [r for r in results if r.get("department", "").lower() == department.lower()]
            if dept_results:
                results = dept_results
        
        return results
    
    async def augment_query(self, query: str, department: Optional[str] = None) -> str:
        """Retrieve relevant context and augment the query"""
        results = await self.query(query, department, top_k=settings.TOP_K_RESULTS)
        
        if not results:
            return query
        
        context_parts = []
        for r in results:
            context_parts.append(f"[{r.get('title', 'Document')}]: {r.get('content', '')}")
        
        augmented = f"""User Query: {query}

Relevant Knowledge Base Context:
{chr(10).join(context_parts)}

Based on the above context, please provide an enhanced response."""
        
        return augmented
    
    async def add_agent_to_kb(self, agent_data: dict):
        """Add a newly created agent to the knowledge base for future RAG queries"""
        await self._add_document({
            "id": f"agent_{agent_data.get('id', '')}",
            "title": f"Agent: {agent_data.get('name', '')}",
            "department": agent_data.get('department', ''),
            "type": "agent",
            "content": json.dumps(agent_data.get('blueprint', {}))
        })
        self.store.save(str(self.index_path))
    
    async def ingest_text(self, text: str, metadata: dict) -> str:
        """Ingest raw text into the knowledge base"""
        chunks = self._chunk_text(text, settings.CHUNK_SIZE, settings.CHUNK_OVERLAP)
        for i, chunk in enumerate(chunks):
            doc = {
                "id": f"{metadata.get('id', 'doc')}_{i}",
                "title": metadata.get("title", "Document"),
                "department": metadata.get("department", ""),
                "type": metadata.get("type", "text"),
                "content": chunk
            }
            await self._add_document(doc)
        self.store.save(str(self.index_path))
        return f"Ingested {len(chunks)} chunks"
    
    def _chunk_text(self, text: str, chunk_size: int, overlap: int) -> List[str]:
        """Split text into overlapping chunks"""
        words = text.split()
        chunks = []
        i = 0
        while i < len(words):
            chunk = " ".join(words[i:i+chunk_size])
            chunks.append(chunk)
            i += chunk_size - overlap
        return chunks if chunks else [text]
