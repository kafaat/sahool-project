from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional, Literal
from uuid import uuid4

GeometryType = Literal['Polygon', 'Rectangle', 'Circle', 'Pivot']

class FieldMetadata(BaseModel):
    source: Optional[Literal['manual', 'auto_ndvi', 'auto_ai', 'import_gis']] = None
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None
    cropType: Optional[str] = None
    notes: Optional[str] = None

class FieldBoundary(BaseModel):
    id: Optional[str] = None
    name: str
    geometryType: GeometryType
    coordinates: List[List[List[float]]]
    center: Optional[List[float]] = None
    radiusMeters: Optional[float] = None
    metadata: Optional[FieldMetadata] = None

class AutoDetectRequest(BaseModel):
    mock: bool = True

class AutoDetectResponse(BaseModel):
    fields: List[FieldBoundary]

class ZonesRequest(BaseModel):
    field: FieldBoundary
    zones: int = 3

class ZonesResponse(BaseModel):
    fields: List[FieldBoundary]

app = FastAPI(title="Field Suite Backend (Demo)")

FIELDS_DB: dict[str, FieldBoundary] = {}

@app.get("/fields/", response_model=List[FieldBoundary])
def list_fields():
    return list(FIELDS_DB.values())

@app.post("/fields/", response_model=FieldBoundary)
def create_field(field: FieldBoundary):
    field_id = field.id or str(uuid4())
    field.id = field_id
    FIELDS_DB[field_id] = field
    return field

@app.post("/fields/auto-detect", response_model=AutoDetectResponse)
def auto_detect(req: AutoDetectRequest):
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
            notes="Mock polygon returned by /fields/auto-detect",
        ),
    )
    FIELDS_DB[demo_field.id] = demo_field
    return AutoDetectResponse(fields=[demo_field])

@app.post("/fields/zones", response_model=ZonesResponse)
def split_into_zones(req: ZonesRequest):
    zones = []
    for i in range(req.zones):
        zones.append(
            FieldBoundary(
                id=str(uuid4()),
                name=f"{req.field.name} - Zone {i+1}",
                geometryType=req.field.geometryType,
                coordinates=req.field.coordinates,
                center=req.field.center,
                radiusMeters=req.field.radiusMeters,
                metadata=req.field.metadata,
            )
        )
    return ZonesResponse(fields=zones)
