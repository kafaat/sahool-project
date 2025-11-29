'use client';

import React, { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { AppShell } from '@/components/Layout';
import { Tabs } from '@/components/Tabs';
import { TimelineChart } from '@/components/TimelineChart';
import { MapView } from '@/components/MapView';
import { AgentChat } from '@/components/AgentChat';
import {
  fetchFields,
  fetchFieldHealth,
  fetchFieldAlerts,
  fetchFieldTimeline,
  type FieldSummary,
  type FieldHealthInsight,
  type FieldAlert,
  type FieldTimelinePoint,
} from '@/lib/api';

const TAB_OVERVIEW = 'overview';
const TAB_NDVI = 'ndvi';
const TAB_WEATHER = 'weather';
const TAB_ALERTS = 'alerts';
const TAB_AI = 'ai';

export default function FieldDetailPage() {
  const params = useParams();
  const router = useRouter();
  const tenantId = Number(params.tenantId);
  const fieldId = Number(params.fieldId);

  const [activeTab, setActiveTab] = useState(TAB_OVERVIEW);
  const [field, setField] = useState<FieldSummary | null>(null);
  const [health, setHealth] = useState<FieldHealthInsight | null>(null);
  const [alerts, setAlerts] = useState<FieldAlert[]>([]);
  const [timeline, setTimeline] = useState<FieldTimelinePoint[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!tenantId || !fieldId) return;
    setError(null);
    setLoading(true);

    Promise.all([
      fetchFields(tenantId).catch(() => []),
      fetchFieldHealth(tenantId, fieldId).catch(() => null),
      fetchFieldAlerts(tenantId, fieldId).catch(() => []),
      fetchFieldTimeline(tenantId, fieldId).catch(() => []),
    ])
      .then(([fields, h, a, t]) => {
        const f = (fields as FieldSummary[]).find((ff) => ff.id === fieldId) || null;
        setField(f);
        setHealth(h as FieldHealthInsight | null);
        setAlerts(a as FieldAlert[]);
        setTimeline(t as FieldTimelinePoint[]);
      })
      .catch((e) => {
        console.error(e);
        setError('Failed to load field details.');
      })
      .finally(() => setLoading(false));
  }, [tenantId, fieldId]);

  const tabs = [
    { id: TAB_OVERVIEW, label: 'Overview' },
    { id: TAB_NDVI, label: 'NDVI & Soil' },
    { id: TAB_WEATHER, label: 'Weather' },
    { id: TAB_ALERTS, label: 'Alerts' },
    { id: TAB_AI, label: 'AI Assistant' },
  ];

  return (
    <AppShell>
      <div className="flex w-full flex-col gap-3">
        <button
          type="button"
          onClick={() => router.push(`/tenant/${tenantId}`)}
          className="inline-flex w-fit items-center rounded-md border border-slate-200 bg-white px-2 py-1 text-[11px] text-slate-600 hover:bg-slate-50"
        >
          ← Back to tenant fields
        </button>

        {error && (
          <div className="rounded-md border border-rose-200 bg-rose-50 px-3 py-2 text-[11px] text-rose-700">
            {error}
          </div>
        )}

        <div className="rounded-lg border border-slate-200 bg-white shadow-sm">
          <div className="border-b border-slate-200 px-4 py-3">
            <div className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">
              Field Details
            </div>
            <div className="text-sm font-semibold text-slate-900">
              {field?.name || (fieldId ? `Field #${fieldId}` : 'Field')}
            </div>
            <div className="mt-1 text-[11px] text-slate-500">
              Tenant #{tenantId}
            </div>
          </div>
          <div className="px-4 pt-3">
            <Tabs tabs={tabs} activeId={activeTab} onChange={setActiveTab} />
          </div>
          <div className="px-4 pb-4 pt-3 text-xs">
            {activeTab === TAB_OVERVIEW && (
              <div className="grid gap-3 md:grid-cols-3">
                <div className="md:col-span-2 space-y-3">
                  <div className="rounded-md bg-slate-50 px-3 py-2">
                    <div className="text-[10px] uppercase tracking-wide text-slate-500">
                      Area & Location
                    </div>
                    <div className="mt-1 text-[11px] text-slate-800">
                      Area:{' '}
                      {field?.area_ha
                        ? `${field.area_ha.toFixed(2)} ha`
                        : '—'}
                      <br />
                      Location:{' '}
                      {field?.centroid_lat && field?.centroid_lon
                        ? `${field.centroid_lat.toFixed(4)}, ${field.centroid_lon.toFixed(4)}`
                        : '—'}
                    </div>
                  </div>
                  <div className="rounded-md bg-slate-50 px-3 py-2">
                    <div className="text-[10px] uppercase tracking-wide text-slate-500">
                      Health
                    </div>
                    {health ? (
                      <div className="mt-1 flex items-center gap-3 text-[11px]">
                        <span className="text-xl font-semibold text-slate-900">
                          {Math.round(health.score ?? 0)}
                        </span>
                        <span className="text-[11px] text-slate-700">
                          {health.label}
                        </span>
                      </div>
                    ) : (
                      <div className="mt-1 text-[11px] text-slate-400">
                        No health analytics yet.
                      </div>
                    )}
                  </div>
                </div>
                <div>
                  <MapView field={field ?? undefined} />
                </div>
              </div>
            )}

            {activeTab === TAB_NDVI && (
              <div className="space-y-3">
                <div className="text-[11px] text-slate-600">
                  NDVI & Soil timeline preview for this field.
                </div>
                <TimelineChart data={timeline} />
                <div className="rounded-md bg-slate-50 px-3 py-2 text-[11px] text-slate-500">
                  يمكن لاحقاً ربط طبقات NDVI Raster + Soil Indicators بالتفصيل في هذه الصفحة (Charts + Grid).
                </div>
              </div>
            )}

            {activeTab === TAB_WEATHER && (
              <div className="space-y-2 text-[11px] text-slate-600">
                <div>
                  This tab can display detailed weather forecast (ETo, rain, temperature)
                  derived from `weather-core` for the selected field.
                </div>
                <div className="rounded-md bg-slate-50 px-3 py-2 text-[11px] text-slate-500">
                  حالياً يتم عرض الـ timeline المختصر في تبويب NDVI، ويمكن توسعتها لاحقاً إلى جداول ورسوم بيانية خاصة بالطقس هنا.
                </div>
              </div>
            )}

            {activeTab === TAB_ALERTS && (
              <div className="space-y-2">
                <div className="text-[11px] text-slate-600">
                  Recent alerts for this field.
                </div>
                <div className="max-h-80 space-y-2 overflow-y-auto text-[11px]">
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
                          {new Date(a.created_at).toLocaleString()}
                        </span>
                      </div>
                      <div className="mt-1 text-[10px] text-slate-600">
                        {a.message}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {activeTab === TAB_AI && (
              <div className="space-y-2">
                <div className="text-[11px] text-slate-600">
                  Ask the field assistant (Agent-AI) about this field.
                </div>
                <AgentChat tenantId={tenantId} field={field ?? undefined} />
              </div>
            )}

            {loading && (
              <div className="mt-3 text-[11px] text-slate-400">
                Loading data...
              </div>
            )}
          </div>
        </div>
      </div>
    </AppShell>
  );
}
