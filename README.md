# AutoFlow — Workflow Automation Platform

A **fully local, Zapier-equivalent** workflow automation platform. Real connectors, real scheduling, real webhooks — no cloud dependencies.

---

## What Works (vs Zapier)

| Feature | Zapier | AutoFlow |
|---|---|---|
| Visual workflow builder | ✅ | ✅ |
| 700+ app directory | ✅ | ✅ 13 apps |
| Real API connectors | ✅ | ✅ All connectors call real APIs |
| Webhook triggers | ✅ | ✅ Real HTTP receiver + HMAC |
| Schedule triggers | ✅ | ✅ Cron/interval via APScheduler |
| Conditional logic (Filter) | ✅ | ✅ 10 operators |
| Data formatter | ✅ | ✅ 40+ text/number/date/JSON ops |
| Storage (key-value) | ✅ | ✅ SQLite-backed with expiry |
| Delay / wait | ✅ | ✅ |
| Step context `{{variables}}` | ✅ | ✅ Full template resolver |
| Run history + logs | ✅ | ✅ Per-step output |
| Credential management | ✅ | ✅ Fernet-encrypted vault |
| Connection testing | ✅ | ✅ Hits real auth endpoints |
| Duplicate workflow | ✅ | ✅ |
| RSS triggers | ✅ | ✅ Polled every 5 min |
| Multi-path branching | ✅ | 🔜 |
| Error retries | ✅ | 🔜 |
| AI-assist builder | ❌ | ✅ Local LLM (Ollama) |
| Offline / private | ❌ | ✅ 100% local |
| Free / unlimited runs | ❌ | ✅ |

---

## Quick Start

```bash
# 1. Clone / unzip this repo
# 2. Run setup
chmod +x setup.sh && ./setup.sh

# 3. Terminal A — backend
cd backend && source .venv/bin/activate
uvicorn main:app --reload --port 8000

# 4. Terminal B — frontend
cd frontend && npm run dev

# 5. Open http://localhost:5173
```

---

## Apps & Connectors

### Communication
| App | Triggers | Actions |
|-----|---------|---------|
| **Gmail** | New Email | Send Email, Find Email, Create Draft |
| **Slack** | New Channel Message | Post Message, Send DM, Set Status |

### Data & Databases
| App | Triggers | Actions |
|-----|---------|---------|
| **Google Sheets** | New Row | Append Row, Update Row, Lookup Row |
| **Airtable** | New Record | Create Record, Update Record, Find Record |
| **Notion** | New DB Item | Create Page, Append to Page, Update Page |

### Developer & Project
| App | Triggers | Actions |
|-----|---------|---------|
| **GitHub** | New Issue, New PR | Create Issue, Create Comment |
| **Trello** | New Card, Card Moved | Create Card, Move Card, Add Comment |
| **Webhooks** | Catch Webhook | POST Request, GET Request |
| **RSS** | New Feed Item | — |

### Built-in Tools (no auth)
| App | Actions |
|-----|---------|
| **Formatter** | 40+ text, number, date, JSON, utility ops |
| **Filter** | Only continue if conditions met (10 operators) |
| **Delay** | Wait N seconds, or until datetime |
| **Storage** | Set/Get/Increment persistent key-value data |
| **Schedule** | Every X min, hourly, daily, weekly, monthly, cron |

---

## Template Variables

In any action input field, reference data from previous steps:

```
{{trigger.body.email}}       — webhook/trigger payload field
{{trigger.body.issue.title}} — nested field
{{step1.output}}             — output of step with output_key "step1"
{{formatter_step.output}}    — formatter result
{{today.output}}             — date formatter result
```

---

## API Reference

```
GET  /api/workflows/            List all workflows
POST /api/workflows/            Create workflow
GET  /api/workflows/{id}        Get workflow
PUT  /api/workflows/{id}        Update workflow
PATCH /api/workflows/{id}/toggle Toggle on/off
DELETE /api/workflows/{id}      Delete
POST /api/workflows/{id}/run_sync  Test run (sync)
GET  /api/workflows/{id}/runs   Run history

GET  /api/connections/apps      App directory
POST /api/connections/          Add connection
POST /api/connections/{id}/test Test credentials

POST /api/webhooks/create?workflow_id=  Create webhook URL
POST /api/webhooks/receive/{path}       Fire webhook (trigger endpoint)

GET  /api/analytics/summary     Platform metrics
```

---

## Adding a Real Gmail Connection

1. Go to **Connections** → click Gmail
2. Enter your Gmail address
3. Generate an App Password at `myaccount.google.com/apppasswords`
   - Enable 2FA first, then go to Security → App passwords
4. Paste the 16-char app password
5. Click **Connect** then **Test**

---

## Architecture

```
backend/
  main.py                   FastAPI app + lifespan
  connectors/
    registry.py             App catalogue (13 apps, 40+ actions)
    executor.py             Real API calls for every connector
  execution/
    engine.py               Step-by-step workflow runner
  scheduler/
    runner.py               APScheduler cron/interval + RSS poller
  credentials/
    vault.py                Fernet encryption at rest
  api/routes/
    workflows.py            CRUD + run endpoints
    connections.py          App connections + testing
    webhooks.py             Real HTTP webhook receiver
    analytics.py            Metrics
  core/
    database.py             SQLite schema (8 tables)
    models.py               Pydantic schemas
    config.py               Settings

frontend/src/
  pages/
    Dashboard.jsx           Stats + run chart
    WorkflowsPage.jsx       List + toggle + duplicate
    WorkflowEditor.jsx      Visual step builder
    ConnectionsPage.jsx     App directory + credential forms
    HistoryPage.jsx         Run logs with step drill-down
  components/
    Sidebar.jsx
    Notifications.jsx
  store/useStore.js         Zustand global state
  utils/api.js              Axios client
```
