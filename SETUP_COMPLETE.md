# AutoFlow - Complete Setup Guide ✅

## System Status: FULLY OPERATIONAL

Your AutoFlow (Zapier-equivalent) workflow automation platform is now completely operational!

---

## 🎯 Quick Start

### Backend Server (FastAPI)
- **Status**: ✅ Running on `http://localhost:8000`
- **Health Check**: `http://localhost:8000/health`
- **API Docs**: `http://localhost:8000/docs` (Swagger UI)

### Frontend (React + Vite)
- **Status**: ✅ Running on `http://localhost:5174`
- **Open in Browser**: [http://localhost:5174](http://localhost:5174)

---

## 📊 What's Already Set Up

### Database
- ✅ SQLite database initialized: `data/platform.db`
- ✅ All schema tables created (workflows, app_connections, webhooks, etc.)
- ✅ Sample workflows seeded for demo purposes

### Backend Features
- ✅ FastAPI REST API with full CORS support
- ✅ Workflow CRUD operations
- ✅ Connection/credential management with encryption
- ✅ Webhook receiver for HTTP triggers
- ✅ Real workflow execution engine
- ✅ Scheduler for cron-based triggers
- ✅ Analytics and history tracking

### 15 Integrated Apps
Built-in apps with real API connectors:
- **Communication**: Gmail, Slack
- **Data**: Google Sheets, Airtable, Notion
- **Development**: GitHub, Trello, Webhooks, RSS
- **Utilities**: Formatter, Filter, Delay, Storage, Schedule, Paths

### Frontend Features
- ✅ Dashboard with analytics
- ✅ Workflow builder interface
- ✅ Connection management
- ✅ Execution history
- ✅ Real-time status updates

---

## 🚀 Running the System

### Option 1: Already Running (Background Processes)
Both servers are already started:
- Backend: `uvicorn main:app --reload --port 8000`
- Frontend: `npm run dev` (Vite)

### Option 2: Manual Start

**Terminal 1 - Backend:**
```bash
cd backend
.venv\Scripts\activate
uvicorn main:app --reload --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

---

## 🔧 Configuration

### Port Configuration
- Backend: `8000` (change in `backend/main.py`)
- Frontend: `5174` (Vite auto-assigned, try 5173 if needed)
- Database: `data/platform.db` (SQLite file-based)

### Environment Variables
Backend settings are in `backend/core/config.py`:
- `SECRET_KEY`: Encryption key for credentials (change in production)
- `SQLITE_PATH`: Database location
- `WEBHOOK_BASE_URL`: For webhook URL generation

---

## 🧪 Testing the API

### List Workflows
```bash
curl http://localhost:8000/api/workflows/
```

### Get Available Apps
```bash
curl http://localhost:8000/api/connections/apps
```

### Health Check
```bash
curl http://localhost:8000/health
```

---

## 📝 Example: Create a Workflow

### Via API
```bash
curl -X POST http://localhost:8000/api/workflows/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Workflow",
    "description": "Test automation",
    "trigger": {
      "type": "manual",
      "app_key": null,
      "config": {}
    },
    "steps": [
      {
        "app_key": "formatter",
        "action": "text",
        "input_map": {"operation": "uppercase", "input": "hello"},
        "output_key": "step1"
      }
    ]
  }'
```

### Via Frontend
1. Open http://localhost:5174
2. Click "New Workflow"
3. Configure trigger and steps
4. Save and enable

---

## 🔐 Security Notes

### Current Setup (Local Development)
- ✅ Credentials encrypted at rest using Fernet
- ✅ CORS configured for localhost only
- ✅ Default secret key (CHANGE IN PRODUCTION)

### Production Checklist
- [ ] Change `SECRET_KEY` in `backend/core/config.py`
- [ ] Update CORS origins
- [ ] Use PostgreSQL instead of SQLite
- [ ] Enable HTTPS/TLS
- [ ] Set up proper API authentication
- [ ] Use environment variables for secrets

---

## 🛠 Troubleshooting

### Backend won't start
```bash
# Check if port 8000 is in use
netstat -ano | findstr :8000

# Or use different port
uvicorn main:app --port 8001
```

### Frontend shows blank page
- Check browser console for errors
- Verify backend is running: `curl http://localhost:8000/health`
- Clear browser cache and reload

### Database errors
- Verify `data/platform.db` exists
- Run seed script: `python scripts/seed_db.py`
- Check file permissions

### Workflow execution fails
- Check workflow step configuration
- Verify API credentials are set correctly
- Review execution history in UI
- Check backend logs

---

## 📚 Key Files & Directories

```
backend/
├── main.py                 # FastAPI app entry point
├── core/
│   ├── config.py          # Settings
│   ├── database.py        # Schema & init
│   ├── models.py          # Pydantic models
│   └── llm.py             # LLM integration (optional)
├── api/routes/            # API endpoints
│   ├── workflows.py       # Workflow CRUD
│   ├── connections.py     # App connections
│   ├── webhooks.py        # Webhook receiver
│   ├── execution.py       # Run history
│   └── analytics.py       # Stats/dashboard
├── connectors/            # App integrations
│   ├── executor.py        # Execute steps
│   ├── registry.py        # App definitions
│   └── base.py            # Base classes
├── execution/
│   └── engine.py          # Workflow engine
└── scheduler/
    └── runner.py          # APScheduler integration

frontend/
├── src/
│   ├── App.jsx            # Main component
│   ├── pages/             # Page components
│   ├── components/        # UI components
│   ├── store/             # Zustand state
│   └── utils/
│       └── api.js         # API client
└── vite.config.js         # Vite configuration

data/
├── platform.db            # SQLite database
└── knowledge_base/        # RAG training data (optional)
```

---

## 🎉 Next Steps

1. **Explore the Dashboard**
   - View sample workflows
   - Check analytics
   - See execution history

2. **Create Your First Workflow**
   - Set up server-to-server connection (Gmail, Airtable, etc.)
   - Build workflow with triggers and actions
   - Test with manual run
   - Enable for production

3. **Set Up Real Credentials**
   - Configure API keys/tokens
   - Test connections
   - Enable live webhooks

4. **Monitor & Optimize**
   - Review execution logs
   - Track success rates
   - Adjust triggers/schedules

---

## 📞 Support

For issues or questions:
1. Check the troubleshooting section above
2. Review backend logs: `backend/.venv/` stdout
3. Check frontend console errors (F12 dev tools)
4. Verify database state with SQLite client

---

## 🗑️ Clean Start (if needed)

To reset everything:
```bash
# Stop servers

# Remove database
del data\platform.db

# Reinitialize
cd backend
.venv\Scripts\python.exe ..\scripts\seed_db.py

# Restart servers
```

---

**System Status**: ✅ FULLY OPERATIONAL

**Last Updated**: March 19, 2026
**Version**: 2.0.0
