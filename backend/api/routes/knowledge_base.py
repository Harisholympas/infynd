"""Knowledge Base API Routes - Upload, manage, and search custom company data"""
from fastapi import APIRouter, UploadFile, File, HTTPException, Request
from typing import List, Dict, Any
import json
from rag.knowledge_base import KnowledgeBaseManager
from pydantic import BaseModel

router = APIRouter(prefix="/api/knowledge-base", tags=["knowledge_base"])

# Initialize KB manager
kb_manager = KnowledgeBaseManager()

class KnowledgeBaseCreateRequest(BaseModel):
    name: str
    description: str = ""
    company_id: str = "default"

@router.on_event("startup")
async def startup():
    """Initialize knowledge base tables"""
    await kb_manager.initialize_db()


@router.post("/create")
async def create_knowledge_base(data: KnowledgeBaseCreateRequest) -> Dict[str, str]:
    """Create a new knowledge base"""
    try:
        kb_id = await kb_manager.create_knowledge_base(data.name, data.description, data.company_id)
        return {
            "status": "success",
            "kb_id": kb_id,
            "message": f"Knowledge base '{data.name}' created successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/upload-document/{kb_id}")
async def upload_document(
    request: Request,
    kb_id: str,
    file: UploadFile = File(...),
    doc_type: str = "text"
) -> Dict[str, Any]:
    """Upload a document to knowledge base"""
    try:
        # Read file content
        content = await file.read()
        
        # Handle different file types
        if file.filename.endswith('.pdf'):
            # For PDF, would need PDF parsing library
            text_content = content.decode('utf-8', errors='ignore')
        elif file.filename.endswith('.txt'):
            text_content = content.decode('utf-8')
        elif file.filename.endswith('.json'):
            data = json.loads(content.decode('utf-8'))
            text_content = json.dumps(data, indent=2)
        else:
            text_content = content.decode('utf-8', errors='ignore')
        
        # Add to KB
        doc_id = await kb_manager.add_document(
            kb_id=kb_id,
            title=file.filename,
            content=text_content,
            doc_type=doc_type
        )

        # Ingest into RAG pipeline so agents/workflows can use it immediately
        rag = getattr(request.app.state, "rag", None)
        if rag:
            await rag.ingest_text(
                text_content,
                metadata={
                    "id": f"kb_{kb_id}_{doc_id}",
                    "title": file.filename,
                    "department": "",
                    "type": f"knowledge_base:{doc_type}",
                },
            )
        
        return {
            "status": "success",
            "doc_id": doc_id,
            "filename": file.filename,
            "message": f"Document '{file.filename}' uploaded successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/upload-batch/{kb_id}")
async def upload_batch_documents(
    request: Request,
    kb_id: str,
    documents: List[Dict[str, str]]
) -> Dict[str, Any]:
    """Upload multiple documents at once"""
    try:
        doc_ids = await kb_manager.add_multiple_documents(kb_id, documents)

        rag = getattr(request.app.state, "rag", None)
        if rag:
            for i, doc in enumerate(documents):
                content = doc.get("content", "")
                title = doc.get("title", f"Batch Document {i+1}")
                if content:
                    await rag.ingest_text(
                        content,
                        metadata={
                            "id": f"kb_{kb_id}_{doc_ids[i] if i < len(doc_ids) else i}",
                            "title": title,
                            "department": doc.get("department", "") or "",
                            "type": f"knowledge_base:{doc.get('doc_type','text')}",
                        },
                    )
        return {
            "status": "success",
            "doc_ids": doc_ids,
            "count": len(doc_ids),
            "message": f"Uploaded {len(doc_ids)} documents successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/search/{kb_id}")
async def search_knowledge_base(
    kb_id: str,
    query: str,
    top_k: int = 5
) -> Dict[str, Any]:
    """Search knowledge base"""
    try:
        results = await kb_manager.search_knowledge_base(kb_id, query, top_k)
        return {
            "status": "success",
            "query": query,
            "results": results,
            "count": len(results)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{kb_id}")
async def get_knowledge_base(kb_id: str) -> Dict[str, Any]:
    """Get knowledge base metadata and statistics"""
    try:
        kb = await kb_manager.get_knowledge_base(kb_id)
        if not kb:
            raise HTTPException(status_code=404, detail="Knowledge base not found")
        return {
            "status": "success",
            "knowledge_base": kb
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/list/{company_id}")
async def list_knowledge_bases(company_id: str) -> Dict[str, Any]:
    """List all knowledge bases for a company"""
    try:
        kbs = await kb_manager.list_knowledge_bases(company_id)
        return {
            "status": "success",
            "knowledge_bases": kbs,
            "count": len(kbs)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{kb_id}")
async def delete_knowledge_base(kb_id: str) -> Dict[str, str]:
    """Delete a knowledge base and all its documents"""
    try:
        success = await kb_manager.delete_knowledge_base(kb_id)
        if success:
            return {
                "status": "success",
                "message": f"Knowledge base {kb_id} deleted successfully"
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to delete knowledge base")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/export/{kb_id}")
async def export_knowledge_base(kb_id: str) -> Dict[str, Any]:
    """Export knowledge base as JSON"""
    try:
        exported = await kb_manager.export_knowledge_base(kb_id)
        if exported:
            return {
                "status": "success",
                "data": exported
            }
        else:
            raise HTTPException(status_code=404, detail="Knowledge base not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/import")
async def import_knowledge_base(
    kb_id: str,
    data: Dict[str, Any]
) -> Dict[str, str]:
    """Import knowledge base from exported JSON"""
    try:
        kb = data.get('knowledge_base', {})
        documents = data.get('documents', [])
        
        # Create KB if needed
        if not await kb_manager.get_knowledge_base(kb_id):
            kb_id = await kb_manager.create_knowledge_base(
                kb.get('name', 'Imported KB'),
                kb.get('description', ''),
                kb.get('company_id', 'default')
            )
        
        # Add documents
        doc_ids = await kb_manager.add_multiple_documents(kb_id, documents)
        
        return {
            "status": "success",
            "kb_id": kb_id,
            "imported_documents": len(doc_ids),
            "message": f"Imported {len(doc_ids)} documents successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/query-with-rag")
async def query_with_rag(
    query: str,
    kb_id: str,
    context_limit: int = 5
) -> Dict[str, Any]:
    """Query knowledge base and enhance with RAG"""
    try:
        # Search KB
        kb_results = await kb_manager.search_knowledge_base(kb_id, query, context_limit)
        
        # Optionally enhance with LLM
        context = "\n".join([r['content'] for r in kb_results])
        
        return {
            "status": "success",
            "query": query,
            "context": context,
            "sources": kb_results,
            "source_count": len(kb_results)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
