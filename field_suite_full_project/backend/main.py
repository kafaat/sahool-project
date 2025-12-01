from fastapi import FastAPI, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Literal, AsyncGenerator
from uuid import uuid4
from datetime import datetime
import json
import asyncio

GeometryType = Literal['Polygon', 'Rectangle', 'Circle', 'Pivot']
SourceType = Literal['manual', 'auto_ndvi', 'auto_ai', 'import_gis']


class FieldMetadata(BaseModel):
    source: Optional[SourceType] = None
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None
    cropType: Optional[str] = None
    notes: Optional[str] = None


class FieldBoundary(BaseModel):
    id: Optional[str] = None
    name: str = Field(..., min_length=1, max_length=255)
    geometryType: GeometryType
    coordinates: List[List[List[float]]]
    center: Optional[List[float]] = None
    radiusMeters: Optional[float] = Field(default=None, ge=0)
    metadata: Optional[FieldMetadata] = None

    @field_validator('coordinates')
    @classmethod
    def validate_coordinates(cls, v):
        if not v or not v[0]:
            raise ValueError('Coordinates cannot be empty')
        for ring in v:
            if len(ring) < 3:
                raise ValueError('Each ring must have at least 3 points')
            for point in ring:
                if len(point) < 2:
                    raise ValueError('Each point must have at least 2 coordinates (lng, lat)')
                lng, lat = point[0], point[1]
                if not (-180 <= lng <= 180):
                    raise ValueError(f'Longitude {lng} out of range [-180, 180]')
                if not (-90 <= lat <= 90):
                    raise ValueError(f'Latitude {lat} out of range [-90, 90]')
        return v

    @field_validator('center')
    @classmethod
    def validate_center(cls, v):
        if v is not None:
            if len(v) < 2:
                raise ValueError('Center must have at least 2 coordinates (lng, lat)')
            lng, lat = v[0], v[1]
            if not (-180 <= lng <= 180):
                raise ValueError(f'Center longitude {lng} out of range [-180, 180]')
            if not (-90 <= lat <= 90):
                raise ValueError(f'Center latitude {lat} out of range [-90, 90]')
        return v


class AutoDetectRequest(BaseModel):
    mock: bool = True
    bounds: Optional[List[float]] = None


class AutoDetectResponse(BaseModel):
    fields: List[FieldBoundary]
    count: int = 0


class ZonesRequest(BaseModel):
    field: FieldBoundary
    zones: int = Field(default=3, ge=1, le=20)


class ZonesResponse(BaseModel):
    fields: List[FieldBoundary]
    count: int = 0


class FieldListResponse(BaseModel):
    fields: List[FieldBoundary]
    count: int


class ErrorResponse(BaseModel):
    detail: str


# AG-UI Event Models
class AGUIEvent(BaseModel):
    type: str
    timestamp: int
    runId: Optional[str] = None


class AGUIMessage(BaseModel):
    role: str
    content: str


class AGUIRequest(BaseModel):
    messages: List[AGUIMessage]
    threadId: Optional[str] = None


