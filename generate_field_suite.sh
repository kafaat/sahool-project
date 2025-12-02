#!/bin/bash
set -e

# ============================================================
#  Field Suite – Full Project Generator (Backend + Web + Mobile)
# ============================================================

BASE="field_suite_full_project"
echo "🔧 Generating project in: $BASE"
mkdir -p $BASE

# ============================================
# SHARED MODELS
# ============================================
mkdir -p $BASE/shared/models

cat > $BASE/shared/models/field_boundary.ts << 'EOF'
export type GeometryType = 'Polygon' | 'Rectangle' | 'Circle' | 'Pivot';

export interface FieldMetadata {
  source?: 'manual' | 'auto_ndvi' | 'auto_ai' | 'import_gis';
  createdAt?: string;
  updatedAt?: string;
  cropType?: string;
  notes?: string;
}

export interface FieldBoundary {
  id?: string;
  name: string;
  geometryType: GeometryType;
  coordinates: number[][][];
  center?: [number, number];
  radiusMeters?: number;
  metadata?: FieldMetadata;
}
EOF

# ============================================
# BACKEND (FastAPI)
# ============================================
mkdir -p $BASE/backend

cat > $BASE/backend/requirements.txt << 'EOF'
fastapi
uvicorn
pydantic
EOF

cat > $BASE/backend/main.py << 'EOF'
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
EOF

# ============================================
# WEB (React + MapLibre)
# ============================================
mkdir -p $BASE/web/src/components
mkdir -p $BASE/web/src/shared/models

# Copy shared model
cp $BASE/shared/models/field_boundary.ts $BASE/web/src/shared/models/

# App.tsx
cat > $BASE/web/src/App.tsx << 'EOF'
import React, { useState } from 'react';
import type { FieldBoundary, GeometryType } from './shared/models/field_boundary';
import { FieldToolbar } from './components/Toolbar';
import { FieldMap } from './components/FieldMap';

const App: React.FC = () => {
  const [activeTool, setActiveTool] = useState<GeometryType | 'select'>('select');
  const [selectedField, setSelectedField] = useState<FieldBoundary | null>(null);

  return (
    <div style={{ display: 'flex', height: '100vh', fontFamily: 'sans-serif' }}>
      <aside style={{ width: 300, borderRight: '1px solid #ddd', padding: 16 }}>
        <h2>Field Tools (Web)</h2>

        <FieldToolbar
          activeTool={activeTool}
          onChangeTool={setActiveTool}
          onRunAutoDetect={async () => {
            try {
              const res = await fetch('http://localhost:8000/fields/auto-detect', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ mock: true }),
              });
              const data = await res.json();
              alert("Auto-detect returned " + data.fields.length);
            } catch (e) {
              alert("Backend unreachable");
            }
          }}
        />

        {selectedField && (
          <div style={{ marginTop: 16 }}>
            <h4>Selected Field</h4>
            <p>{selectedField.name}</p>
          </div>
        )}
      </aside>

      <main style={{ flex: 1 }}>
        <FieldMap
          activeTool={activeTool}
          onFieldSaved={setSelectedField}
        />
      </main>
    </div>
  );
};

export default App;
EOF

# Toolbar.tsx
cat > $BASE/web/src/components/Toolbar.tsx << 'EOF'
import React from 'react';
import type { GeometryType } from '../shared/models/field_boundary';

interface Props {
  activeTool: GeometryType | 'select';
  onChangeTool: (t: GeometryType | 'select') => void;
  onRunAutoDetect: () => void;
}

const TOOLS = [
  ['select', 'Select / Edit'],
  ['Polygon', 'Polygon'],
  ['Rectangle', 'Rectangle'],
  ['Circle', 'Circle'],
  ['Pivot', 'Pivot'],
];

export const FieldToolbar: React.FC<Props> = ({ activeTool, onChangeTool, onRunAutoDetect }) => (
  <div>
    <h3>Tools</h3>
    {TOOLS.map(([id, label]) => (
      <button
        key={id}
        onClick={() => onChangeTool(id as any)}
        style={{
          width: '100%',
          marginBottom: 8,
          background: activeTool === id ? '#e0f3ff' : '#fff',
          padding: 8,
        }}
      >
        {label}
      </button>
    ))}

    <button style={{ width: '100%', padding: 8 }} onClick={onRunAutoDetect}>
      Auto Detect (Mock)
    </button>
  </div>
);
EOF

