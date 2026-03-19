"""Analytics API"""
import json, aiosqlite
from fastapi import APIRouter
from core.database import DB_PATH

router = APIRouter()

@router.get("/summary")
async def get_summary():
    async with aiosqlite.connect(DB_PATH) as db:
        total_wf = (await (await db.execute("SELECT COUNT(*) FROM workflows")).fetchone())[0]
        active_wf = (await (await db.execute("SELECT COUNT(*) FROM workflows WHERE status='on'")).fetchone())[0]
        total_runs = (await (await db.execute("SELECT COUNT(*) FROM workflow_runs")).fetchone())[0]
        success_runs = (await (await db.execute("SELECT COUNT(*) FROM workflow_runs WHERE status='success'")).fetchone())[0]
        error_runs = (await (await db.execute("SELECT COUNT(*) FROM workflow_runs WHERE status='error'")).fetchone())[0]
        
        recent_cursor = await db.execute("""
            SELECT w.name, wr.status, wr.started_at, wr.duration_ms
            FROM workflow_runs wr JOIN workflows w ON wr.workflow_id=w.id
            ORDER BY wr.started_at DESC LIMIT 20
        """)
        recent = [dict(zip([c[0] for c in recent_cursor.description], r))
                  for r in await recent_cursor.fetchall()]
        
        top_cursor = await db.execute("""
            SELECT w.name, w.run_count, w.error_count, w.status
            FROM workflows w ORDER BY run_count DESC LIMIT 10
        """)
        top_wf = [dict(zip([c[0] for c in top_cursor.description], r))
                  for r in await top_cursor.fetchall()]
        
        # Runs per day last 7 days
        daily_cursor = await db.execute("""
            SELECT DATE(started_at) as day, COUNT(*) as runs,
                   SUM(CASE WHEN status='success' THEN 1 ELSE 0 END) as success
            FROM workflow_runs 
            WHERE started_at >= DATE('now', '-7 days')
            GROUP BY DATE(started_at) ORDER BY day
        """)
        daily = [{"day": r[0], "runs": r[1], "success": r[2]} for r in await daily_cursor.fetchall()]
        
        # App usage
        app_cursor = await db.execute("""
            SELECT w.id, w.steps FROM workflows
        """)
        app_counts = {}
        for row in await app_cursor.fetchall():
            try:
                steps = json.loads(row[1] or "[]")
                for s in steps:
                    ak = s.get("app_key","unknown")
                    app_counts[ak] = app_counts.get(ak, 0) + 1
            except: pass
        app_usage = sorted([{"app": k, "count": v} for k,v in app_counts.items()],
                           key=lambda x: -x["count"])[:8]
    
    return {
        "total_workflows": total_wf,
        "active_workflows": active_wf,
        "total_runs": total_runs,
        "success_runs": success_runs,
        "error_runs": error_runs,
        "success_rate": round(success_runs / total_runs * 100, 1) if total_runs else 0,
        "recent_runs": recent,
        "top_workflows": top_wf,
        "daily_runs": daily,
        "app_usage": app_usage,
    }