# Initialize FastAPI app
app = FastAPI(
    title="Field Suite Backend",
    description="API for managing agricultural field boundaries with AG-UI protocol support",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory database
FIELDS_DB: dict[str, FieldBoundary] = {}


def get_timestamp() -> str:
    return datetime.utcnow().isoformat() + "Z"


def get_ms_timestamp() -> int:
    return int(datetime.utcnow().timestamp() * 1000)


# AG-UI Event Helpers
def create_agui_event(event_type: str, run_id: str, **kwargs) -> str:
    event = {
        "type": event_type,
        "timestamp": get_ms_timestamp(),
        "runId": run_id,
        **kwargs
    }
    return f"data: {json.dumps(event)}\n\n"


async def stream_agui_response(
    run_id: str,
    message_id: str,
    content: str,
    tool_calls: Optional[List[dict]] = None
) -> AsyncGenerator[str, None]:
    """Stream AG-UI compatible events"""

    # RUN_STARTED
    yield create_agui_event("RUN_STARTED", run_id)
    await asyncio.sleep(0.05)

    # TEXT_MESSAGE_START
    yield create_agui_event("TEXT_MESSAGE_START", run_id, messageId=message_id, role="assistant")
    await asyncio.sleep(0.05)

    # Stream content word by word
    words = content.split(" ")
    for i, word in enumerate(words):
        delta = word + (" " if i < len(words) - 1 else "")
        yield create_agui_event("TEXT_MESSAGE_CONTENT", run_id, messageId=message_id, delta=delta)
        await asyncio.sleep(0.03)

    # TEXT_MESSAGE_END
    yield create_agui_event("TEXT_MESSAGE_END", run_id, messageId=message_id)
    await asyncio.sleep(0.05)

    # Tool calls if any
    if tool_calls:
        for tc in tool_calls:
            tool_call_id = str(uuid4())
            yield create_agui_event("TOOL_CALL_START", run_id, toolCallId=tool_call_id, toolName=tc["name"])
            await asyncio.sleep(0.05)
            yield create_agui_event("TOOL_CALL_ARGS", run_id, toolCallId=tool_call_id, delta=json.dumps(tc.get("args", {})))
            await asyncio.sleep(0.1)
            yield create_agui_event("TOOL_CALL_END", run_id, toolCallId=tool_call_id, result=tc.get("result"))
            await asyncio.sleep(0.05)

    # STATE_SNAPSHOT
    yield create_agui_event("STATE_SNAPSHOT", run_id, snapshot={
        "fieldsCount": len(FIELDS_DB),
        "fields": [{"id": f.id, "name": f.name} for f in FIELDS_DB.values()]
    })
    await asyncio.sleep(0.05)

    # RUN_FINISHED
    yield create_agui_event("RUN_FINISHED", run_id)


@app.get("/", tags=["Health"])
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Field Suite Backend",
        "version": "2.0.0",
        "protocol": "AG-UI",
        "capabilities": ["streaming", "tool_calls", "state_sync"]
    }


# AG-UI Compatible Endpoint
@app.post("/api/copilotkit", tags=["AG-UI"])
async def copilotkit_handler(request: Request):
    """AG-UI compatible streaming endpoint for CopilotKit"""
    body = await request.json()
    messages = body.get("messages", [])
    thread_id = body.get("threadId", str(uuid4()))

    run_id = str(uuid4())
    message_id = str(uuid4())

    # Parse the last user message
    user_message = ""
    if messages:
        last_message = messages[-1]
        user_message = last_message.get("content", "").lower()

    # Determine response based on user message
    response_content = ""
    tool_calls = []

    if "list" in user_message or "show" in user_message and "field" in user_message:
        fields = list(FIELDS_DB.values())
        if fields:
            field_list = ", ".join([f.name for f in fields])
            response_content = f"You have {len(fields)} field(s): {field_list}. Would you like more details about any specific field?"
        else:
            response_content = "You don't have any fields yet. Would you like me to help you create one or run auto-detection?"
        tool_calls = [{"name": "listFields", "args": {}, "result": {"count": len(fields)}}]

    elif "auto" in user_message and "detect" in user_message:
        response_content = "I'll run auto-detection to find field boundaries from satellite imagery. This uses NDVI analysis to identify crop boundaries."
        tool_calls = [{"name": "autoDetectFields", "args": {"mock": True}, "result": {"detected": 1}}]

    elif "stat" in user_message:
        fields = list(FIELDS_DB.values())
        response_content = f"Field Statistics: Total fields: {len(fields)}. " + \
            f"Types: {', '.join(set(f.geometryType for f in fields)) if fields else 'N/A'}. " + \
            "Would you like more detailed analytics?"
        tool_calls = [{"name": "getFieldStatistics", "args": {}, "result": {"total": len(fields)}}]

    elif "recommend" in user_message or "crop" in user_message:
        response_content = "Based on your field properties, I recommend: 1) Consider crop rotation with legumes to improve soil nitrogen. 2) The field shapes are suitable for precision agriculture. 3) Schedule soil testing before next planting season."
        tool_calls = [{"name": "getCropRecommendations", "args": {}, "result": {"recommendations": 3}}]

    elif "help" in user_message:
        response_content = "I can help you with: 1) Creating and managing field boundaries, 2) Auto-detecting fields from satellite imagery, 3) Splitting fields into management zones, 4) Providing crop recommendations, 5) Field statistics and analytics. What would you like to do?"

    elif "hello" in user_message or "hi" in user_message:
        response_content = "Hello! I'm your Field Assistant. I can help you manage your agricultural fields, detect boundaries, split into zones, and provide crop recommendations. What would you like to do today?"

    else:
        response_content = f"I understand you want to know about '{user_message}'. I can help with field management tasks like listing fields, auto-detection, zone splitting, and crop recommendations. What specific action would you like me to take?"

    return StreamingResponse(
        stream_agui_response(run_id, message_id, response_content, tool_calls),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


# AG-UI State Endpoint
@app.get("/api/copilotkit/state", tags=["AG-UI"])
async def get_agui_state():
    """Get current application state for AG-UI synchronization"""
    return {
        "fields": [f.model_dump() for f in FIELDS_DB.values()],
        "fieldsCount": len(FIELDS_DB),
        "lastUpdated": get_timestamp()
    }


@app.get("/fields/", response_model=FieldListResponse, tags=["Fields"])
def list_fields():
    """List all field boundaries"""
    fields = list(FIELDS_DB.values())
    return FieldListResponse(fields=fields, count=len(fields))


@app.get("/fields/{field_id}", response_model=FieldBoundary, tags=["Fields"],
         responses={404: {"model": ErrorResponse}})
def get_field(field_id: str):
    """Get a specific field by ID"""
    if field_id not in FIELDS_DB:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Field with ID '{field_id}' not found"
        )
    return FIELDS_DB[field_id]


