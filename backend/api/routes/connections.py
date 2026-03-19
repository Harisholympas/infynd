"""App Connections (credential management) API"""
import json, uuid, aiosqlite
from datetime import datetime
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import Dict, Any, Optional
from core.database import DB_PATH
from credentials.vault import encrypt_credentials, decrypt_credentials
from connectors.registry import APP_REGISTRY, list_apps, get_app
from agents.resume_analyzer import resume_analyzer

router = APIRouter()


class ConnectionCreate(BaseModel):
    app_key: str
    name: str
    credentials: Dict[str, Any] = {}


@router.get("/apps")
async def list_available_apps():
    """List all available apps with their triggers and actions."""
    return {"apps": list_apps(), "total": len(APP_REGISTRY)}


@router.get("/apps/{app_key}")
async def get_app_detail(app_key: str):
    app = get_app(app_key)
    if not app:
        raise HTTPException(status_code=404, detail=f"App '{app_key}' not found")
    return {"key": app_key, **app}


@router.get("/")
async def list_connections():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT id, app_key, name, status, last_tested_at, created_at FROM app_connections ORDER BY created_at DESC")
        rows = await cursor.fetchall()
    return {"connections": [dict(r) for r in rows]}


@router.post("/")
async def create_connection(data: ConnectionCreate):
    app = get_app(data.app_key)
    if not app:
        raise HTTPException(status_code=400, detail=f"Unknown app: {data.app_key}")
    
    conn_id = str(uuid.uuid4())
    encrypted = encrypt_credentials(data.credentials)
    
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO app_connections (id, app_key, name, credentials, status, created_at) VALUES (?,?,?,?,?,?)",
            (conn_id, data.app_key, data.name, encrypted, "active", datetime.utcnow().isoformat()))
        await db.commit()
    
    return {"id": conn_id, "app_key": data.app_key, "name": data.name, "status": "active"}


@router.post("/resume-screen")
async def analyze_resume(
    file: UploadFile = File(...),
    job_title: str = Form(""),
    job_description: str = Form(""),
):
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    try:
        result = await resume_analyzer.analyze_file(
            file.filename or "resume.txt",
            content,
            job_title=job_title,
            job_description=job_description,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {"status": "success", **result}


@router.post("/{connection_id}/test")
async def test_connection(connection_id: str):
    """Test if credentials work for this connection."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM app_connections WHERE id=?", (connection_id,))
        row = await cursor.fetchone()
    
    if not row:
        raise HTTPException(status_code=404, detail="Connection not found")
    
    conn = dict(row)
    creds = decrypt_credentials(conn["credentials"])
    app_key = conn["app_key"]
    
    result = {"connection_id": connection_id, "app_key": app_key}
    
    try:
        import httpx
        if app_key == "slack":
            token = creds.get("bot_token","")
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.post("https://slack.com/api/auth.test",
                                      headers={"Authorization": f"Bearer {token}"})
                data = r.json()
                result["ok"] = data.get("ok", False)
                result["detail"] = data.get("error") or f"Connected as {data.get('user','')}"
        elif app_key == "notion":
            api_key = creds.get("api_key","")
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.get("https://api.notion.com/v1/users/me",
                                     headers={"Authorization": f"Bearer {api_key}",
                                              "Notion-Version": "2022-06-28"})
                data = r.json()
                result["ok"] = "id" in data
                result["detail"] = data.get("name") or data.get("message","")
        elif app_key == "github":
            token = creds.get("token","")
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.get("https://api.github.com/user",
                                     headers={"Authorization": f"token {token}"})
                data = r.json()
                result["ok"] = "id" in data
                result["detail"] = f"Connected as @{data.get('login','')}"
        elif app_key == "airtable":
            api_key = creds.get("api_key","")
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.get("https://api.airtable.com/v0/meta/whoami",
                                     headers={"Authorization": f"Bearer {api_key}"})
                data = r.json()
                result["ok"] = "id" in data
                result["detail"] = f"Connected as {data.get('email','')}"
        elif app_key in ("formatter","filter","delay","storage","schedule","paths","webhooks","rss", "resume_screener"):
            result["ok"] = True
            result["detail"] = "No authentication required"
        elif app_key == "gmail":
            result["ok"] = bool(creds.get("email") and creds.get("app_password"))
            result["detail"] = f"Credentials {'provided' if result['ok'] else 'missing'} for {creds.get('email','')}"
        else:
            result["ok"] = bool(creds)
            result["detail"] = "Credentials saved (connection test not available for this app)"
        
        # Update test timestamp
        status = "active" if result.get("ok") else "error"
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("UPDATE app_connections SET last_tested_at=?, status=? WHERE id=?",
                             (datetime.utcnow().isoformat(), status, connection_id))
            await db.commit()
    
    except Exception as e:
        result["ok"] = False
        result["detail"] = str(e)
    
    return result


@router.delete("/{connection_id}")
async def delete_connection(connection_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM app_connections WHERE id=?", (connection_id,))
        await db.commit()
    return {"deleted": True}
