import json
from typing import Optional, List

from fastapi import FastAPI, File, UploadFile, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from sqlalchemy.orm import Session

from db import SessionLocal, engine
from models import FieldModel, FieldZoneModel
from services.ndvi_service import NDVIService
from services.sentinel_service import SentinelService

from shapely import wkt
from shapely.geometry import mapping


app = FastAPI(title="Field Suite NDVI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


from models import Base
Base.metadata.create_all(bind=engine)


@app.get("/")
def health_check():
    return {"status": "healthy", "service": "Field Suite NDVI API", "version": "1.0.0"}


@app.get("/fields/")
def list_fields(db: Session = Depends(get_db)):
    rows = db.query(FieldModel).all()
    results = []
    for f in rows:
        try:
            geom = wkt.loads(f.geom_wkt)
            coords = list(geom.exterior.coords)
            results.append({
                "id": f.id,
                "name": f.name,
                "geometryType": f.geometry_type,
                "coordinates": [coords],
            })
        except:
            continue
    return results


@app.post("/fields/ndvi-detect")
async def ndvi_detect(
    threshold: float = 0.4,
    n_zones: int = 3,
    red_band: UploadFile | None = File(None),
    nir_band: UploadFile | None = File(None),
    use_sentinel: bool = False,
    date: Optional[str] = None,
    aoi_wkt: Optional[str] = None,
    db: Session = Depends(get_db),
):
    if use_sentinel:
        if not date or not aoi_wkt:
            return {"error": "date + aoi_wkt required"}

        pid = SentinelService.search_product(aoi_wkt, date)
        zip_path = f"/tmp/{pid}.zip"
        workdir = f"/tmp/{pid}"

        SentinelService.download_product(pid, zip_path)
        red_path, nir_path = SentinelService.get_bands_paths_from_zip(zip_path, workdir)

    else:
        if red_band is None or nir_band is None:
            return {"error": "upload B04 & B08 or use_sentinel=true"}

        red_path = f"/tmp/{red_band.filename}"
        nir_path = f"/tmp/{nir_band.filename}"
        with open(red_path, "wb") as f:
            f.write(await red_band.read())
        with open(nir_path, "wb") as f:
            f.write(await nir_band.read())

    ndvi, transform = NDVIService.compute_ndvi(red_path, nir_path)

    base_polygon = NDVIService.ndvi_to_polygon(ndvi, transform, threshold)
    if base_polygon is None:
        return {"status": "no-field-detected"}

    zones = NDVIService.ndvi_zones(ndvi, transform, n_zones)

    field_row = FieldModel(
        name=f"NDVI {threshold}",
        geometry_type="Polygon",
        geom_wkt=base_polygon.wkt,
        metadata_json=json.dumps({"thr": threshold}),
    )
    db.add(field_row)
    db.commit()
    db.refresh(field_row)

    zone_json = []
    for z in zones:
        zm = FieldZoneModel(
            field_id=field_row.id,
            level=z["level"],
            min_ndvi=z["range"][0],
            max_ndvi=z["range"][1],
            geom_wkt=z["polygon"].wkt,
        )
        db.add(zm)
        db.commit()
        db.refresh(zm)

        zone_json.append({
            "type": "Feature",
            "geometry": mapping(z["polygon"]),
            "properties": {
                "id": zm.id,
                "level": zm.level,
                "min": zm.min_ndvi,
                "max": zm.max_ndvi,
            }
        })

    return {
        "id": field_row.id,
        "polygon": mapping(base_polygon),
        "zones": {
            "type": "FeatureCollection",
            "features": zone_json
        }
    }


@app.get("/fields/{field_id}/zones")
def get_field_zones(field_id: int, db: Session = Depends(get_db)):
    rows = db.query(FieldZoneModel).filter(FieldZoneModel.field_id == field_id).all()
    feats = []
    for z in rows:
        geom = wkt.loads(z.geom_wkt)
        feats.append({
            "type": "Feature",
            "geometry": mapping(geom),
            "properties": {
                "id": z.id,
                "level": z.level,
                "min": z.min_ndvi,
                "max": z.max_ndvi,
            }
        })
    return {
        "type": "FeatureCollection",
        "features": feats
    }


@app.post("/ndvi/heatmap")
async def ndvi_heatmap(
    red_band: UploadFile = File(...),
    nir_band: UploadFile = File(...),
):
    red_path = f"/tmp/{red_band.filename}"
    nir_path = f"/tmp/{nir_band.filename}"

    with open(red_path, "wb") as f:
        f.write(await red_band.read())
    with open(nir_path, "wb") as f:
        f.write(await nir_band.read())

    ndvi, _ = NDVIService.compute_ndvi(red_path, nir_path)
    png = NDVIService.ndvi_heatmap_png(ndvi)

    return Response(content=png, media_type="image/png")
