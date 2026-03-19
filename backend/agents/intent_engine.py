"""Intent Understanding Engine - Extracts structured intent from user input"""
import json
import logging
from core.llm import llm_client

logger = logging.getLogger(__name__)

INTENT_PROMPT = """You are an AI intent analyzer for a workforce automation platform.

Analyze the following task description and extract structured intent.

Department: {department}
Role: {role}
Task: {task}

Respond ONLY with valid JSON, no markdown:
{{
  "department": "{department}",
  "role": "{role}",
  "task": "concise task summary",
  "frequency": "daily|weekly|monthly|hourly|on-demand",
  "required_tools": ["tool1", "tool2"],
  "complexity": "low|medium|high",
  "suggested_steps": [
    "step 1",
    "step 2",
    "step 3"
  ],
  "automation_potential": "high|medium|low",
  "estimated_time_per_occurrence_minutes": 30,
  "keywords": ["keyword1", "keyword2"]
}}"""


class IntentEngine:
    """Extracts structured intent from natural language task descriptions"""
    
    async def extract_intent(self, department: str, role: str, 
                              task: str, context: str = "") -> dict:
        """Extract structured intent from task description"""
        prompt = INTENT_PROMPT.format(
            department=department,
            role=role,
            task=task
        )
        
        if context:
            prompt += f"\n\nAdditional context:\n{context}"
        
        response = await llm_client.generate(prompt, temperature=0.1)
        
        try:
            clean = response.strip()
            if "```json" in clean:
                clean = clean.split("```json")[1].split("```")[0].strip()
            elif "```" in clean:
                clean = clean.split("```")[1].split("```")[0].strip()
            start = clean.find("{")
            end = clean.rfind("}") + 1
            if start >= 0 and end > start:
                clean = clean[start:end]
            return json.loads(clean)
        except Exception as e:
            logger.error(f"Intent parse error: {e}")
            return self._default_intent(department, role, task)
    
    def _default_intent(self, department: str, role: str, task: str) -> dict:
        words = task.lower().split()
        tools = []
        if any(w in words for w in ["email", "send", "notify"]):
            tools.append("email_sender")
        if any(w in words for w in ["report", "document", "create"]):
            tools.append("report_generator")
        if any(w in words for w in ["data", "analyze", "process"]):
            tools.append("data_analyzer")
        if not tools:
            tools = ["task_tracker"]
        
        return {
            "department": department,
            "role": role,
            "task": task[:200],
            "frequency": "daily",
            "required_tools": tools,
            "complexity": "medium",
            "suggested_steps": [
                "Collect required inputs",
                "Process and validate data",
                "Execute primary action",
                "Generate output",
                "Notify stakeholders"
            ],
            "automation_potential": "high",
            "estimated_time_per_occurrence_minutes": 30,
            "keywords": task.lower().split()[:5]
        }


intent_engine = IntentEngine()
