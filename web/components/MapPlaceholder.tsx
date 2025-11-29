'use client';

import React from 'react';
import type { FieldSummary } from '@/lib/api';

interface Props {
  field?: FieldSummary | null;
}

export function MapPlaceholder({ field }: Props) {
  return (
    <div className="rounded-lg border border-slate-200 bg-slate-50 p-3 text-xs text-slate-600">
      <div className="mb-1 flex items-center justify-between">
        <div className="text-[10px] font-semibold uppercase tracking-wide text-slate-500">
          Field Location (Preview)
        </div>
        <div className="text-[10px] text-slate-400">
          Map integration (MapLibre/Leaflet) can be added later
        </div>
      </div>
      <div className="mt-1 text-[11px]">
        {field && field.centroid_lat && field.centroid_lon ? (
          <>
            <div>
              Lat: <span className="font-mono">{field.centroid_lat.toFixed(5)}</span>
            </div>
            <div>
              Lon: <span className="font-mono">{field.centroid_lon.toFixed(5)}</span>
            </div>
            <div className="mt-2 text-[10px] text-slate-500">
              يمكن لاحقًا عرض الحقل على خريطة تفاعلية مع طبقات NDVI و الحدود.
            </div>
          </>
        ) : (
          <div className="text-slate-400">
            No centroid coordinates for this field yet.
          </div>
        )}
      </div>
    </div>
  );
}
