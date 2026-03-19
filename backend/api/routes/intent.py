"""Intent extraction routes"""
from fastapi import APIRouter, Request
from core.models import IntentRequest
from agents.intent_engine import intent_engine

router = APIRouter()


@router.post("/extract")
async def extract_intent(request: Request, data: IntentRequest):
    """Extract structured intent from task description"""
    rag = request.app.state.rag
    rag_context = await rag.augment_query(
        f"{data.department} {data.role} {data.task_description}",
        department=data.department
    )
    intent = await intent_engine.extract_intent(
        data.department, data.role, data.task_description, rag_context
    )
    return {"intent": intent, "rag_context": rag_context[:500]}
