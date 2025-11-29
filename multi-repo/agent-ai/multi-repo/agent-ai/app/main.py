from fastapi import FastAPI
from app.api.routes import router as agent_router

app = FastAPI(title="agent-ai", version="1.0.0")

@app.get("/health")
def health():
    return {"service": "agent-ai", "status": "ok"}

app.include_router(agent_router)