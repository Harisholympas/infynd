"""Webhook receiver - real HTTP endpoint for triggering workflows"""
import json, uuid, aiosqlite, hmac, hashlib, logging
from datetime import datetime
from fastapi import APIRouter, Request, HTTPException, Header
from typing import Optional
from core.database import DB_PATH
from execution.engine import workflow_engine

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/receive/{endpoint_path}")
async def receive_webhook(endpoint_path: str, request: Request,
                           x_hub_signature: Optional[str] = Header(None)):
    """Receive a webhook and fire the associated workflow."""
    # Look up webhook
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM webhooks WHERE endpoint_path=?", (endpoint_path,))
        row = await cursor.fetchone()
    
    if not row:
        raise HTTPException(status_code=404, detail="Webhook endpoint not found")
    
    webhook = dict(row)
    body_bytes = await request.body()
    
    # Verify HMAC signature if provided
    if x_hub_signature and webhook.get("secret"):
        expected = "sha256=" + hmac.new(
            webhook["secret"].encode(), body_bytes, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(x_hub_signature, expected):
            raise HTTPException(status_code=401, detail="Invalid signature")
    
    # Parse body
    try:
        body = json.loads(body_bytes) if body_bytes else {}
    except:
        body = {"raw": body_bytes.decode("utf-8", errors="replace")}
    
    trigger_data = {
        "trigger": "webhook",
        "endpoint": endpoint_path,
        "method": request.method,
        "headers": dict(request.headers),
        "query_params": dict(request.query_params),
        "body": body,
        "received_at": datetime.utcnow().isoformat()
    }
    
    # Update webhook stats
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE webhooks SET received_count=received_count+1, last_received_at=? WHERE endpoint_path=?",
            (datetime.utcnow().isoformat(), endpoint_path))
        await db.commit()
    
    # Fire workflow if linked and active
    result = {"received": True, "endpoint": endpoint_path}
    if webhook.get("workflow_id"):
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT status FROM workflows WHERE id=?", (webhook["workflow_id"],))
            wf_row = await cursor.fetchone()
        
        if wf_row and dict(wf_row)["status"] == "on":
            run_result = await workflow_engine.run(webhook["workflow_id"], trigger_data)
            result["run_id"] = run_result.get("run_id")
            result["status"] = run_result.get("status")
        else:
            result["note"] = "Workflow is turned off"
    
    return result


@router.post("/create")
async def create_webhook_endpoint(workflow_id: str):
    """Create a new webhook endpoint for a workflow."""
    endpoint_path = str(uuid.uuid4()).replace("-","")[:16]
    secret = str(uuid.uuid4()).replace("-","")
    wh_id = str(uuid.uuid4())
    
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO webhooks (id, workflow_id, secret, endpoint_path, created_at) VALUES (?,?,?,?,?)",
            (wh_id, workflow_id, secret, endpoint_path, datetime.utcnow().isoformat()))
        # Update workflow trigger
        from core.config import settings
        webhook_url = f"{settings.WEBHOOK_BASE_URL}/api/webhooks/receive/{endpoint_path}"
        await db.execute(
            "UPDATE workflows SET trigger_type='webhook', trigger_config=?, updated_at=? WHERE id=?",
            (json.dumps({"type":"webhook","config":{"url":webhook_url,"endpoint":endpoint_path}}),
             datetime.utcnow().isoformat(), workflow_id))
        await db.commit()
    
    from core.config import settings
    return {
        "webhook_id": wh_id,
        "endpoint_path": endpoint_path,
        "secret": secret,
        "url": f"{settings.WEBHOOK_BASE_URL}/api/webhooks/receive/{endpoint_path}",
        "note": "POST JSON to this URL to trigger your workflow"
    }


@router.get("/list")
async def list_webhooks():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT id, workflow_id, endpoint_path, received_count, last_received_at, created_at FROM webhooks ORDER BY created_at DESC")
        rows = await cursor.fetchall()
    from core.config import settings
    result = []
    for r in rows:
        d = dict(r)
        d["url"] = f"{settings.WEBHOOK_BASE_URL}/api/webhooks/receive/{d['endpoint_path']}"
        result.append(d)
    return {"webhooks": result}
