"""Seed demo workflows into the database"""
import asyncio, sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'backend'))

from core.database import init_db, DB_PATH
import aiosqlite
from datetime import datetime
import uuid

DEMO_WORKFLOWS = [
  {
    "name": "New GitHub Issue → Slack Alert",
    "description": "Posts a Slack message whenever a new GitHub issue is opened",
    "trigger_type": "webhook",
    "trigger_config": {"type":"webhook","config":{"endpoint":"github-issues"}},
    "steps": [
      {
        "app_key": "formatter", "action": "text",
        "input_map": {
          "operation": "uppercase",
          "input": "{{trigger.body.issue.title}}"
        },
        "output_key": "title_upper", "halt_on_error": False
      },
      {
        "app_key": "slack", "action": "post_message",
        "input_map": {
          "channel": "#dev-alerts",
          "text": ":bug: New issue: {{trigger.body.issue.title}}\n{{trigger.body.issue.html_url}}"
        },
        "output_key": "slack_result", "halt_on_error": True
      }
    ]
  },
  {
    "name": "Daily 9am Report",
    "description": "Runs every weekday at 9am and posts a standup prompt to Slack",
    "trigger_type": "schedule",
    "trigger_config": {"type":"schedule","config":{"trigger_action":"every_day","time":"09:00","timezone":"UTC"}},
    "steps": [
      {
        "app_key": "formatter", "action": "date_time",
        "input_map": {"operation": "now", "format": "%A %B %d, %Y"},
        "output_key": "today", "halt_on_error": False
      },
      {
        "app_key": "slack", "action": "post_message",
        "input_map": {
          "channel": "#standup",
          "text": "Good morning team! It's {{today.output}}.\n\nPlease share:\n• What did you complete yesterday?\n• What are you working on today?\n• Any blockers?"
        },
        "output_key": "standup_msg", "halt_on_error": False
      }
    ]
  },
  {
    "name": "Webhook → Airtable Logger",
    "description": "Receives any webhook payload and logs it as an Airtable record",
    "trigger_type": "webhook",
    "trigger_config": {"type":"webhook","config":{"endpoint":"airtable-logger"}},
    "steps": [
      {
        "app_key": "formatter", "action": "date_time",
        "input_map": {"operation": "now", "format": "%Y-%m-%d %H:%M:%S"},
        "output_key": "timestamp", "halt_on_error": False
      },
      {
        "app_key": "formatter", "action": "json",
        "input_map": {
          "operation": "stringify",
          "input": "{{trigger.body}}"
        },
        "output_key": "payload_str", "halt_on_error": False
      },
      {
        "app_key": "airtable", "action": "create_record",
        "input_map": {
          "base_id": "YOUR_BASE_ID",
          "table_name": "Webhook Logs",
          "fields": "{\"Timestamp\": \"{{timestamp.output}}\", \"Source\": \"{{trigger.endpoint}}\", \"Payload\": \"{{payload_str.output}}\"}"
        },
        "output_key": "airtable_record", "halt_on_error": False
      }
    ]
  },
  {
    "name": "Filter + Conditional Email",
    "description": "Only sends email if a form submission has 'urgent' in the message",
    "trigger_type": "webhook",
    "trigger_config": {"type":"webhook","config":{}},
    "steps": [
      {
        "app_key": "filter", "action": "only_continue_if",
        "input_map": {
          "conditions": "[{\"field\":\"{{trigger.body.message}}\",\"operator\":\"contains\",\"value\":\"urgent\"}]"
        },
        "output_key": "filter_result", "halt_on_error": True
      },
      {
        "app_key": "gmail", "action": "send_email",
        "input_map": {
          "to": "team@company.com",
          "subject": "🚨 Urgent message received",
          "body": "An urgent message was received:\n\n{{trigger.body.message}}\n\nFrom: {{trigger.body.name}} <{{trigger.body.email}}>"
        },
        "output_key": "email_result", "halt_on_error": False
      }
    ]
  }
]

async def seed():
    await init_db()
    async with aiosqlite.connect(DB_PATH) as db:
        existing = await db.execute("SELECT COUNT(*) FROM workflows")
        count = (await existing.fetchone())[0]
        if count > 0:
            print(f"  {count} workflows already exist, skipping seed")
            return

        now = datetime.utcnow().isoformat()
        for wf in DEMO_WORKFLOWS:
            wf_id = str(uuid.uuid4())
            await db.execute("""
                INSERT INTO workflows (id, name, description, status, trigger_type, trigger_config, steps, created_at, updated_at)
                VALUES (?,?,?,?,?,?,?,?,?)
            """, (wf_id, wf["name"], wf["description"], "off",
                  wf["trigger_type"], json.dumps(wf["trigger_config"]),
                  json.dumps(wf["steps"]), now, now))
            print(f"  ✓ {wf['name']}")
        await db.commit()
    print("Demo workflows seeded.")

if __name__ == "__main__":
    asyncio.run(seed())