# FieldMap.tsx
cat > $BASE/web/src/components/FieldMap.tsx << 'EOF'
import React, { useEffect, useRef, useState } from 'react';
import maplibregl from 'maplibre-gl';
import type { GeometryType, FieldBoundary } from '../shared/models/field_boundary';

import 'maplibre-gl/dist/maplibre-gl.css';

interface Props {
  activeTool: GeometryType | 'select';
  onFieldSaved: (f: FieldBoundary) => void;
}

type Coord = [number, number];

export const FieldMap: React.FC<Props> = ({ activeTool, onFieldSaved }) => {
  const container = useRef(null);
  const map = useRef<any>(null);
  const [coords, setCoords] = useState<Coord[]>([]);

  useEffect(() => {
    if (map.current) return;
    map.current = new maplibregl.Map({
      container: container.current!,
      style: 'https://demotiles.maplibre.org/style.json',
      center: [45, 15],
      zoom: 5,
    });
    map.current.on('click', (e: any) => {
      if (activeTool === 'Polygon') {
        const p: Coord = [e.lngLat.lng, e.lngLat.lat];
        setCoords((c) => [...c, p]);
      }
    });
  });

  const finish = async () => {
    if (coords.length < 3) return alert("Polygon incomplete");

    const boundary: FieldBoundary = {
      name: "Polygon Field (Web)",
      geometryType: "Polygon",
      coordinates: [[...coords, coords[0]]],
      metadata: { source: 'manual' },
    };

    await fetch("http://localhost:8000/fields/", {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(boundary),
    });

    onFieldSaved(boundary);
    setCoords([]);
    alert("Saved");
  };

  return (
    <div style={{ height: '100%', position: 'relative' }}>
      <div ref={container} style={{ height: '100%' }} />
      {activeTool === 'Polygon' && coords.length >= 3 && (
        <button
          onClick={finish}
          style={{ position: 'absolute', top: 20, right: 20, padding: 10 }}
        >
          Finish Polygon
        </button>
      )}
    </div>
  );
};
EOF

# ============================================
# MOBILE (Flutter)
# ============================================
mkdir -p $BASE/mobile/lib

cat > $BASE/mobile/lib/main.dart << 'EOF'
import 'package:flutter/material.dart';
import 'field_map_page.dart';

void main() {
  runApp(const FieldSuiteApp());
}

class FieldSuiteApp extends StatelessWidget {
  const FieldSuiteApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Field Suite Mobile',
      home: const FieldMapPage(),
    );
  }
}
EOF

cat > $BASE/mobile/lib/field_map_page.dart << 'EOF'
import 'package:flutter/material.dart';
import 'package:maplibre_gl/maplibre_gl.dart';

enum Tool { select, polygon }

class FieldMapPage extends StatefulWidget {
  const FieldMapPage({super.key});
  @override
  State<FieldMapPage> createState() => _FieldMapPageState();
}

class _FieldMapPageState extends State<FieldMapPage> {
  Tool tool = Tool.select;
  List<LatLng> pts = [];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("Field Tools (Mobile)")),
      body: Stack(
        children: [
          MaplibreMap(
            styleString: "https://demotiles.maplibre.org/style.json",
            initialCameraPosition:
                const CameraPosition(target: LatLng(15, 45), zoom: 5),
            onMapClick: (p, c) {
              if (tool == Tool.polygon) {
                setState(() => pts.add(c));
              }
            },
          ),
          Positioned(
            left: 10,
            top: 10,
            child: Column(children: [
              ElevatedButton(
                  onPressed: () => setState(() => tool = Tool.select),
                  child: const Text("Select")),
              ElevatedButton(
                  onPressed: () => setState(() => tool = Tool.polygon),
                  child: const Text("Polygon")),
            ]),
          ),
        ],
      ),
    );
  }
}
EOF

# === DONE ===
echo "✅ Project successfully generated in: $BASE"
