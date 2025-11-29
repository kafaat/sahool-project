from fastapi import FastAPI
from .routes.proxy_geo import router as proxy_geo
from .routes.proxy_imagery import router as proxy_imagery
from .routes.proxy_weather import router as proxy_weather
from .routes.proxy_soil import router as proxy_soil
from .routes.proxy_alerts import router as proxy_alerts
from .routes.nano_routes import router as nano_router
app=FastAPI(title="gateway-edge V62")
@app.get("/health")
def health(): return {"status":"ok","service":"gateway-edge"}
app.include_router(proxy_geo); app.include_router(proxy_imagery); app.include_router(proxy_weather)
app.include_router(proxy_soil); app.include_router(proxy_alerts); app.include_router(nano_router)