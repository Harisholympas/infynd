"""Database - complete schema for Zapier-equivalent platform"""
import aiosqlite
import logging
from pathlib import Path
from core.config import settings

logger = logging.getLogger(__name__)
DB_PATH = settings.SQLITE_PATH

async def init_db():
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript("""
        PRAGMA journal_mode=WAL;

        -- Workflows (Zapier "Zaps")
        CREATE TABLE IF NOT EXISTS workflows (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            status TEXT DEFAULT 'off',  -- off | on | error
            trigger_type TEXT NOT NULL,  -- webhook | schedule | email | manual | app_event
            trigger_config TEXT DEFAULT '{}',
            steps TEXT DEFAULT '[]',    -- JSON array of steps
            folder TEXT DEFAULT '',
            tags TEXT DEFAULT '[]',
            run_count INTEGER DEFAULT 0,
            error_count INTEGER DEFAULT 0,
            last_run_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Individual workflow step executions (Zap history)
        CREATE TABLE IF NOT EXISTS workflow_runs (
            id TEXT PRIMARY KEY,
            workflow_id TEXT NOT NULL,
            status TEXT DEFAULT 'running',  -- running | success | error | halted
            trigger_data TEXT DEFAULT '{}',
            steps_results TEXT DEFAULT '[]',
            error_message TEXT,
            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            duration_ms INTEGER,
            FOREIGN KEY (workflow_id) REFERENCES workflows(id)
        );

        -- App connections / credentials (Zapier "Connected Accounts")
        CREATE TABLE IF NOT EXISTS app_connections (
            id TEXT PRIMARY KEY,
            app_key TEXT NOT NULL,      -- gmail, slack, notion, sheets, etc.
            name TEXT NOT NULL,         -- user-given label e.g. "Work Gmail"
            credentials TEXT DEFAULT '{}',  -- encrypted JSON
            status TEXT DEFAULT 'active',
            last_tested_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Webhook endpoints (Zapier webhook triggers)
        CREATE TABLE IF NOT EXISTS webhooks (
            id TEXT PRIMARY KEY,
            workflow_id TEXT,
            secret TEXT NOT NULL,
            endpoint_path TEXT NOT NULL UNIQUE,
            received_count INTEGER DEFAULT 0,
            last_received_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (workflow_id) REFERENCES workflows(id)
        );

        -- Scheduled tasks (Zapier schedule trigger)  
        CREATE TABLE IF NOT EXISTS schedules (
            id TEXT PRIMARY KEY,
            workflow_id TEXT NOT NULL,
            cron_expr TEXT NOT NULL,
            timezone TEXT DEFAULT 'UTC',
            next_run_at TIMESTAMP,
            last_run_at TIMESTAMP,
            enabled INTEGER DEFAULT 1,
            FOREIGN KEY (workflow_id) REFERENCES workflows(id)
        );

        -- Data store (Zapier Storage by Zapier)
        CREATE TABLE IF NOT EXISTS data_store (
            id TEXT PRIMARY KEY,
            workflow_id TEXT,
            key TEXT NOT NULL,
            value TEXT,
            expires_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(workflow_id, key)
        );

        -- Formatter results cache
        CREATE TABLE IF NOT EXISTS formatter_cache (
            id TEXT PRIMARY KEY,
            operation TEXT NOT NULL,
            input_hash TEXT NOT NULL UNIQUE,
            result TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Error log
        CREATE TABLE IF NOT EXISTS error_log (
            id TEXT PRIMARY KEY,
            workflow_id TEXT,
            run_id TEXT,
            step_index INTEGER,
            error_type TEXT,
            error_message TEXT,
            stack_trace TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Audit / analytics
        CREATE TABLE IF NOT EXISTS analytics_events (
            id TEXT PRIMARY KEY,
            event_type TEXT NOT NULL,
            workflow_id TEXT,
            metadata TEXT DEFAULT '{}',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Task queue for async step execution
        CREATE TABLE IF NOT EXISTS task_queue (
            id TEXT PRIMARY KEY,
            run_id TEXT NOT NULL,
            workflow_id TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            payload TEXT DEFAULT '{}',
            attempts INTEGER DEFAULT 0,
            max_attempts INTEGER DEFAULT 3,
            scheduled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            picked_at TIMESTAMP,
            completed_at TIMESTAMP
        );
        """)
        await db.commit()
    logger.info("Database initialized")

async def get_db():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        yield db
