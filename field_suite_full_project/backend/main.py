from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Literal
from uuid import uuid4
from datetime import datetime

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
    bounds: Optional[List[float]] = None  # [minLng, minLat, maxLng, maxLat]


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


# Initialize FastAPI app
app = FastAPI(
    title="Field Suite Backend",
    description="API for managing agricultural field boundaries with geospatial support",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory database
FIELDS_DB: dict[str, FieldBoundary] = {}


def get_timestamp() -> str:
    return datetime.utcnow().isoformat() + "Z"


@app.get("/", tags=["Health"])
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "Field Suite Backend", "version": "1.0.0"}


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

    # Set timestamps
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

    # Preserve createdAt, update updatedAt
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
