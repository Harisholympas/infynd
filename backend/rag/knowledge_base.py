"""Knowledge Base Manager - Handle custom data upload and vector DB for RAG"""
import json
import logging
import uuid
from pathlib import Path
from typing import List, Dict, Any, Optional
import aiosqlite
from datetime import datetime
from core.database import DB_PATH

logger = logging.getLogger(__name__)

try:
    import numpy as np
    import faiss
    HAS_VECTOR_SUPPORT = True
except ImportError:
    HAS_VECTOR_SUPPORT = False
    logger.warning("FAISS/NumPy not available, vector operations disabled")


class KnowledgeBaseManager:
    """Manages custom knowledge bases with vector embeddings"""
    
    def __init__(self):
        self.vector_store = None
        self.documents = []
        self.kb_path = Path("data/knowledge_bases")
        self.kb_path.mkdir(parents=True, exist_ok=True)
    
    async def initialize_db(self):
        """Create knowledge base tables"""
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS knowledge_bases (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    company_id TEXT,
                    created_at TEXT,
                    updated_at TEXT,
                    metadata TEXT
                )
            """)
            
            await db.execute("""
                CREATE TABLE IF NOT EXISTS kb_documents (
                    id TEXT PRIMARY KEY,
                    kb_id TEXT NOT NULL,
                    title TEXT,
                    content TEXT,
                    doc_type TEXT,
                    embedding TEXT,
                    created_at TEXT,
                    FOREIGN KEY (kb_id) REFERENCES knowledge_bases(id)
                )
            """)
            
            await db.execute("""
                CREATE TABLE IF NOT EXISTS kb_chunks (
                    id TEXT PRIMARY KEY,
                    doc_id TEXT NOT NULL,
                    chunk_text TEXT,
                    embedding TEXT,
                    chunk_order INTEGER,
                    FOREIGN KEY (doc_id) REFERENCES kb_documents(id)
                )
            """)
            
            await db.commit()
            logger.info("Knowledge base tables created")
    
    async def create_knowledge_base(self, name: str, description: str, company_id: str) -> str:
        """Create a new knowledge base"""
        kb_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("""
                INSERT INTO knowledge_bases (id, name, description, company_id, created_at, updated_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (kb_id, name, description, company_id, now, now, json.dumps({})))
            await db.commit()
        
        logger.info(f"Created knowledge base: {name} ({kb_id})")
        return kb_id
    
    async def add_document(self, kb_id: str, title: str, content: str, doc_type: str = "text") -> str:
        """Add a document to knowledge base with chunks and embeddings"""
        doc_id = str(uuid.uuid4())
        
        # Chunk the document
        chunks = self._chunk_text(content)
        
        async with aiosqlite.connect(DB_PATH) as db:
            # Save document
            await db.execute("""
                INSERT INTO kb_documents (id, kb_id, title, content, doc_type, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (doc_id, kb_id, title, content, doc_type, datetime.utcnow().isoformat()))
            
            # Save chunks with embeddings
            for i, chunk in enumerate(chunks):
                chunk_id = str(uuid.uuid4())
                embedding = await self._get_embedding(chunk)
                
                await db.execute("""
                    INSERT INTO kb_chunks (id, doc_id, chunk_text, embedding, chunk_order)
                    VALUES (?, ?, ?, ?, ?)
                """, (chunk_id, doc_id, chunk, embedding, i))
            
            await db.commit()
        
        logger.info(f"Added document: {title} to KB {kb_id} with {len(chunks)} chunks")
        return doc_id
    
    async def add_multiple_documents(self, kb_id: str, documents: List[Dict[str, str]]) -> List[str]:
        """Add multiple documents at once"""
        doc_ids = []
        for doc in documents:
            doc_id = await self.add_document(
                kb_id, 
                doc.get("title", "Untitled"), 
                doc.get("content", ""),
                doc.get("type", "text")
            )
            doc_ids.append(doc_id)
        return doc_ids
    
    async def search_knowledge_base(self, kb_id: str, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search knowledge base for relevant documents"""
        query_embedding = await self._get_embedding(query)
        
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            
            # Get all chunks from KB
            cursor = await db.execute("""
                SELECT kc.id, kc.chunk_text, kc.embedding, kd.title, kd.id as doc_id
                FROM kb_chunks kc
                JOIN kb_documents kd ON kc.doc_id = kd.id
                WHERE kd.kb_id = ?
            """, (kb_id,))
            
            rows = await cursor.fetchall()
            
            # Score by similarity
            results = []
            for row in rows:
                embedding = json.loads(row['embedding']) if row['embedding'] else []
                similarity = self._cosine_similarity(query_embedding, embedding)
                results.append({
                    "chunk_id": row['id'],
                    "doc_id": row['doc_id'],
                    "title": row['title'],
                    "content": row['chunk_text'],
                    "similarity": similarity
                })
            
            # Sort by similarity and return top_k
            results.sort(key=lambda x: x['similarity'], reverse=True)
            return results[:top_k]
    
    async def get_knowledge_base(self, kb_id: str) -> Optional[Dict]:
        """Get knowledge base metadata and stats"""
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM knowledge_bases WHERE id = ?", (kb_id,)
            )
            kb = await cursor.fetchone()
            
            if kb:
                kb_dict = dict(kb)
                kb_dict['metadata'] = json.loads(kb_dict.get('metadata', '{}'))
                
                # Get stats
                doc_cursor = await db.execute(
                    "SELECT COUNT(*) as count FROM kb_documents WHERE kb_id = ?", (kb_id,)
                )
                doc_count = await doc_cursor.fetchone()
                kb_dict['document_count'] = doc_count['count']
                
                return kb_dict
        
        return None
    
    async def list_knowledge_bases(self, company_id: str) -> List[Dict]:
        """List all knowledge bases for a company"""
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM knowledge_bases WHERE company_id = ? ORDER BY created_at DESC",
                (company_id,)
            )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    def _chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 100) -> List[str]:
        """Split text into overlapping chunks"""
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            chunks.append(chunk.strip())
            start = end - overlap
        
        return [c for c in chunks if len(c) > 50]  # Filter out small chunks
    
    async def _get_embedding(self, text: str) -> str:
        """Get embedding for text (mock implementation - use real model in production)"""
        try:
            from core.llm import llm_client
            # In production, use actual embedding model
            embedding = [0.1] * 384  # Mock embedding
            return json.dumps(embedding)
        except Exception as e:
            logger.warning(f"Failed to get embedding: {e}")
            return json.dumps([0.0] * 384)
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between vectors"""
        if not HAS_VECTOR_SUPPORT or not vec1 or not vec2:
            return 0.0
        
        a = np.array(vec1, dtype=np.float32)
        b = np.array(vec2, dtype=np.float32)
        
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
        
        return float(np.dot(a, b) / (norm_a * norm_b))
    
    async def delete_knowledge_base(self, kb_id: str) -> bool:
        """Delete a knowledge base and all its documents"""
        async with aiosqlite.connect(DB_PATH) as db:
            # Delete chunks
            await db.execute("DELETE FROM kb_chunks WHERE doc_id IN (SELECT id FROM kb_documents WHERE kb_id = ?)", (kb_id,))
            # Delete documents
            await db.execute("DELETE FROM kb_documents WHERE kb_id = ?", (kb_id,))
            # Delete knowledge base
            await db.execute("DELETE FROM knowledge_bases WHERE id = ?", (kb_id,))
            await db.commit()
        
        logger.info(f"Deleted knowledge base: {kb_id}")
        return True
    
    async def export_knowledge_base(self, kb_id: str) -> Dict:
        """Export knowledge base as JSON"""
        kb = await self.get_knowledge_base(kb_id)
        if not kb:
            return {}
        
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM kb_documents WHERE kb_id = ?", (kb_id,)
            )
            documents = [dict(row) for row in await cursor.fetchall()]
        
        return {
            "knowledge_base": kb,
            "documents": documents,
            "exported_at": datetime.utcnow().isoformat()
        }
