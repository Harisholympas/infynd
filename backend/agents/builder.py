"""Agent Builder Engine - Dynamically creates AI agents from blueprints"""
import json
import logging
import uuid
import aiosqlite
from typing import Dict, Any, Optional
from datetime import datetime
from core.config import settings
from core.llm import llm_client
from core.database import DB_PATH
from core.models import AgentBlueprint

logger = logging.getLogger(__name__)


AGENT_GENERATION_PROMPT = """You are an AI agent architect. Given the following information, generate a detailed agent blueprint.

Department: {department}
Role: {role}
Task Description: {task}
RAG Context: {rag_context}
Extracted Intent: {intent}

Generate a complete agent blueprint in this EXACT JSON format (no markdown, no explanation):
{{
  "agent_name": "descriptive name for this agent",
  "department": "{department}",
  "role": "{role}",
  "description": "what this agent does in 1-2 sentences",
  "steps": [
    "step 1: specific action",
    "step 2: specific action",
    "step 3: specific action",
    "step 4: validate and output"
  ],
  "tools": ["tool1", "tool2"],
  "triggers": ["trigger_condition_1", "trigger_condition_2"],
  "memory": true,
  "metadata": {{
    "complexity": "low|medium|high",
    "frequency": "daily|weekly|monthly|on-demand",
    "estimated_time_saved_hours": 2
  }}
}}

Available tools: email_sender, calendar_manager, document_creator, data_analyzer, 
report_generator, slack_notifier, file_manager, database_query, form_filler, 
web_scraper, pdf_extractor, spreadsheet_processor, notification_sender, task_tracker

Make the steps specific and actionable for the given task."""


class AgentBuilder:
    """Builds AI agents from blueprints"""
    
    async def generate_blueprint(self, department: str, role: str, 
                                  task: str, rag_context: str = "",
                                  intent: str = "") -> AgentBlueprint:
        """Use LLM to generate a detailed agent blueprint"""
        prompt = AGENT_GENERATION_PROMPT.format(
            department=department,
            role=role,
            task=task,
            rag_context=rag_context or "No additional context available",
            intent=intent or task
        )
        
        response = await llm_client.generate(prompt, temperature=0.2)
        
        try:
            # Clean response - strip markdown if present
            clean = response.strip()
            if "```json" in clean:
                clean = clean.split("```json")[1].split("```")[0].strip()
            elif "```" in clean:
                clean = clean.split("```")[1].split("```")[0].strip()
            
            # Find JSON object
            start = clean.find("{")
            end = clean.rfind("}") + 1
            if start >= 0 and end > start:
                clean = clean[start:end]
            
            data = json.loads(clean)
            return AgentBlueprint(**data)
        except Exception as e:
            logger.error(f"Failed to parse blueprint from LLM: {e}")
            # Return a sensible default blueprint
            return self._default_blueprint(department, role, task)
    
    def _default_blueprint(self, department: str, role: str, task: str) -> AgentBlueprint:
        """Generate a default blueprint when LLM fails"""
        task_words = task.lower().split()
        tools = self._infer_tools(task_words)
        steps = self._infer_steps(task, tools)
        
        return AgentBlueprint(
            agent_name=f"{department} {role} Automation Agent",
            department=department,
            role=role,
            description=f"Automates: {task[:100]}",
            steps=steps,
            tools=tools,
            triggers=["manual", "scheduled"],
            memory=True,
            metadata={"complexity": "medium", "frequency": "daily", "estimated_time_saved_hours": 1}
        )
    
    def _infer_tools(self, task_words: list) -> list:
        tool_map = {
            "email": "email_sender", "report": "report_generator",
            "document": "document_creator", "schedule": "calendar_manager",
            "data": "data_analyzer", "slack": "slack_notifier",
            "file": "file_manager", "database": "database_query",
            "form": "form_filler", "pdf": "pdf_extractor",
            "spreadsheet": "spreadsheet_processor", "task": "task_tracker",
            "notify": "notification_sender"
        }
        tools = set()
        for word in task_words:
            for key, tool in tool_map.items():
                if key in word:
                    tools.add(tool)
        return list(tools) if tools else ["task_tracker", "notification_sender"]
    
    def _infer_steps(self, task: str, tools: list) -> list:
        return [
            f"1. Receive and validate task input",
            f"2. Analyze: {task[:80]}",
            f"3. Execute using {', '.join(tools[:2]) if tools else 'available tools'}",
            "4. Process results and handle errors",
            "5. Generate output and send notifications",
            "6. Log execution and update memory"
        ]
    
    async def save_agent(self, blueprint: AgentBlueprint, user_id: str = "default") -> str:
        """Save agent to database"""
        agent_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("""
                INSERT INTO agents (id, name, department, role, description, blueprint, 
                                    status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, 'active', ?, ?)
            """, (
                agent_id, blueprint.agent_name, blueprint.department,
                blueprint.role, blueprint.description,
                json.dumps(blueprint.model_dump()), now, now
            ))
            await db.commit()
        
        logger.info(f"Agent saved: {agent_id} - {blueprint.agent_name}")
        return agent_id
    
    async def list_agents(self, department: Optional[str] = None) -> list:
        """List all agents, optionally filtered by department"""
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            if department:
                cursor = await db.execute(
                    "SELECT * FROM agents WHERE department = ? ORDER BY created_at DESC",
                    (department,)
                )
            else:
                cursor = await db.execute(
                    "SELECT * FROM agents ORDER BY created_at DESC"
                )
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]
    
    async def get_agent(self, agent_id: str) -> Optional[dict]:
        """Get a specific agent by ID"""
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM agents WHERE id = ?", (agent_id,))
            row = await cursor.fetchone()
            return dict(row) if row else None
    
    async def delete_agent(self, agent_id: str) -> bool:
        """Delete an agent"""
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("DELETE FROM agents WHERE id = ?", (agent_id,))
            await db.commit()
        return True


agent_builder = AgentBuilder()
