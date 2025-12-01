from fastapi import FastAPI
from contextlib import asynccontextmanager
import logging

from app.api.routes import router as agent_router
from app.services.knowledge_base import get_knowledge_base
from app.services.langchain_agent import get_agent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle"""
    # Startup
    logger.info("🚀 Starting Agent-AI service...")

    try:
        # Initialize knowledge base
        logger.info("📚 Initializing agricultural knowledge base...")
        kb = get_knowledge_base()
        logger.info(f"✅ Knowledge base initialized")

        # Initialize LangChain agent
        logger.info("🤖 Initializing LangChain agricultural agent...")
        agent = get_agent()
        logger.info(f"✅ Agent initialized with provider: {agent.llm_provider if agent.llm else 'rule-based'}")

        app.state.knowledge_base = kb
        app.state.agent = agent

        logger.info("✅ Agent-AI service ready!")

    except Exception as e:
        logger.error(f"❌ Error during startup: {e}", exc_info=True)
        # Continue anyway with degraded functionality
        logger.warning("⚠️  Service starting with limited functionality")

    yield

    # Shutdown
    logger.info("👋 Shutting down Agent-AI service...")


app = FastAPI(
    title="Sahool Agent-AI",
    description="Advanced Agricultural AI Agent with LangChain and RAG",
    version="2.0.0",
    lifespan=lifespan
)


@app.get("/health")
def health():
    """Health check endpoint"""
    return {
        "service": "agent-ai",
        "version": "2.0.0",
        "status": "ok"
    }


app.include_router(agent_router)
