"""
3-Layer Memory System:
1. User Memory: role, preferences, past actions
2. Department Memory: workflows, best practices
3. Agent Memory: execution history, improvements

Uses SQLite + ChromaDB
"""
import json
from typing import Dict, List, Optional
from datetime import datetime
import logging

from core.database import AsyncSessionLocal, User, AgentExecution
from rag.pipeline import rag_pipeline
from sqlalchemy import select, func

logger = logging.getLogger(__name__)


class MemorySystem:
    """Manages all 3 layers of memory"""
    
    async def initialize(self):
        """Initialize memory system"""
        logger.info("Memory system initialized")
    
    # ─── LAYER 1: USER MEMORY ───────────────────────────────
    
    async def get_user_memory(self, session_id: str) -> Dict:
        """Retrieve user-level memory"""
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(User).where(User.session_id == session_id)
            )
            user = result.scalar_one_or_none()
            
            if user:
                return {
                    "session_id": session_id,
                    "department": user.department,
                    "role": user.role,
                    "preferences": json.loads(user.preferences) if user.preferences else {},
                    "exists": True
                }
            
            return {
                "session_id": session_id,
                "department": None,
                "role": None,
                "preferences": {},
                "exists": False
            }
    
    async def update_user_memory(
        self,
        session_id: str,
        department: Optional[str] = None,
        role: Optional[str] = None,
        preferences: Optional[Dict] = None
    ) -> Dict:
        """Update or create user memory"""
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(User).where(User.session_id == session_id)
            )
            user = result.scalar_one_or_none()
            
            if user:
                if department:
                    user.department = department
                if role:
                    user.role = role
                if preferences:
                    existing_prefs = json.loads(user.preferences) if user.preferences else {}
                    existing_prefs.update(preferences)
                    user.preferences = json.dumps(existing_prefs)
                user.updated_at = datetime.utcnow()
            else:
                user = User(
                    session_id=session_id,
                    department=department,
                    role=role,
                    preferences=json.dumps(preferences or {})
                )
                db.add(user)
            
            await db.commit()
            return await self.get_user_memory(session_id)
    
    # ─── LAYER 2: DEPARTMENT MEMORY ─────────────────────────
    
    async def get_department_memory(self, department: str) -> Dict:
        """Get department-level memory including workflows and best practices"""
        # Query recent executions in this department
        async with AsyncSessionLocal() as db:
            from core.database import Agent
            result = await db.execute(
                select(Agent)
                .where(Agent.department == department)
                .where(Agent.status == "active")
                .order_by(Agent.usage_count.desc())
                .limit(10)
            )
            agents = result.scalars().all()
            
            # Get common patterns
            from core.database import TaskPattern
            patterns_result = await db.execute(
                select(TaskPattern)
                .where(TaskPattern.department == department)
                .order_by(TaskPattern.frequency.desc())
                .limit(5)
            )
            patterns = patterns_result.scalars().all()
        
        # Get relevant knowledge from RAG
        rag_docs = await rag_pipeline.retrieve(
            query=f"workflows and best practices in {department}",
            department=department,
            n_results=3
        )
        
        return {
            "department": department,
            "active_agents": [
                {
                    "agent_id": a.agent_id,
                    "name": a.agent_name,
                    "usage_count": a.usage_count,
                    "time_saved_minutes": a.time_saved_minutes
                }
                for a in agents
            ],
            "top_patterns": [
                {
                    "task": p.task_description[:100],
                    "frequency": p.frequency,
                    "role": p.role
                }
                for p in patterns
            ],
            "knowledge_docs": [
                {
                    "title": d["metadata"].get("title", "Unknown"),
                    "type": d["metadata"].get("type", "doc"),
                    "relevance": round(d["relevance_score"], 2)
                }
                for d in rag_docs
            ]
        }
    
    # ─── LAYER 3: AGENT MEMORY ──────────────────────────────
    
    async def get_agent_memory(self, agent_id: str) -> Dict:
        """Get agent-level memory - execution history and improvements"""
        async with AsyncSessionLocal() as db:
            # Recent executions
            result = await db.execute(
                select(AgentExecution)
                .where(AgentExecution.agent_id == agent_id)
                .order_by(AgentExecution.started_at.desc())
                .limit(20)
            )
            executions = result.scalars().all()
            
            # Aggregate stats
            total = len(executions)
            successful = sum(1 for e in executions if e.status == "completed")
            
            # Extract learnings from outputs
            learnings = []
            for e in executions[:5]:  # Last 5 executions
                if e.output_data:
                    output = json.loads(e.output_data)
                    if output.get("summary"):
                        learnings.append(output["summary"][:150])
        
        return {
            "agent_id": agent_id,
            "total_executions": total,
            "success_rate": round(successful / total * 100, 1) if total > 0 else 0,
            "recent_learnings": learnings,
            "improvement_suggestions": await self._get_improvement_suggestions(agent_id, executions)
        }
    
    async def store_execution(
        self,
        agent_id: str,
        execution_id: str,
        input_data: Dict,
        output: Dict,
        session_id: Optional[str] = None
    ):
        """Store execution in agent memory (RAG)"""
        # Add execution summary to RAG for future context
        doc_id = f"execution_{execution_id}"
        content = (
            f"Agent {agent_id} execution:\n"
            f"Input: {json.dumps(input_data)[:200]}\n"
            f"Summary: {output.get('summary', '')}\n"
            f"Steps: {output.get('steps_completed', 0)} completed"
        )
        
        await rag_pipeline.add_document(
            doc_id=doc_id,
            content=content,
            metadata={
                "type": "execution",
                "agent_id": agent_id,
                "execution_id": execution_id,
                "department": "general"
            }
        )
    
    async def get_context(
        self,
        agent_id: str,
        department: Optional[str],
        session_id: Optional[str]
    ) -> Dict:
        """Get combined memory context for agent execution"""
        context = {}
        
        if session_id:
            user_mem = await self.get_user_memory(session_id)
            context["user"] = user_mem
        
        if department:
            dept_mem = await self.get_department_memory(department)
            context["department_agents_count"] = len(dept_mem["active_agents"])
            context["department_patterns"] = dept_mem["top_patterns"][:3]
        
        agent_mem = await self.get_agent_memory(agent_id)
        context["agent_executions"] = agent_mem["total_executions"]
        context["agent_success_rate"] = agent_mem["success_rate"]
        context["previous_learnings"] = agent_mem["recent_learnings"][:3]
        
        return context
    
    async def _get_improvement_suggestions(self, agent_id: str, executions: List) -> List[str]:
        """Generate improvement suggestions based on execution history"""
        if len(executions) < 3:
            return ["Run agent more times to generate improvement suggestions"]
        
        failed = [e for e in executions if e.status == "failed"]
        if failed:
            return [
                f"Agent failed {len(failed)} times - review error handling",
                "Consider adding retry logic for failed steps",
                "Review tool configurations for reliability"
            ]
        
        return [
            "Agent running smoothly",
            "Consider scheduling for automated runs",
            "Share this agent with your team"
        ]


# Singleton
memory_system = MemorySystem()
