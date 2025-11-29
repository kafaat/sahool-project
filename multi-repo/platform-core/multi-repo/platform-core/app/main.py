from fastapi import FastAPI

from app.core.logging import configure_logging
from app.api.routes.auth import router as auth_router
from app.api.routes.tenants import router as tenants_router
from app.api.routes.users import router as users_router

configure_logging()
app = FastAPI(title="platform-core", version="1.0.0")


@app.get("/health")
def health():
    return {"status": "ok", "service": "platform-core"}


app.include_router(auth_router)
app.include_router(tenants_router)
app.include_router(users_router)