@app.post("/fields/", response_model=FieldBoundary, status_code=status.HTTP_201_CREATED, tags=["Fields"])
def create_field(field: FieldBoundary):
    """Create a new field boundary"""
    field_id = field.id or str(uuid4())
    field.id = field_id

    if field.metadata is None:
        field.metadata = FieldMetadata()
    field.metadata.createdAt = get_timestamp()
    field.metadata.updatedAt = get_timestamp()

    FIELDS_DB[field_id] = field
    return field


@app.put("/fields/{field_id}", response_model=FieldBoundary, tags=["Fields"],
         responses={404: {"model": ErrorResponse}})
def update_field(field_id: str, field: FieldBoundary):
    """Update an existing field boundary"""
    if field_id not in FIELDS_DB:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Field with ID '{field_id}' not found"
        )

    field.id = field_id
    existing = FIELDS_DB[field_id]
    if field.metadata is None:
        field.metadata = FieldMetadata()
    if existing.metadata and existing.metadata.createdAt:
        field.metadata.createdAt = existing.metadata.createdAt
    field.metadata.updatedAt = get_timestamp()

    FIELDS_DB[field_id] = field
    return field


@app.delete("/fields/{field_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Fields"],
            responses={404: {"model": ErrorResponse}})
def delete_field(field_id: str):
    """Delete a field boundary"""
    if field_id not in FIELDS_DB:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Field with ID '{field_id}' not found"
        )
    del FIELDS_DB[field_id]


@app.post("/fields/auto-detect", response_model=AutoDetectResponse, tags=["Detection"])
def auto_detect(req: AutoDetectRequest):
    """Auto-detect field boundaries using NDVI/AI (mock implementation)"""
    timestamp = get_timestamp()
    demo_field = FieldBoundary(
        id=str(uuid4()),
        name="Auto Field (NDVI Mock)",
        geometryType="Polygon",
        coordinates=[[
            [45.0, 15.0],
            [45.1, 15.0],
            [45.1, 15.1],
            [45.0, 15.1],
            [45.0, 15.0],
        ]],
        metadata=FieldMetadata(
            source="auto_ndvi",
            createdAt=timestamp,
            updatedAt=timestamp,
            notes="Mock polygon returned by /fields/auto-detect",
        ),
    )
    FIELDS_DB[demo_field.id] = demo_field
    return AutoDetectResponse(fields=[demo_field], count=1)


@app.post("/fields/zones", response_model=ZonesResponse, tags=["Zones"])
def split_into_zones(req: ZonesRequest):
    """Split a field into management zones"""
    timestamp = get_timestamp()
    zones = []
    for i in range(req.zones):
        zone_metadata = FieldMetadata(
            source=req.field.metadata.source if req.field.metadata else None,
            createdAt=timestamp,
            updatedAt=timestamp,
            cropType=req.field.metadata.cropType if req.field.metadata else None,
            notes=f"Zone {i+1} of {req.zones} from '{req.field.name}'",
        )
        zones.append(
            FieldBoundary(
                id=str(uuid4()),
                name=f"{req.field.name} - Zone {i+1}",
                geometryType=req.field.geometryType,
                coordinates=req.field.coordinates,
                center=req.field.center,
                radiusMeters=req.field.radiusMeters,
                metadata=zone_metadata,
            )
        )
    return ZonesResponse(fields=zones, count=len(zones))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
