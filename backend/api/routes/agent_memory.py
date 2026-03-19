"""Agent Memory Persistence API Routes - Resume execution, access memory, track history"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, Optional
from memory.persistent import AgentPersistentMemory

router = APIRouter(prefix="/api/agent-memory", tags=["agent_memory"])

# Initialize memory manager
memory = AgentPersistentMemory()


@router.on_event("startup")
async def startup():
    """Initialize agent memory tables"""
    await memory.initialize_db()


# ── Execution State Management ──

@router.post("/save-state")
async def save_execution_state(
    agent_id: str,
    workflow_id: str,
    state: Dict[str, Any],
    current_step: int,
    total_steps: int
) -> Dict[str, Any]:
    """Save agent execution state for later resumption"""
    try:
        state_id = await memory.save_execution_state(
            agent_id, workflow_id, state, current_step, total_steps
        )
        
        return {
            "status": "success",
            "state_id": state_id,
            "agent_id": agent_id,
            "progress": f"{current_step}/{total_steps}",
            "message": "Execution state saved successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/pause/{state_id}")
async def pause_execution(state_id: str) -> Dict[str, Any]:
    """Pause an ongoing execution"""
    try:
        await memory.pause_execution(state_id)
        
        return {
            "status": "success",
            "state_id": state_id,
            "message": "Execution paused successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/resume/{state_id}")
async def resume_execution(state_id: str) -> Dict[str, Any]:
    """Resume a paused execution from where it left off"""
    try:
        state = await memory.resume_execution(state_id)
        
        if not state:
            raise HTTPException(status_code=404, detail="Execution state not found")
        
        return {
            "status": "success",
            "state_id": state_id,
            "agent_id": state['agent_id'],
            "workflow_id": state['workflow_id'],
            "current_step": state['current_step'],
            "total_steps": state['total_steps'],
            "state": state,
            "message": "Execution resumed successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/complete/{state_id}")
async def complete_execution(
    state_id: str,
    final_output: Dict[str, Any]
) -> Dict[str, Any]:
    """Mark execution as completed"""
    try:
        await memory.complete_execution(state_id, final_output)
        
        return {
            "status": "success",
            "state_id": state_id,
            "message": "Execution completed successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── Pattern Learning ──

@router.post("/record-pattern")
async def record_successful_pattern(
    agent_id: str,
    pattern_type: str,
    pattern_data: Dict[str, Any],
    success_rate: float
) -> Dict[str, Any]:
    """Record a successful pattern for reuse"""
    try:
        pattern_id = await memory.record_successful_pattern(
            agent_id, pattern_type, pattern_data, success_rate
        )
        
        return {
            "status": "success",
            "pattern_id": pattern_id,
            "agent_id": agent_id,
            "pattern_type": pattern_type,
            "message": "Pattern recorded successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/learned-patterns/{agent_id}")
async def get_learned_patterns(
    agent_id: str,
    pattern_type: Optional[str] = None
) -> Dict[str, Any]:
    """Get learned patterns for an agent"""
    try:
        patterns = await memory.get_learned_patterns(agent_id, pattern_type)
        
        return {
            "status": "success",
            "agent_id": agent_id,
            "pattern_type": pattern_type or "all",
            "patterns": patterns,
            "count": len(patterns)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── Context & Recent Memory ──

@router.post("/add-context")
async def add_context_event(
    agent_id: str,
    event_type: str,
    event_data: Dict[str, Any],
    ttl_hours: int = 24
) -> Dict[str, Any]:
    """Add contextual event to short-term memory"""
    try:
        event_id = await memory.add_context_event(agent_id, event_type, event_data, ttl_hours)
        
        return {
            "status": "success",
            "event_id": event_id,
            "agent_id": agent_id,
            "event_type": event_type,
            "ttl_hours": ttl_hours
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/context/{agent_id}")
async def get_recent_context(
    agent_id: str,
    hours: int = 24
) -> Dict[str, Any]:
    """Get recent context events"""
    try:
        context = await memory.get_recent_context(agent_id, hours)
        
        return {
            "status": "success",
            "agent_id": agent_id,
            "time_range_hours": hours,
            "context_events": context,
            "count": len(context)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── Knowledge Accumulation ──

@router.post("/add-knowledge")
async def add_knowledge(
    agent_id: str,
    knowledge_type: str,
    knowledge_data: Dict[str, Any],
    confidence: float = 0.8,
    source: str = "experience"
) -> Dict[str, Any]:
    """Add accumulated knowledge"""
    try:
        knowledge_id = await memory.add_knowledge(
            agent_id, knowledge_type, knowledge_data, confidence, source
        )
        
        return {
            "status": "success",
            "knowledge_id": knowledge_id,
            "agent_id": agent_id,
            "knowledge_type": knowledge_type,
            "confidence": confidence,
            "source": source
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/knowledge/{agent_id}")
async def get_agent_knowledge(
    agent_id: str,
    knowledge_type: Optional[str] = None
) -> Dict[str, Any]:
    """Get accumulated knowledge for an agent"""
    try:
        knowledge = await memory.get_agent_knowledge(agent_id, knowledge_type)
        
        return {
            "status": "success",
            "agent_id": agent_id,
            "knowledge_type": knowledge_type or "all",
            "knowledge": knowledge,
            "count": len(knowledge)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── Task History & Statistics ──

@router.post("/record-task")
async def record_task_completion(
    agent_id: str,
    task_name: str,
    task_parameters: Dict[str, Any],
    result: Dict[str, Any],
    duration_seconds: float,
    tools_used: list,
    success: bool
) -> Dict[str, Any]:
    """Record completed task for learning and statistics"""
    try:
        task_id = await memory.record_task_completion(
            agent_id, task_name, task_parameters, result, 
            duration_seconds, tools_used, success
        )
        
        return {
            "status": "success",
            "task_id": task_id,
            "agent_id": agent_id,
            "task_name": task_name,
            "success": success,
            "duration_seconds": duration_seconds
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/history/{agent_id}")
async def get_task_history(
    agent_id: str,
    limit: int = 50
) -> Dict[str, Any]:
    """Get task history"""
    try:
        history = await memory.get_task_history(agent_id, limit)
        
        return {
            "status": "success",
            "agent_id": agent_id,
            "limit": limit,
            "history": history,
            "count": len(history)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/statistics/{agent_id}")
async def get_agent_statistics(agent_id: str) -> Dict[str, Any]:
    """Get agent statistics from task history"""
    try:
        stats = await memory.get_agent_statistics(agent_id)
        
        return {
            "status": "success",
            "agent_id": agent_id,
            "statistics": stats
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/insights/{agent_id}")
async def get_agent_insights(agent_id: str) -> Dict[str, Any]:
    """Get comprehensive insights about an agent"""
    try:
        stats = await memory.get_agent_statistics(agent_id)
        patterns = await memory.get_learned_patterns(agent_id)
        knowledge = await memory.get_agent_knowledge(agent_id)
        
        return {
            "status": "success",
            "agent_id": agent_id,
            "statistics": stats,
            "learned_patterns_count": len(patterns),
            "accumulated_knowledge_count": len(knowledge),
            "insights": {
                "most_used_tools": stats.get('most_used_tools', [])[:3],
                "success_rate_percentage": round(stats.get('success_rate', 0) * 100, 2),
                "average_execution_time": f"{stats.get('average_duration_seconds', 0):.2f}s"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
