'use client';

import React from 'react';
import type { FieldTimelinePoint } from '@/lib/api';

interface Props {
  data: FieldTimelinePoint[];
}

const WIDTH = 420;
const HEIGHT = 120;
const PADDING_X = 24;
const PADDING_Y = 18;

export function TimelineChart({ data }: Props) {
  if (!data || data.length === 0) {
    return (
      <div className="flex h-24 items-center justify-center rounded-md border border-dashed border-slate-200 bg-slate-50 text-[11px] text-slate-400">
        No timeline data yet.
      </div>
    );
  }

  const points = data.slice(-24); // آخر 24 نقطة فقط
  const ndviValues = points
    .map((p) => (p.ndvi === null || p.ndvi === undefined ? null : p.ndvi))
    .filter((v): v is number => v !== null);
  const etoValues = points
    .map((p) => (p.eto === null || p.eto === undefined ? null : p.eto))
    .filter((v): v is number => v !== null);

  const minNdvi = ndviValues.length ? Math.min(...ndviValues) : 0;
  const maxNdvi = ndviValues.length ? Math.max(...ndviValues) : 1;
  const minEto = etoValues.length ? Math.min(...etoValues) : 0;
  const maxEto = etoValues.length ? Math.max(...etoValues) : 5;

  const toX = (idx: number) => {
    if (points.length === 1) return WIDTH / 2;
    const t = idx / (points.length - 1);
    return PADDING_X + t * (WIDTH - 2 * PADDING_X);
  };

  const toY = (v: number, minV: number, maxV: number) => {
    if (maxV === minV) return HEIGHT / 2;
    const norm = (v - minV) / (maxV - minV);
    return HEIGHT - PADDING_Y - norm * (HEIGHT - 2 * PADDING_Y);
  };

  const ndviPath = ndviValues.length
    ? points
        .map((p, idx) => {
          if (p.ndvi === null || p.ndvi === undefined) return null;
          const x = toX(idx);
          const y = toY(p.ndvi, minNdvi, maxNdvi);
          return `${idx === 0 ? 'M' : 'L'} ${x} ${y}`;
        })
        .filter(Boolean)
        .join(' ')
    : '';

  const etoPath = etoValues.length
    ? points
        .map((p, idx) => {
          if (p.eto === null || p.eto === undefined) return null;
          const x = toX(idx);
          const y = toY(p.eto, minEto, maxEto);
          return `${idx === 0 ? 'M' : 'L'} ${x} ${y}`;
        })
        .filter(Boolean)
        .join(' ')
    : '';

  return (
    <div className="rounded-md border border-slate-200 bg-slate-50 px-3 py-2">
      <div className="mb-1 flex items-center justify-between text-[10px] text-slate-500">
        <span>NDVI (خط أخضر) - ETo (خط أزرق)</span>
        <span>Last {points.length} points</span>
      </div>
      <svg
        width={WIDTH}
        height={HEIGHT}
        className="w-full"
        viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
      >
        <defs>
          <linearGradient id="gridFill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#e5e7eb" stopOpacity="0.5" />
            <stop offset="100%" stopColor="#f8fafc" stopOpacity="0.9" />
          </linearGradient>
        </defs>
        <rect
          x={0}
          y={0}
          width={WIDTH}
          height={HEIGHT}
          fill="url(#gridFill)"
          rx={6}
        />
        {/* محور أفقي بسيط */}
        <line
          x1={PADDING_X}
          y1={HEIGHT - PADDING_Y}
          x2={WIDTH - PADDING_X}
          y2={HEIGHT - PADDING_Y}
          stroke="#cbd5f5"
          strokeWidth={0.5}
        />
        {/* مسار NDVI */}
        {ndviPath && (
          <path
            d={ndviPath}
            fill="none"
            stroke="#059669"
            strokeWidth={1.6}
          />
        )}
        {/* مسار ETo */}
        {etoPath && (
          <path
            d={etoPath}
            fill="none"
            stroke="#2563eb"
            strokeWidth={1.2}
            strokeDasharray="3 3"
          />
        )}
      </svg>
    </div>
  );
}
