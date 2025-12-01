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
