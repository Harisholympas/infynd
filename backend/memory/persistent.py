"""Enhanced Agent Memory System - Long-term persistent memory with resumption capability"""
import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import aiosqlite
from core.database import DB_PATH

logger = logging.getLogger(__name__)


class AgentPersistentMemory:
    """Manages persistent long-term memory for agents to resume tasks"""
    
    async def initialize_db(self):
        """Initialize agent memory database tables"""
        async with aiosqlite.connect(DB_PATH) as db:
            # Agent execution state - allows resuming tasks
            await db.execute("""
                CREATE TABLE IF NOT EXISTS agent_execution_state (
                    id TEXT PRIMARY KEY,
                    agent_id TEXT NOT NULL,
                    workflow_id TEXT,
                    execution_state TEXT,
                    current_step INTEGER,
                    total_steps INTEGER,
                    inputs TEXT,
                    outputs TEXT,
                    context TEXT,
                    status TEXT,
                    started_at TEXT,
                    paused_at TEXT,
                    resumed_at TEXT,
                    completed_at TEXT,
                    created_at TEXT
                )
            """)
            
            # Agent learned patterns and successful strategies
            await db.execute("""
                CREATE TABLE IF NOT EXISTS agent_patterns (
                    id TEXT PRIMARY KEY,
                    agent_id TEXT,
                    pattern_type TEXT,
                    pattern_data TEXT,
                    success_rate REAL,
                    usage_count INTEGER,
                    created_at TEXT,
                    last_used TEXT
                )
            """)
            
            # Agent contextual memory - short-term events
            await db.execute("""
                CREATE TABLE IF NOT EXISTS agent_context_memory (
                    id TEXT PRIMARY KEY,
                    agent_id TEXT,
                    event_type TEXT,
                    event_data TEXT,
                    relevance_score REAL,
                    timestamp TEXT,
                    expires_at TEXT
                )
            """)
            
            # Agent knowledge accumulation
            await db.execute("""
                CREATE TABLE IF NOT EXISTS agent_knowledge (
                    id TEXT PRIMARY KEY,
                    agent_id TEXT,
                    knowledge_type TEXT,
                    knowledge_data TEXT,
                    confidence REAL,
                    source TEXT,
                    created_at TEXT
                )
            """)
            
            # Agent task history for pattern learning
            await db.execute("""
                CREATE TABLE IF NOT EXISTS agent_task_history (
                    id TEXT PRIMARY KEY,
                    agent_id TEXT,
                    task_name TEXT,
                    task_parameters TEXT,
                    result TEXT,
                    duration_seconds REAL,
                    success BOOLEAN,
                    tools_used TEXT,
                    created_at TEXT
                )
            """)
            
            await db.commit()
            logger.info("Agent memory tables initialized")
    
    # ── Execution State Management ──
    
    async def save_execution_state(self, agent_id: str, workflow_id: str, 
                                   state: Dict[str, Any], current_step: int, 
                                   total_steps: int) -> str:
        """Save agent execution state for resumption"""
        state_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("""
                INSERT INTO agent_execution_state 
                (id, agent_id, workflow_id, execution_state, current_step, total_steps, 
                 inputs, outputs, context, status, started_at, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                state_id, agent_id, workflow_id,
                json.dumps(state.get('execution', {})),
                current_step, total_steps,
                json.dumps(state.get('inputs', {})),
                json.dumps(state.get('outputs', {})),
                json.dumps(state.get('context', {})),
                'executing', now, now
            ))
            await db.commit()
        
        logger.info(f"Saved execution state for agent {agent_id}: {state_id}")
        return state_id
    
    async def pause_execution(self, state_id: str) -> bool:
        """Pause execution and save current state"""
        now = datetime.utcnow().isoformat()
        
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("""
                UPDATE agent_execution_state 
                SET status = 'paused', paused_at = ?
                WHERE id = ?
            """, (now, state_id))
            await db.commit()
        
        logger.info(f"Paused execution: {state_id}")
        return True
    
    async def resume_execution(self, state_id: str) -> Optional[Dict[str, Any]]:
        """Resume a paused execution from where it left off"""
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM agent_execution_state WHERE id = ?", (state_id,)
            )
            row = await cursor.fetchone()
            
            if row:
                now = datetime.utcnow().isoformat()
                await db.execute("""
                    UPDATE agent_execution_state 
                    SET status = 'resumed', resumed_at = ?
                    WHERE id = ?
                """, (now, state_id))
                await db.commit()
                
                row_dict = dict(row)
                row_dict['execution_state'] = json.loads(row_dict['execution_state'])
                row_dict['inputs'] = json.loads(row_dict['inputs'])
                row_dict['outputs'] = json.loads(row_dict['outputs'])
                row_dict['context'] = json.loads(row_dict['context'])
                
                logger.info(f"Resumed execution: {state_id}")
                return row_dict
        
        return None
    
    async def complete_execution(self, state_id: str, final_output: Dict[str, Any]) -> bool:
        """Mark execution as complete"""
        now = datetime.utcnow().isoformat()
        
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("""
                UPDATE agent_execution_state 
                SET status = 'completed', outputs = ?, completed_at = ?
                WHERE id = ?
            """, (json.dumps(final_output), now, state_id))
            await db.commit()
        
        logger.info(f"Completed execution: {state_id}")
        return True
    
    # ── Pattern Learning ──
    
    async def record_successful_pattern(self, agent_id: str, pattern_type: str, 
                                       pattern_data: Dict[str, Any], success_rate: float):
        """Record a successful pattern for future use"""
        pattern_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("""
                INSERT INTO agent_patterns 
                (id, agent_id, pattern_type, pattern_data, success_rate, usage_count, created_at, last_used)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (pattern_id, agent_id, pattern_type, json.dumps(pattern_data), 
                  success_rate, 1, now, now))
            await db.commit()
        
        logger.info(f"Recorded pattern for agent {agent_id}: {pattern_type}")
        return pattern_id
    
    async def get_learned_patterns(self, agent_id: str, pattern_type: str = None) -> List[Dict]:
        """Retrieve learned patterns sorted by success rate"""
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            
            if pattern_type:
                cursor = await db.execute("""
                    SELECT * FROM agent_patterns 
                    WHERE agent_id = ? AND pattern_type = ?
                    ORDER BY success_rate DESC, usage_count DESC
                """, (agent_id, pattern_type))
            else:
                cursor = await db.execute("""
                    SELECT * FROM agent_patterns 
                    WHERE agent_id = ?
                    ORDER BY success_rate DESC, usage_count DESC
                """, (agent_id,))
            
            rows = await cursor.fetchall()
            patterns = []
            for row in rows:
                pattern = dict(row)
                pattern['pattern_data'] = json.loads(pattern['pattern_data'])
                patterns.append(pattern)
            
            return patterns
    
    # ── Context & Recent Memory ──
    
    async def add_context_event(self, agent_id: str, event_type: str, 
                               event_data: Dict[str, Any], ttl_hours: int = 24):
        """Add contextual event to short-term memory"""
        event_id = str(uuid.uuid4())
        now = datetime.utcnow()
        expires_at = (now + timedelta(hours=ttl_hours)).isoformat()
        
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("""
                INSERT INTO agent_context_memory 
                (id, agent_id, event_type, event_data, relevance_score, timestamp, expires_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (event_id, agent_id, event_type, json.dumps(event_data), 
                  0.8, now.isoformat(), expires_at))
            await db.commit()
        
        return event_id
    
    async def get_recent_context(self, agent_id: str, hours: int = 24) -> List[Dict]:
        """Get recent context events"""
        cutoff = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
        
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT * FROM agent_context_memory 
                WHERE agent_id = ? AND timestamp > ? AND expires_at > datetime('now')
                ORDER BY timestamp DESC
            """, (agent_id, cutoff))
            
            rows = await cursor.fetchall()
            events = []
            for row in rows:
                event = dict(row)
                event['event_data'] = json.loads(event['event_data'])
                events.append(event)
            
            return events
    
    # ── Knowledge Accumulation ──
    
    async def add_knowledge(self, agent_id: str, knowledge_type: str, 
                           knowledge_data: Dict[str, Any], confidence: float = 0.8, 
                           source: str = "experience"):
        """Add accumulated knowledge"""
        knowledge_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("""
                INSERT INTO agent_knowledge 
                (id, agent_id, knowledge_type, knowledge_data, confidence, source, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (knowledge_id, agent_id, knowledge_type, json.dumps(knowledge_data), 
                  confidence, source, now))
            await db.commit()
        
        return knowledge_id
    
    async def get_agent_knowledge(self, agent_id: str, knowledge_type: str = None) -> List[Dict]:
        """Get accumulated knowledge"""
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            
            if knowledge_type:
                cursor = await db.execute("""
                    SELECT * FROM agent_knowledge 
                    WHERE agent_id = ? AND knowledge_type = ?
                    ORDER BY confidence DESC, created_at DESC
                """, (agent_id, knowledge_type))
            else:
                cursor = await db.execute("""
                    SELECT * FROM agent_knowledge 
                    WHERE agent_id = ?
                    ORDER BY confidence DESC, created_at DESC
                """, (agent_id,))
            
            rows = await cursor.fetchall()
            knowledge = []
            for row in rows:
                item = dict(row)
                item['knowledge_data'] = json.loads(item['knowledge_data'])
                knowledge.append(item)
            
            return knowledge
    
    # ── Task History & Learning ──
    
    async def record_task_completion(self, agent_id: str, task_name: str, 
                                    task_parameters: Dict, result: Dict, 
                                    duration_seconds: float, tools_used: List[str], 
                                    success: bool):
        """Record completed task for learning and statistics"""
        task_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("""
                INSERT INTO agent_task_history 
                (id, agent_id, task_name, task_parameters, result, duration_seconds, success, tools_used, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (task_id, agent_id, task_name, json.dumps(task_parameters), 
                  json.dumps(result), duration_seconds, success, json.dumps(tools_used), now))
            await db.commit()
        
        return task_id
    
    async def get_task_history(self, agent_id: str, limit: int = 50) -> List[Dict]:
        """Get task history for analysis and learning"""
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT * FROM agent_task_history 
                WHERE agent_id = ?
                ORDER BY created_at DESC
                LIMIT ?
            """, (agent_id, limit))
            
            rows = await cursor.fetchall()
            history = []
            for row in rows:
                item = dict(row)
                item['task_parameters'] = json.loads(item['task_parameters'])
                item['result'] = json.loads(item['result'])
                item['tools_used'] = json.loads(item['tools_used'])
                history.append(item)
            
            return history
    
    async def get_agent_statistics(self, agent_id: str) -> Dict[str, Any]:
        """Get agent statistics from task history"""
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            
            # Total tasks
            count_cursor = await db.execute(
                "SELECT COUNT(*) as count FROM agent_task_history WHERE agent_id = ?",
                (agent_id,)
            )
            total_tasks = (await count_cursor.fetchone())['count']
            
            # Success rate
            success_cursor = await db.execute("""
                SELECT COUNT(*) as count FROM agent_task_history 
                WHERE agent_id = ? AND success = 1
            """, (agent_id,))
            successful_tasks = (await success_cursor.fetchone())['count']
            
            # Average duration
            duration_cursor = await db.execute("""
                SELECT AVG(duration_seconds) as avg_duration FROM agent_task_history 
                WHERE agent_id = ?
            """, (agent_id,))
            avg_duration = (await duration_cursor.fetchone())['avg_duration'] or 0
            
            # Most used tools
            cursor = await db.execute("""
                SELECT tools_used FROM agent_task_history 
                WHERE agent_id = ?
            """, (agent_id,))
            
            rows = await cursor.fetchall()
            tool_usage = {}
            for row in rows:
                tools = json.loads(row['tools_used'])
                for tool in tools:
                    tool_usage[tool] = tool_usage.get(tool, 0) + 1
            
            return {
                "total_tasks": total_tasks,
                "successful_tasks": successful_tasks,
                "success_rate": successful_tasks / total_tasks if total_tasks > 0 else 0,
                "average_duration_seconds": avg_duration,
                "most_used_tools": sorted(tool_usage.items(), key=lambda x: x[1], reverse=True),
                "total_tools_used": len(tool_usage)
            }
