"""
Real scheduler - uses APScheduler to fire workflows on cron/interval schedules.
Also polls RSS feeds and IMAP inboxes as triggers.
"""
import json, logging, asyncio, uuid, aiosqlite, re
from datetime import datetime, timedelta
from typing import Dict
from core.database import DB_PATH

logger = logging.getLogger(__name__)

try:
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from apscheduler.triggers.cron import CronTrigger
    from apscheduler.triggers.interval import IntervalTrigger
    HAS_APSCHEDULER = True
except ImportError:
    HAS_APSCHEDULER = False
    logger.warning("APScheduler not installed. Run: pip install apscheduler")


def parse_schedule_trigger(trigger_config: dict) -> dict:
    """Convert our trigger config to APScheduler kwargs."""
    trigger_type = trigger_config.get("config", {})
    ttype = trigger_config.get("type","")
    cfg = trigger_config.get("config", {})
    app_trigger = cfg.get("trigger_action","")

    if app_trigger == "every_x_minutes":
        return {"type": "interval", "minutes": int(cfg.get("interval", 15))}
    elif app_trigger == "every_hour":
        return {"type": "cron", "minute": int(cfg.get("minute", 0))}
    elif app_trigger == "every_day":
        time_str = cfg.get("time", "09:00")
        h, m = time_str.split(":") if ":" in time_str else ("9","0")
        return {"type": "cron", "hour": int(h), "minute": int(m)}
    elif app_trigger == "every_week":
        day_map = {"monday":"mon","tuesday":"tue","wednesday":"wed","thursday":"thu",
                   "friday":"fri","saturday":"sat","sunday":"sun"}
        day = day_map.get(cfg.get("day","monday"), "mon")
        time_str = cfg.get("time", "09:00")
        h, m = time_str.split(":") if ":" in time_str else ("9","0")
        return {"type": "cron", "day_of_week": day, "hour": int(h), "minute": int(m)}
    elif app_trigger == "every_month":
        time_str = cfg.get("time", "09:00")
        h, m = time_str.split(":") if ":" in time_str else ("9","0")
        return {"type": "cron", "day": int(cfg.get("day", 1)), "hour": int(h), "minute": int(m)}
    elif app_trigger == "custom_cron":
        return {"type": "cron_expr", "cron": cfg.get("cron", "0 9 * * 1")}
    
    return {}


class WorkflowScheduler:
    def __init__(self):
        self.scheduler = None
        self.rss_poll_states: Dict[str, str] = {}  # feed_url -> last_guid

    async def start(self):
        if not HAS_APSCHEDULER:
            logger.warning("APScheduler unavailable - schedules disabled")
            return
        self.scheduler = AsyncIOScheduler()
        self.scheduler.start()
        await self._load_active_schedules()
        # RSS poller every 5 min
        self.scheduler.add_job(self._poll_all_rss, "interval", minutes=5,
                               id="rss_global_poller", replace_existing=True)
        logger.info("Scheduler started")

    async def stop(self):
        if self.scheduler:
            self.scheduler.shutdown(wait=False)

    async def _load_active_schedules(self):
        """Load all 'on' schedule-triggered workflows and register them."""
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT id, trigger_type, trigger_config FROM workflows WHERE status='on'")
            rows = await cursor.fetchall()
        
        for row in rows:
            if row["trigger_type"] == "schedule":
                try:
                    cfg = json.loads(row["trigger_config"] or "{}")
                    self.register_workflow(row["id"], cfg)
                except Exception as e:
                    logger.error(f"Failed to register schedule for {row['id']}: {e}")

    def register_workflow(self, workflow_id: str, trigger_config: dict):
        if not self.scheduler:
            return
        sched = parse_schedule_trigger(trigger_config)
        if not sched:
            return
        
        job_id = f"wf_{workflow_id}"
        
        if sched["type"] == "interval":
            self.scheduler.add_job(
                self._fire_workflow, "interval",
                minutes=sched.get("minutes", 15),
                id=job_id, replace_existing=True,
                args=[workflow_id, {"trigger": "schedule"}])
        elif sched["type"] == "cron":
            self.scheduler.add_job(
                self._fire_workflow, "cron",
                hour=sched.get("hour", "*"),
                minute=sched.get("minute", 0),
                day=sched.get("day","*"),
                day_of_week=sched.get("day_of_week","*"),
                id=job_id, replace_existing=True,
                args=[workflow_id, {"trigger": "schedule"}])
        elif sched["type"] == "cron_expr":
            parts = sched["cron"].split()
            if len(parts) == 5:
                self.scheduler.add_job(
                    self._fire_workflow, CronTrigger.from_crontab(sched["cron"]),
                    id=job_id, replace_existing=True,
                    args=[workflow_id, {"trigger": "schedule"}])

    def unregister_workflow(self, workflow_id: str):
        if self.scheduler:
            try: self.scheduler.remove_job(f"wf_{workflow_id}")
            except: pass

    async def _fire_workflow(self, workflow_id: str, trigger_data: dict):
        from execution.engine import workflow_engine
        logger.info(f"Scheduler firing workflow {workflow_id}")
        try:
            result = await workflow_engine.run(workflow_id, trigger_data)
            logger.info(f"Scheduled run {workflow_id}: {result.get('status')}")
        except Exception as e:
            logger.error(f"Scheduled run failed {workflow_id}: {e}")

    async def _poll_all_rss(self):
        """Poll all RSS-triggered active workflows."""
        from connectors.executor import poll_rss
        from execution.engine import workflow_engine

        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT id, trigger_config FROM workflows WHERE status='on' AND trigger_type='rss'")
            rows = await cursor.fetchall()
        
        for row in rows:
            try:
                cfg = json.loads(row["trigger_config"] or "{}")
                feed_url = cfg.get("config",{}).get("feed_url","")
                if not feed_url:
                    continue
                items = await poll_rss(feed_url, self.rss_poll_states.get(feed_url, ""))
                if items:
                    self.rss_poll_states[feed_url] = items[0].get("guid","")
                    for item in items:
                        await workflow_engine.run(row["id"], {"trigger": "rss", **item})
            except Exception as e:
                logger.error(f"RSS poll error {row['id']}: {e}")


scheduler = WorkflowScheduler()
