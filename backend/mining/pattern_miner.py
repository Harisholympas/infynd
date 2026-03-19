"""Task Pattern Miner - Detects repeated patterns and suggests agents"""
import json
import logging
import uuid
import hashlib
import aiosqlite
from datetime import datetime
from typing import List, Dict
from core.database import DB_PATH
from core.llm import llm_client

logger = logging.getLogger(__name__)


class PatternMiner:
    """Mines task patterns and automatically suggests new agents"""
    
    async def record_task(self, department: str, role: str, task: str):
        """Record a task occurrence"""
        pattern_hash = hashlib.md5(
            f"{department}_{role}_{task.lower().strip()}".encode()
        ).hexdigest()
        
        async with aiosqlite.connect(DB_PATH) as db:
            existing = await db.execute(
                "SELECT id, frequency FROM task_patterns WHERE pattern_hash = ?",
                (pattern_hash,)
            )
            row = await existing.fetchone()
            
            if row:
                await db.execute("""
                    UPDATE task_patterns 
                    SET frequency = frequency + 1, last_seen = ?
                    WHERE pattern_hash = ?
                """, (datetime.utcnow().isoformat(), pattern_hash))
            else:
                await db.execute("""
                    INSERT INTO task_patterns 
                    (id, department, role, task_description, frequency, pattern_hash)
                    VALUES (?, ?, ?, ?, 1, ?)
                """, (str(uuid.uuid4()), department, role, task, pattern_hash))
            
            await db.commit()
    
    async def get_patterns(self, min_frequency: int = 2, 
                            department: str = None) -> List[Dict]:
        """Get frequently repeated task patterns"""
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            if department:
                cursor = await db.execute("""
                    SELECT * FROM task_patterns 
                    WHERE frequency >= ? AND department = ?
                    ORDER BY frequency DESC LIMIT 20
                """, (min_frequency, department))
            else:
                cursor = await db.execute("""
                    SELECT * FROM task_patterns 
                    WHERE frequency >= ?
                    ORDER BY frequency DESC LIMIT 20
                """, (min_frequency,))
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]
    
    async def suggest_agents(self) -> List[Dict]:
        """Suggest new agents based on detected patterns"""
        patterns = await self.get_patterns(min_frequency=2)
        suggestions = []
        
        for pattern in patterns:
            if pattern.get("suggested_agent_id"):
                continue  # Already has an agent
            
            suggestion = await self._generate_suggestion(pattern)
            suggestions.append(suggestion)
        
        return suggestions
    
    async def _generate_suggestion(self, pattern: dict) -> dict:
        """Generate an agent suggestion from a pattern"""
        prompt = f"""Given this frequently repeated task pattern:
Department: {pattern['department']}
Role: {pattern['role']}  
Task: {pattern['task_description']}
Frequency: {pattern['frequency']} times

Suggest an agent name and brief description (JSON only, no markdown):
{{"agent_name": "...", "description": "...", "confidence": 0.9}}"""
        
        response = await llm_client.generate(prompt, temperature=0.1)
        
        try:
            clean = response.strip()
            if "```" in clean:
                clean = clean.split("```")[1] if "```json" not in clean else clean.split("```json")[1]
                clean = clean.split("```")[0].strip()
            start = clean.find("{")
            end = clean.rfind("}") + 1
            if start >= 0 and end > start:
                data = json.loads(clean[start:end])
            else:
                raise ValueError("No JSON found")
        except:
            data = {
                "agent_name": f"{pattern['department']} {pattern['role']} Automation",
                "description": f"Automates: {pattern['task_description'][:80]}",
                "confidence": 0.7
            }
        
        return {
            "pattern_id": pattern["id"],
            "department": pattern["department"],
            "role": pattern["role"],
            "task_description": pattern["task_description"],
            "frequency": pattern["frequency"],
            "suggested_agent_name": data.get("agent_name", ""),
            "description": data.get("description", ""),
            "confidence": data.get("confidence", 0.7)
        }
    
    async def get_stats(self) -> dict:
        """Get mining statistics"""
        async with aiosqlite.connect(DB_PATH) as db:
            total = await db.execute("SELECT COUNT(*) FROM task_patterns")
            t = await total.fetchone()
            repeated = await db.execute(
                "SELECT COUNT(*) FROM task_patterns WHERE frequency > 1"
            )
            r = await repeated.fetchone()
            top = await db.execute("""
                SELECT department, SUM(frequency) as total 
                FROM task_patterns GROUP BY department 
                ORDER BY total DESC LIMIT 5
            """)
            top_rows = await top.fetchall()
        
        return {
            "total_patterns": t[0] if t else 0,
            "repeated_patterns": r[0] if r else 0,
            "top_departments": [{"department": row[0], "total": row[1]} for row in top_rows]
        }


pattern_miner = PatternMiner()
