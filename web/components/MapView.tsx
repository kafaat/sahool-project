'use client';

import React, { useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import L from 'leaflet';
import type { FieldSummary } from '@/lib/api';
import 'leaflet/dist/leaflet.css';

// Fix default icon paths for Leaflet when bundling
// (Leaflet expects images to be in a specific folder)
const DefaultIcon = L.icon({
  iconUrl:
    'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  iconRetinaUrl:
    'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  shadowUrl:
    'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
});

L.Marker.prototype.options.icon = DefaultIcon;

interface Props {
  field?: FieldSummary | null;
}

export function MapView({ field }: Props) {
  // Default center: somewhere neutral if لا توجد إحداثيات
  const lat = field?.centroid_lat ?? 15.3694; // مثال: اليمن
  const lon = field?.centroid_lon ?? 44.1910;
  const hasCoords = !!field?.centroid_lat && !!field?.centroid_lon;

  // To avoid hydration issues, ensure window is defined (client-side only)
  useEffect(() => {
    // no-op, just to make sure this is client-side
  }, []);

  return (
    <div className="h-64 w-full overflow-hidden rounded-lg border border-slate-200 bg-slate-100">
      <MapContainer
        center={[lat, lon]}
        zoom={hasCoords ? 14 : 5}
        scrollWheelZoom={false}
        style={{ height: '100%', width: '100%' }}
      >
        <TileLayer
          attribution="&copy; OpenStreetMap contributors"
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        {hasCoords && (
          <Marker position={[field!.centroid_lat!, field!.centroid_lon!]}>
            <Popup>
              <div className="text-xs">
                <div className="font-semibold">
                  {field?.name || `Field #${field?.id}`}
                </div>
                <div>
                  Lat: {field?.centroid_lat?.toFixed(5)} <br />
                  Lon: {field?.centroid_lon?.toFixed(5)}
                </div>
                {field?.bbox && (
                  <div className="mt-1 text-[10px] text-slate-600">
                    BBox: [{field.bbox.map((v) => v.toFixed(4)).join(', ')}]
                  </div>
                )}
              </div>
            </Popup>
          </Marker>
        )}
      </MapContainer>
    </div>
  );
}
