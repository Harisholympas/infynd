"""Analytics tracker"""
import json
import logging
import uuid
import aiosqlite
from datetime import datetime
from core.database import DB_PATH

logger = logging.getLogger(__name__)


class AnalyticsTracker:
    
    async def track_event(self, event_type: str, agent_id: str = None,
                           department: str = None, role: str = None,
                           metadata: dict = None):
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("""
                INSERT INTO analytics_events (id, event_type, agent_id, department, role, metadata, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                str(uuid.uuid4()), event_type, agent_id, department, role,
                json.dumps(metadata or {}), datetime.utcnow().isoformat()
            ))
            await db.commit()

    async def get_summary(self) -> dict:
        async with aiosqlite.connect(DB_PATH) as db:
            ta_r = await db.execute("SELECT COUNT(*) FROM agents WHERE status='active'")
            ta = (await ta_r.fetchone())[0]
            te_r = await db.execute("SELECT COUNT(*) FROM executions")
            te = (await te_r.fetchone())[0]
            sc_r = await db.execute("SELECT COUNT(*) FROM executions WHERE status='completed'")
            sc = (await sc_r.fetchone())[0]
            success_rate = (sc / te * 100) if te > 0 else 0
            time_saved = (sc * 30) / 60
            dept_cursor = await db.execute("""
                SELECT department, COUNT(*) as count FROM agents WHERE status='active'
                GROUP BY department ORDER BY count DESC LIMIT 5
            """)
            dept_rows = await dept_cursor.fetchall()
            top_depts = [{"department": r[0], "count": r[1]} for r in dept_rows]
            events_cursor = await db.execute("""
                SELECT event_type, department, created_at, metadata
                FROM analytics_events ORDER BY created_at DESC LIMIT 10
            """)
            event_rows = await events_cursor.fetchall()
            recent = [{"event_type": r[0], "department": r[1], "created_at": r[2],
                       "metadata": json.loads(r[3] or "{}")} for r in event_rows]
            agent_usage_cursor = await db.execute("""
                SELECT name, department, execution_count, success_rate
                FROM agents WHERE status='active' ORDER BY execution_count DESC LIMIT 10
            """)
            usage_rows = await agent_usage_cursor.fetchall()
            agent_stats = [{"name": r[0], "department": r[1], "executions": r[2],
                            "success_rate": r[3]} for r in usage_rows]
        return {
            "total_agents": ta, "total_executions": te,
            "success_rate": round(success_rate, 1), "time_saved_hours": round(time_saved, 1),
            "top_departments": top_depts, "recent_activity": recent, "agent_stats": agent_stats
        }


analytics_tracker = AnalyticsTracker()
