"""Workflows CRUD + run API"""
import json, uuid, aiosqlite
from datetime import datetime
from fastapi import APIRouter, HTTPException, BackgroundTasks
from core.database import DB_PATH
from core.models import WorkflowCreate, WorkflowUpdate
from execution.engine import workflow_engine
from scheduler.runner import scheduler

router = APIRouter()


def _row_to_workflow(row: dict) -> dict:
    for field in ("trigger_config","steps","tags"):
        if isinstance(row.get(field), str):
            try: row[field] = json.loads(row[field])
            except: row[field] = {} if field != "steps" else []
    return row


@router.get("/")
async def list_workflows(folder: str = None, status: str = None):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        q = "SELECT * FROM workflows WHERE 1=1"
        params = []
        if folder: q += " AND folder=?"; params.append(folder)
        if status: q += " AND status=?"; params.append(status)
        q += " ORDER BY updated_at DESC"
        cursor = await db.execute(q, params)
        rows = await cursor.fetchall()
    return {"workflows": [_row_to_workflow(dict(r)) for r in rows], "total": len(rows)}


@router.post("/")
async def create_workflow(data: WorkflowCreate):
    wf_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    
    trigger_config = {
        "type": data.trigger.type,
        "app_key": data.trigger.app_key,
        "connection_id": data.trigger.connection_id,
        "config": data.trigger.config,
    }
    
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO workflows (id, name, description, status, trigger_type, trigger_config, steps, folder, tags, created_at, updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)
        """, (wf_id, data.name, data.description, "off",
              data.trigger.type,
              json.dumps(trigger_config),
              json.dumps([s.model_dump() for s in data.steps]),
              data.folder,
              json.dumps(data.tags),
              now, now))
        await db.commit()
    
    return {"id": wf_id, "name": data.name, "status": "off", "created_at": now}


@router.get("/{workflow_id}")
async def get_workflow(workflow_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM workflows WHERE id=?", (workflow_id,))
        row = await cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return _row_to_workflow(dict(row))


@router.put("/{workflow_id}")
async def update_workflow(workflow_id: str, data: WorkflowUpdate):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM workflows WHERE id=?", (workflow_id,))
        row = await cursor.fetchone()
        if not row: raise HTTPException(status_code=404, detail="Workflow not found")
        
        updates = {"updated_at": datetime.utcnow().isoformat()}
        if data.name is not None: updates["name"] = data.name
        if data.description is not None: updates["description"] = data.description
        if data.folder is not None: updates["folder"] = data.folder
        if data.tags is not None: updates["tags"] = json.dumps(data.tags)
        if data.steps is not None: updates["steps"] = json.dumps([s.model_dump() for s in data.steps])
        if data.trigger is not None:
            updates["trigger_type"] = data.trigger.type
            updates["trigger_config"] = json.dumps({
                "type": data.trigger.type, "app_key": data.trigger.app_key,
                "connection_id": data.trigger.connection_id, "config": data.trigger.config})
        if data.status is not None:
            updates["status"] = data.status
            was_on = dict(row).get("status") == "on"
            if data.status == "on" and not was_on:
                cfg = json.loads(dict(row).get("trigger_config","{}"))
                scheduler.register_workflow(workflow_id, cfg)
            elif data.status == "off":
                scheduler.unregister_workflow(workflow_id)
        
        set_clause = ", ".join(f"{k}=?" for k in updates)
        vals = list(updates.values()) + [workflow_id]
        await db.execute(f"UPDATE workflows SET {set_clause} WHERE id=?", vals)
        await db.commit()
    
    return await get_workflow(workflow_id)


@router.patch("/{workflow_id}/toggle")
async def toggle_workflow(workflow_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT status, trigger_config FROM workflows WHERE id=?", (workflow_id,))
        row = await cursor.fetchone()
        if not row: raise HTTPException(status_code=404, detail="Not found")
        new_status = "off" if dict(row)["status"] == "on" else "on"
        await db.execute("UPDATE workflows SET status=?, updated_at=? WHERE id=?",
                         (new_status, datetime.utcnow().isoformat(), workflow_id))
        await db.commit()
    
    if new_status == "on":
        cfg = json.loads(dict(row).get("trigger_config","{}"))
        scheduler.register_workflow(workflow_id, cfg)
    else:
        scheduler.unregister_workflow(workflow_id)
    
    return {"workflow_id": workflow_id, "status": new_status}


@router.delete("/{workflow_id}")
async def delete_workflow(workflow_id: str):
    scheduler.unregister_workflow(workflow_id)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM workflows WHERE id=?", (workflow_id,))
        await db.execute("DELETE FROM workflow_runs WHERE workflow_id=?", (workflow_id,))
        await db.commit()
    return {"deleted": True}


@router.post("/{workflow_id}/run")
async def run_workflow(workflow_id: str, background_tasks: BackgroundTasks,
                        trigger_data: dict = None):
    """Manually trigger a workflow run."""
    payload = trigger_data or {"trigger": "manual", "timestamp": datetime.utcnow().isoformat()}
    background_tasks.add_task(workflow_engine.run, workflow_id, payload)
    return {"status": "queued", "workflow_id": workflow_id, "trigger_data": payload}


@router.post("/{workflow_id}/run_sync")
async def run_workflow_sync(workflow_id: str, trigger_data: dict = None):
    """Synchronous run (waits for result). Good for testing."""
    payload = trigger_data or {"trigger": "manual", "timestamp": datetime.utcnow().isoformat()}
    result = await workflow_engine.run(workflow_id, payload)
    return result


@router.get("/{workflow_id}/runs")
async def get_runs(workflow_id: str, limit: int = 50):
    runs = await workflow_engine.get_runs(workflow_id, limit)
    parsed = []
    for r in runs:
        for f in ("trigger_data","steps_results"):
            if isinstance(r.get(f), str):
                try: r[f] = json.loads(r[f])
                except: pass
        parsed.append(r)
    return {"runs": parsed, "total": len(parsed)}


@router.get("/runs/all")
async def get_all_runs(limit: int = 100):
    runs = await workflow_engine.get_runs(None, limit)
    for r in runs:
        for f in ("trigger_data","steps_results"):
            if isinstance(r.get(f), str):
                try: r[f] = json.loads(r[f])
                except: pass
    return {"runs": runs, "total": len(runs)}
