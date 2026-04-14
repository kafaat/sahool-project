# Sahool Yemen Shared Library
# مكتبة سهول اليمن المشتركة

مكتبة Python مشتركة لجميع خدمات منصة سهول اليمن الزراعية.

## Installation

```bash
pip install -e ./libs-shared
# أو
pip install sahool-shared
```

## Components

### Models (النماذج)

```python
from sahool_shared.models import (
    Region, Farmer, Field, NDVIResult, WeatherData, Alert, User, Tenant
)
```

### Authentication (المصادقة)

```python
from sahool_shared.auth import (
    create_access_token,
    verify_token,
    hash_password,
    verify_password,
    get_current_user,
    require_role,
)

# Create tokens
tokens = create_access_token(user_id, tenant_id, role)

# FastAPI dependency
@app.get("/protected")
async def protected_route(user = Depends(get_current_user)):
    return {"user_id": user.user_id}

# Role-based access
@app.get("/admin")
async def admin_route(user = Depends(require_role("admin"))):
    return {"admin": True}
```

### Cache (التخزين المؤقت)

```python
from sahool_shared.cache import RedisCache, cached, get_cache

# Using cache directly
cache = await get_cache()
await cache.set("key", {"data": "value"}, ttl=3600)
data = await cache.get_json("key")

# Using decorator
@cached(ttl=300, prefix="weather")
async def get_weather(lat: float, lon: float):
    ...
```

### Events (الأحداث)

```python
from sahool_shared.events import (
    EventBus, publish_event,
    FieldCreatedEvent, NDVIProcessedEvent
)

# Publish event
event = FieldCreatedEvent.create(
    field_id="...",
    farmer_id="...",
    tenant_id="...",
    name="حقل القمح",
    area_hectares=10.5,
)
await publish_event(event)

# Subscribe to events
@subscribe("field.created")
async def handle_field_created(event):
    print(f"Field created: {event.data['field_id']}")
```

### Schemas (المخططات)

```python
from sahool_shared.schemas import (
    FieldCreate, FieldResponse, FieldListResponse,
    WeatherResponse, WeatherForecast,
    NDVIResponse, NDVITimeline,
    TokenResponse, UserResponse,
)
```

### Database (قاعدة البيانات)

```python
from sahool_shared.utils import get_db, DatabaseManager

# FastAPI dependency
@app.get("/fields")
async def get_fields(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Field))
    return result.scalars().all()

# Manual usage
manager = DatabaseManager(url="postgresql+asyncpg://...")
await manager.connect()
async with manager.session() as session:
    ...
```

## Environment Variables

```bash
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db
REDIS_URL=redis://localhost:6379/0
JWT_SECRET_KEY=your-secret-key
JWT_REFRESH_SECRET_KEY=your-refresh-secret
JWT_ACCESS_EXPIRE_MINUTES=30
JWT_REFRESH_EXPIRE_DAYS=7
```

## License

MIT License - Sahool Yemen 2024
