'use client';

import React, { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { AppShell } from '@/components/Layout';
import { FieldList } from '@/components/FieldList';
import { FieldOverview } from '@/components/FieldOverview';
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
import { AgentChat } from '@/components/AgentChat';

export default function TenantDashboardPage() {
  const params = useParams();
  const tenantId = Number(params.tenantId);

  const [fields, setFields] = useState<FieldSummary[]>([]);
  const [selectedField, setSelectedField] = useState<FieldSummary | null>(null);
  const [health, setHealth] = useState<FieldHealthInsight | null>(null);
  const [alerts, setAlerts] = useState<FieldAlert[]>([]);
  const [timeline, setTimeline] = useState<FieldTimelinePoint[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!tenantId) return;
    setError(null);
    fetchFields(tenantId)
      .then((items) => {
        setFields(items);
        if (items.length > 0) {
          setSelectedField(items[0]);
        }
      })
      .catch((err) => {
        console.error(err);
        setError('Failed to load fields from API');
      });
  }, [tenantId]);

  useEffect(() => {
    if (!tenantId || !selectedField) return;
    setLoading(true);
    setError(null);

    Promise.all([
      fetchFieldHealth(tenantId, selectedField.id).catch(() => null),
      fetchFieldAlerts(tenantId, selectedField.id).catch(() => []),
      fetchFieldTimeline(tenantId, selectedField.id).catch(() => []),
    ])
      .then(([h, a, t]) => {
        setHealth(h as FieldHealthInsight | null);
        setAlerts(a as FieldAlert[]);
        setTimeline(t as FieldTimelinePoint[]);
      })
      .catch((err) => {
        console.error(err);
        setError('Failed to load analytics for field');
      })
      .finally(() => setLoading(false));
  }, [tenantId, selectedField?.id]);

  return (
    <AppShell>
      <FieldList
        fields={fields}
        selectedId={selectedField?.id}
        onSelect={(f) => setSelectedField(f)}
      />
      <div className="flex flex-1 flex-col gap-3">
        {error && (
          <div className="rounded-md border border-rose-200 bg-rose-50 px-3 py-2 text-[11px] text-rose-700">
            {error}
          </div>
        )}
        <FieldOverview
          field={selectedField}
          health={health}
          alerts={alerts}
          timeline={timeline}
          loading={loading}
        />
      </div>
    <div className="mt-3">
        <AgentChat tenantId={tenantId} field={selectedField} />
      </div>
    </AppShell>
  );
}
