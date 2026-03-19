"""Memory Manager - 3-layer memory system: User, Department, Agent"""
import json
import logging
import uuid
import aiosqlite
from datetime import datetime
from typing import Optional, Dict, Any
from core.database import DB_PATH

logger = logging.getLogger(__name__)


class MemoryManager:
    """Manages the 3-layer memory system"""
    
    async def initialize(self):
        """Initialize memory with defaults"""
        departments = ["HR", "Finance", "Sales", "Marketing", "Engineering", 
                       "Operations", "Legal", "Customer Support"]
        async with aiosqlite.connect(DB_PATH) as db:
            for dept in departments:
                existing = await db.execute(
                    "SELECT id FROM department_memory WHERE department = ?", (dept,)
                )
                row = await existing.fetchone()
                if not row:
                    await db.execute("""
                        INSERT INTO department_memory (id, department, workflows, best_practices, common_tools)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        str(uuid.uuid4()), dept,
                        json.dumps(self._default_workflows(dept)),
                        json.dumps(self._default_practices(dept)),
                        json.dumps(self._default_tools(dept))
                    ))
            await db.commit()
        logger.info("Memory manager initialized")
    
    # ---- USER MEMORY ----
    
    async def get_user_memory(self, user_id: str = "default") -> dict:
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM user_memory WHERE user_id = ?", (user_id,)
            )
            row = await cursor.fetchone()
            if row:
                r = dict(row)
                r["preferences"] = json.loads(r.get("preferences") or "{}")
                r["past_actions"] = json.loads(r.get("past_actions") or "[]")
                return r
            return {"user_id": user_id, "department": None, "role": None, 
                    "preferences": {}, "past_actions": []}
    
    async def update_user_memory(self, user_id: str, department: str = None, 
                                  role: str = None, action: str = None) -> dict:
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM user_memory WHERE user_id = ?", (user_id,)
            )
            row = await cursor.fetchone()
            
            if row:
                existing = dict(row)
                past_actions = json.loads(existing.get("past_actions") or "[]")
                if action:
                    past_actions.append({
                        "action": action, 
                        "timestamp": datetime.utcnow().isoformat()
                    })
                    past_actions = past_actions[-50:]  # Keep last 50
                
                await db.execute("""
                    UPDATE user_memory 
                    SET department = COALESCE(?, department),
                        role = COALESCE(?, role),
                        past_actions = ?,
                        updated_at = ?
                    WHERE user_id = ?
                """, (
                    department, role, json.dumps(past_actions),
                    datetime.utcnow().isoformat(), user_id
                ))
            else:
                past_actions = [{"action": action, "timestamp": datetime.utcnow().isoformat()}] if action else []
                await db.execute("""
                    INSERT INTO user_memory (id, user_id, department, role, preferences, past_actions)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    str(uuid.uuid4()), user_id, department, role,
                    json.dumps({}), json.dumps(past_actions)
                ))
            await db.commit()
        return await self.get_user_memory(user_id)
    
    # ---- DEPARTMENT MEMORY ----
    
    async def get_department_memory(self, department: str) -> dict:
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM department_memory WHERE department = ?", (department,)
            )
            row = await cursor.fetchone()
            if row:
                r = dict(row)
                r["workflows"] = json.loads(r.get("workflows") or "[]")
                r["best_practices"] = json.loads(r.get("best_practices") or "[]")
                r["common_tools"] = json.loads(r.get("common_tools") or "[]")
                return r
            return {"department": department, "workflows": [], 
                    "best_practices": [], "common_tools": []}
    
    async def update_department_memory(self, department: str, 
                                        workflow: str = None, practice: str = None) -> dict:
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute(
                "SELECT * FROM department_memory WHERE department = ?", (department,)
            )
            row = await cursor.fetchone()
            if row:
                data = dict(row)
                workflows = json.loads(data.get("workflows") or "[]")
                practices = json.loads(data.get("best_practices") or "[]")
                if workflow and workflow not in workflows:
                    workflows.append(workflow)
                if practice and practice not in practices:
                    practices.append(practice)
                await db.execute("""
                    UPDATE department_memory SET workflows = ?, best_practices = ?, updated_at = ?
                    WHERE department = ?
                """, (json.dumps(workflows), json.dumps(practices), 
                      datetime.utcnow().isoformat(), department))
                await db.commit()
        return await self.get_department_memory(department)
    
    # ---- DEFAULTS ----
    
    def _default_workflows(self, dept: str) -> list:
        workflows = {
            "HR": ["Onboarding new employees", "Processing leave requests", "Performance reviews", "Payroll processing"],
            "Finance": ["Invoice processing", "Expense approvals", "Monthly reconciliation", "Budget reporting"],
            "Sales": ["Lead qualification", "Follow-up scheduling", "Proposal generation", "CRM updates"],
            "Marketing": ["Campaign planning", "Content scheduling", "Analytics reporting", "Email campaigns"],
            "Engineering": ["Code review process", "Bug triage", "Sprint planning", "Deployment checklist"],
            "Operations": ["Inventory management", "Vendor coordination", "Process documentation", "KPI tracking"],
            "Legal": ["Contract review", "Compliance checks", "Document management", "Risk assessment"],
            "Customer Support": ["Ticket routing", "Response templates", "Escalation process", "Customer follow-up"]
        }
        return workflows.get(dept, ["General workflow", "Task management"])
    
    def _default_practices(self, dept: str) -> list:
        return [f"Follow {dept} SOP", "Document all actions", "Escalate when uncertain", "Regular status updates"]
    
    def _default_tools(self, dept: str) -> list:
        tools = {
            "HR": ["email_sender", "form_filler", "document_creator", "calendar_manager"],
            "Finance": ["spreadsheet_processor", "report_generator", "data_analyzer", "pdf_extractor"],
            "Sales": ["email_sender", "calendar_manager", "task_tracker", "document_creator"],
            "Marketing": ["email_sender", "report_generator", "data_analyzer", "notification_sender"],
            "Engineering": ["task_tracker", "notification_sender", "document_creator", "database_query"],
        }
        return tools.get(dept, ["task_tracker", "notification_sender", "email_sender"])


memory_manager = MemoryManager()
