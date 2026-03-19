"""RAG query routes"""
from fastapi import APIRouter, Request
from core.models import RAGQueryRequest
from pydantic import BaseModel

router = APIRouter()


class IngestRequest(BaseModel):
    text: str
    title: str
    department: str = ""
    doc_type: str = "text"


@router.post("/query")
async def query_rag(request: Request, data: RAGQueryRequest):
    rag = request.app.state.rag
    results = await rag.query(data.query, data.department, data.top_k)
    augmented = await rag.augment_query(data.query, data.department)
    return {"query": data.query, "results": results, "augmented_context": augmented[:1000]}


@router.post("/ingest")
async def ingest_document(request: Request, data: IngestRequest):
    rag = request.app.state.rag
    result = await rag.ingest_text(data.text, {
        "title": data.title, "department": data.department, 
        "type": data.doc_type, "id": data.title.lower().replace(" ", "_")
    })
    return {"status": "ingested", "result": result}


@router.get("/stats")
async def rag_stats(request: Request):
    rag = request.app.state.rag
    doc_count = len(rag.store.documents) if rag.store else 0
    return {"document_count": doc_count, "status": "active"}
