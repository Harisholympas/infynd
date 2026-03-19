"""AutoFlow - Zapier-equivalent Workflow Automation Platform"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.database import init_db
from core.config import settings
from scheduler.runner import scheduler
from rag.pipeline import RAGPipeline

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting AutoFlow Platform...")
    await init_db()
    # Initialize RAG pipeline (used by agents/intent and knowledge base ingestion)
    app.state.rag = RAGPipeline()
    try:
        await app.state.rag.initialize()
        logger.info("✅ RAG pipeline initialized")
    except Exception as e:
        logger.warning(f"⚠️ RAG pipeline failed to initialize: {e}")
    await scheduler.start()
    logger.info("AutoFlow ready.")
    yield
    await scheduler.stop()
    logger.info("AutoFlow shut down.")


app = FastAPI(title="AutoFlow", description="Zapier-equivalent local workflow automation",
              version="2.0.0", lifespan=lifespan)

app.add_middleware(CORSMiddleware,
    allow_origins=["http://localhost:3000","http://localhost:5173"],
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# Import and register all routers
from api.routes import workflows, connections, webhooks, analytics, execution

app.include_router(workflows.router, prefix="/api/workflows", tags=["workflows"])
app.include_router(connections.router, prefix="/api/connections", tags=["connections"])
app.include_router(webhooks.router, prefix="/api/webhooks", tags=["webhooks"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])
app.include_router(execution.router, prefix="/api/execution", tags=["execution"])

# Keep legacy routes for backwards compat
try:
    from api.routes import agents, voice, intent, rag, memory, mining
    app.include_router(agents.router, prefix="/api/agents", tags=["agents"])
    app.include_router(voice.router, prefix="/api/voice", tags=["voice"])
    app.include_router(intent.router, prefix="/api/intent", tags=["intent"])
    app.include_router(rag.router, prefix="/api/rag", tags=["rag"])
    app.include_router(memory.router, prefix="/api/memory", tags=["memory"])
    app.include_router(mining.router, prefix="/api/mining", tags=["mining"])
except Exception as e:
    logger.warning(f"Legacy routes skipped: {e}")

# New AI agent enhancement routes
try:
    from api.routes import knowledge_base, tools, auto_config, agent_memory
    app.include_router(knowledge_base.router)
    app.include_router(tools.router)
    app.include_router(auto_config.router)
    app.include_router(agent_memory.router)
    logger.info("✅ AI agent enhancement routes loaded (knowledge base, tools, auto-config, memory)")
except Exception as e:
    logger.warning(f"⚠️ AI agent enhancement routes failed to load: {e}")


@app.get("/")
async def root():
    return {"platform": "AutoFlow", "version": "2.0.0", "status": "online"}

@app.get("/health")
async def health():
    return {"status": "healthy", "scheduler": scheduler.scheduler is not None}
