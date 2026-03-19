"""Core Pydantic models"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime
import uuid

def gen_id(): return str(uuid.uuid4())

# ── Step types ────────────────────────────────────────────────────────────────

class StepConfig(BaseModel):
    app_key: str                    # e.g. "gmail", "slack", "formatter"
    action: str                     # e.g. "send_email", "post_message"
    connection_id: Optional[str] = None
    input_map: Dict[str, Any] = {}  # field -> static value or {{step.field}} template
    output_key: str = ""            # store result as this key for downstream steps
    conditions: List[Dict] = []     # filter/branch conditions
    retry_on_error: bool = False
    halt_on_error: bool = True

class TriggerConfig(BaseModel):
    type: Literal["webhook","schedule","manual","email_imap","app_event","rss"]
    app_key: Optional[str] = None
    connection_id: Optional[str] = None
    config: Dict[str, Any] = {}     # e.g. {"cron": "0 9 * * 1", "timezone": "UTC"}

# ── Workflow ───────────────────────────────────────────────────────────────────

class WorkflowCreate(BaseModel):
    name: str
    description: str = ""
    trigger: TriggerConfig
    steps: List[StepConfig] = []
    folder: str = ""
    tags: List[str] = []

class WorkflowUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    trigger: Optional[TriggerConfig] = None
    steps: Optional[List[StepConfig]] = None
    folder: Optional[str] = None
    tags: Optional[List[str]] = None
    status: Optional[str] = None

class WorkflowResponse(BaseModel):
    id: str
    name: str
    description: str
    status: str
    trigger: Dict[str, Any]
    steps: List[Dict[str, Any]]
    folder: str
    tags: List[str]
    run_count: int
    error_count: int
    last_run_at: Optional[str]
    created_at: str
    updated_at: str

# ── Runs ──────────────────────────────────────────────────────────────────────

class RunResponse(BaseModel):
    id: str
    workflow_id: str
    status: str
    trigger_data: Dict[str, Any]
    steps_results: List[Dict[str, Any]]
    error_message: Optional[str]
    started_at: str
    completed_at: Optional[str]
    duration_ms: Optional[int]

# ── App connections ────────────────────────────────────────────────────────────

class AppConnectionCreate(BaseModel):
    app_key: str
    name: str
    credentials: Dict[str, Any] = {}

class AppConnectionResponse(BaseModel):
    id: str
    app_key: str
    name: str
    status: str
    last_tested_at: Optional[str]
    created_at: str

# ── Formatter ─────────────────────────────────────────────────────────────────

class FormatterRequest(BaseModel):
    operation: str
    input: Any
    options: Dict[str, Any] = {}
