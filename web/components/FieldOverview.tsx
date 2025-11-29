'use client';

import React from 'react';
import type {
  FieldSummary,
  FieldHealthInsight,
  FieldAlert,
  FieldTimelinePoint,
} from '@/lib/api';
import { TimelineChart } from '@/components/TimelineChart';
import { MapView } from '@/components/MapView';

interface Props {
  field?: FieldSummary | null;
  health?: FieldHealthInsight | null;
  alerts: FieldAlert[];
  timeline: FieldTimelinePoint[];
  loading?: boolean;
}

function chipColor(label: string | undefined) {
  if (!label) return 'bg-slate-200 text-slate-800';
  const l = label.toLowerCase();
  if (l.includes('excellent') || l.includes('جيد')) {
    return 'bg-emerald-100 text-emerald-800';
  }
  if (l.includes('medium') || l.includes('متوسط')) {
    return 'bg-amber-100 text-amber-800';
  }
  if (l.includes('stress') || l.includes('ضعيف') || l.includes('مرتفع')) {
    return 'bg-rose-100 text-rose-800';
  }
  return 'bg-slate-200 text-slate-800';
}

export function FieldOverview({
  field,
  health,
  alerts,
  timeline,
  loading,
}: Props) {
  if (!field) {
    return (
      <div className="flex flex-1 items-center justify-center rounded-lg border border-dashed border-slate-300 bg-slate-50">
        <div className="text-sm text-slate-400">
          Select a field from the left to view analytics.
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-1 flex-col gap-4">
      <section className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
        <div className="mb-3 flex items-center justify-between gap-2">
          <div>
            <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">
              Field Overview
            </div>
            <div className="text-base font-semibold text-slate-900">
              {field.name || `Field #${field.id}`}
            </div>
          </div>
          {health && (
            <div className="flex flex-col items-end text-right">
              <div className="text-[10px] uppercase tracking-wide text-slate-500">
                Health Score
              </div>
              <div className="text-xl font-semibold text-slate-900">
                {Math.round(health.score ?? 0)}
              </div>
              <div
                className={`mt-1 inline-flex items-center rounded-full px-2 py-[2px] text-[10px] font-medium ${chipColor(
                  health.label,
                )}`}
              >
                {health.label ?? 'N/A'}
              </div>
            </div>
          )}
        </div>
        <div className="grid gap-3 text-xs text-slate-600 sm:grid-cols-3">
          <div className="rounded-md bg-slate-50 px-3 py-2">
            <div className="text-[10px] uppercase tracking-wide text-slate-500">
              Area
            </div>
            <div className="mt-1 text-sm font-medium text-slate-900">
              {field.area_ha ? `${field.area_ha.toFixed(2)} ha` : '—'}
            </div>
          </div>
          <div className="rounded-md bg-slate-50 px-3 py-2">
            <div className="text-[10px] uppercase tracking-wide text-slate-500">
              Location
            </div>
            <div className="mt-1 text-[11px] text-slate-800">
              {field.centroid_lat && field.centroid_lon
                ? `${field.centroid_lat.toFixed(4)}, ${field.centroid_lon.toFixed(4)}`
                : '—'}
            </div>
          </div>
          <div className="rounded-md bg-slate-50 px-3 py-2">
            <div className="text-[10px] uppercase tracking-wide text-slate-500">
              NDVI / Weather Snapshot
            </div>
            <div className="mt-1 text-[11px] text-slate-800">
              {timeline.length > 0
                ? 'Timeline data available'
                : 'No timeline yet'}
            </div>
          </div>
        </div>
        {loading && (
          <div className="mt-3 text-[11px] text-slate-400">
            Loading latest analytics...
          </div>
        )}
      </section>

      <section className="grid gap-4 md:grid-cols-3">
        <div className="md:col-span-2 flex flex-col gap-3 rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
          <div className="mb-1 flex items-center justify-between">
            <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">
              NDVI & Weather Timeline
            </div>
            <div className="text-[10px] text-slate-400">
              Simple line chart (NDVI & ETo)
            </div>
          </div>
          <TimelineChart data={timeline} />
        </div>

        <div className="space-y-3">
          <MapView field={field} />
          <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
            <div className="mb-3 flex items-center justify-between">
              <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                Recent Alerts
              </div>
              <div className="text-[10px] text-slate-400">
                Last {alerts.length} items
              </div>
            </div>
            <div className="max-h-56 space-y-2 overflow-y-auto text-[11px]">
              {alerts.length === 0 && (
                <div className="text-slate-400">
                  No alerts for this field yet.
                </div>
              )}
              {alerts.map((a) => (
                <div
                  key={a.id}
                  className="rounded-md border border-slate-100 bg-slate-50 px-2 py-2"
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-[10px] font-semibold text-slate-800">
                      {a.title}
                    </span>
                    <span className="text-[9px] text-slate-400">
                      {new Date(a.created_at).toLocaleDateString()}
                    </span>
                  </div>
                  <div className="mt-1 text-[10px] text-slate-600">
                    {a.message}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
