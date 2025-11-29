'use client';

import React from 'react';
import Link from 'next/link';
import type { FieldSummary } from '@/lib/api';

interface Props {
  tenantId: number;
  fields: FieldSummary[];
  selectedId?: number;
  onSelect: (field: FieldSummary) => void;
}

export function FieldList({ fields, selectedId, onSelect, tenantId }: Props) {
  return (
    <div className="w-72 shrink-0 rounded-lg border border-slate-200 bg-white shadow-sm">
      <div className="border-b border-slate-100 px-4 py-3">
        <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">
          Fields
        </div>
      </div>
      <div className="max-h-[520px] space-y-1 overflow-y-auto px-2 py-2 text-sm">
        {fields.length === 0 && (
          <div className="px-2 py-6 text-center text-xs text-slate-400">
            No fields yet for this tenant.
          </div>
        )}
        {fields.map((f) => {
          const active = f.id === selectedId;
          return (
            <button
              key={f.id}
              type="button"
              onClick={() => onSelect(f)}
              className={`flex w-full flex-col rounded-md px-3 py-2 text-left hover:bg-emerald-50 ${
                active
                  ? 'border border-emerald-500 bg-emerald-50'
                  : 'border border-transparent'
              }`}
            >
              <span className="text-xs font-semibold text-slate-800">
                {f.name || `Field #${f.id}`}
              </span>
              <span className="mt-0.5 text-[10px] text-emerald-700 underline">
                <Link href={`/tenant/${tenantId}/field/${f.id}`}>Open details</Link>
              </span>
              <span className="text-[10px] text-slate-500">
                Area:{' '}
                {f.area_ha ? `${f.area_ha.toFixed(2)} ha` : 'N/A'}
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
