"""Execution history API"""
import json
from fastapi import APIRouter
from execution.engine import workflow_engine

router = APIRouter()

@router.get("/history")
async def get_history(workflow_id: str = None, limit: int = 50):
    runs = await workflow_engine.get_runs(workflow_id, limit)
    for r in runs:
        for f in ("trigger_data","steps_results"):
            if isinstance(r.get(f), str):
                try: r[f] = json.loads(r[f])
                except: pass
    return {"runs": runs, "total": len(runs)}
