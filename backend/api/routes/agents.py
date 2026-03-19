"""Agent CRUD API routes"""
from fastapi import APIRouter, HTTPException, Request
from core.models import AgentCreate, IntentRequest
from agents.builder import agent_builder
from agents.intent_engine import intent_engine
from analytics.tracker import analytics_tracker
from mining.pattern_miner import pattern_miner

router = APIRouter()


@router.post("/generate")
async def generate_agent(request: Request, data: IntentRequest):
    """Generate and save an agent from task description"""
    rag = request.app.state.rag
    
    # Get RAG context
    rag_context = await rag.augment_query(
        f"{data.department} {data.role} {data.task_description}",
        department=data.department
    )
    
    # Extract intent
    intent = await intent_engine.extract_intent(
        data.department, data.role, data.task_description, rag_context
    )
    
    # Generate blueprint
    blueprint = await agent_builder.generate_blueprint(
        department=data.department,
        role=data.role,
        task=data.task_description,
        rag_context=rag_context,
        intent=str(intent)
    )
    
    # Save agent
    agent_id = await agent_builder.save_agent(blueprint)
    
    # Add to RAG knowledge base
    agent_data = await agent_builder.get_agent(agent_id)
    await rag.add_agent_to_kb(agent_data)
    
    # Record pattern
    await pattern_miner.record_task(data.department, data.role, data.task_description)
    
    # Track analytics
    await analytics_tracker.track_event(
        "agent_created", agent_id=agent_id,
        department=data.department, role=data.role,
        metadata={"task": data.task_description[:100]}
    )
    
    return {"agent_id": agent_id, "blueprint": blueprint.model_dump(), "intent": intent}


@router.get("/")
async def list_agents(department: str = None):
    agents = await agent_builder.list_agents(department)
    return {"agents": agents, "total": len(agents)}


@router.get("/{agent_id}")
async def get_agent(agent_id: str):
    agent = await agent_builder.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


@router.delete("/{agent_id}")
async def delete_agent(agent_id: str):
    await agent_builder.delete_agent(agent_id)
    return {"status": "deleted", "agent_id": agent_id}
