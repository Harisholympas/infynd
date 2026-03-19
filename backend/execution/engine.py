"""
Workflow Execution Engine - runs workflows step-by-step with real connectors.
Handles context passing, error handling, filter halts, and branching.
"""
import json, logging, uuid, aiosqlite
from datetime import datetime
from typing import Dict, Any, List, Optional
from core.database import DB_PATH
from core.config import settings
from credentials.vault import decrypt_credentials
from connectors.executor import execute_step, resolve_inputs, evaluate_conditions

logger = logging.getLogger(__name__)


def get_default_app_credentials(app_key: str) -> dict:
    if app_key == "gmail" and settings.DEFAULT_GMAIL_EMAIL and settings.DEFAULT_GMAIL_APP_PASSWORD:
        return {
            "email": settings.DEFAULT_GMAIL_EMAIL,
            "app_password": settings.DEFAULT_GMAIL_APP_PASSWORD,
        }
    return {}


async def get_connection_credentials(app_key: str, connection_id: str) -> dict:
    """Load decrypted credentials for an app connection."""
    if not connection_id:
        return get_default_app_credentials(app_key)
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT credentials FROM app_connections WHERE id=?", (connection_id,))
        row = await cursor.fetchone()
        if row:
            try:
                return decrypt_credentials(row["credentials"] or "{}")
            except:
                try:
                    return json.loads(row["credentials"] or "{}")
                except:
                    return get_default_app_credentials(app_key)
    return get_default_app_credentials(app_key)


class WorkflowEngine:
    """Execute a workflow, returning a full run record."""

    async def run(self, workflow_id: str, trigger_data: Dict[str, Any]) -> Dict[str, Any]:
        run_id = str(uuid.uuid4())
        started_at = datetime.utcnow()

        # Load workflow
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM workflows WHERE id=?", (workflow_id,))
            wf = await cursor.fetchone()
        if not wf:
            return {"error": "Workflow not found", "run_id": run_id}

        wf = dict(wf)
        steps = json.loads(wf.get("steps", "[]"))

        # Persist run record as 'running'
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "INSERT INTO workflow_runs (id, workflow_id, status, trigger_data, started_at) VALUES (?,?,?,?,?)",
                (run_id, workflow_id, "running", json.dumps(trigger_data), started_at.isoformat()))
            await db.commit()

        # Build execution context
        context = {"trigger": trigger_data}
        steps_results = []
        final_status = "success"
        error_message = None

        for idx, step in enumerate(steps):
            step_key = step.get("output_key") or f"step{idx+1}"
            app_key = step.get("app_key", "")
            action = step.get("action", "")
            input_map = step.get("input_map", {})
            connection_id = step.get("connection_id", "")
            halt_on_error = step.get("halt_on_error", True)
            conditions = step.get("conditions", [])

            # Check step conditions (filter-style pre-conditions)
            if conditions:
                passed = evaluate_conditions(conditions, context)
                if not passed:
                    result = {"skipped": True, "reason": "Pre-conditions not met"}
                    steps_results.append({"step": idx+1, "app_key": app_key, "action": action,
                                          "status": "skipped", "output": result})
                    context[step_key] = result
                    continue

            # Resolve input templates against context
            resolved_inputs = resolve_inputs(input_map, context)
            resolved_inputs["_context"] = context  # for filter step

            # Load credentials
            creds = await get_connection_credentials(app_key, connection_id)

            # Execute
            try:
                output = await execute_step(app_key, action, resolved_inputs, creds, workflow_id)
            except Exception as e:
                output = {"error": str(e)}

            # Check for halt signals (filter passed=False, or error)
            step_status = "success"
            if output.get("halt") or output.get("passed") == False:
                step_status = "halted"
                steps_results.append({"step": idx+1, "app_key": app_key, "action": action,
                                       "status": "halted", "output": output})
                context[step_key] = output
                final_status = "halted"
                error_message = "Workflow halted by Filter step"
                break

            if output.get("error") and halt_on_error:
                step_status = "error"
                steps_results.append({"step": idx+1, "app_key": app_key, "action": action,
                                       "status": "error", "output": output})
                context[step_key] = output
                final_status = "error"
                error_message = output["error"]

                # Log to error_log
                async with aiosqlite.connect(DB_PATH) as db:
                    await db.execute(
                        "INSERT INTO error_log (id, workflow_id, run_id, step_index, error_type, error_message) VALUES (?,?,?,?,?,?)",
                        (str(uuid.uuid4()), workflow_id, run_id, idx,
                         "execution_error", output["error"]))
                    await db.commit()
                break
            elif output.get("error"):
                step_status = "error_ignored"

            steps_results.append({"step": idx+1, "app_key": app_key, "action": action,
                                   "status": step_status, "output": output})
            context[step_key] = output

        # Finalize run record
        completed_at = datetime.utcnow()
        duration_ms = int((completed_at - started_at).total_seconds() * 1000)

        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("""
                UPDATE workflow_runs SET status=?, steps_results=?, error_message=?,
                    completed_at=?, duration_ms=? WHERE id=?
            """, (final_status, json.dumps(steps_results), error_message,
                  completed_at.isoformat(), duration_ms, run_id))
            await db.execute("""
                UPDATE workflows SET run_count=run_count+1, last_run_at=?,
                    error_count=error_count+(?),
                    updated_at=? WHERE id=?
            """, (completed_at.isoformat(), 1 if final_status == "error" else 0,
                  completed_at.isoformat(), workflow_id))
            await db.commit()

        return {
            "run_id": run_id, "workflow_id": workflow_id, "status": final_status,
            "steps_results": steps_results, "error_message": error_message,
            "duration_ms": duration_ms, "context_keys": list(context.keys())
        }

    async def get_runs(self, workflow_id: Optional[str] = None, limit: int = 50) -> List[dict]:
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            if workflow_id:
                cursor = await db.execute(
                    "SELECT * FROM workflow_runs WHERE workflow_id=? ORDER BY started_at DESC LIMIT ?",
                    (workflow_id, limit))
            else:
                cursor = await db.execute(
                    "SELECT * FROM workflow_runs ORDER BY started_at DESC LIMIT ?", (limit,))
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]


workflow_engine = WorkflowEngine()
