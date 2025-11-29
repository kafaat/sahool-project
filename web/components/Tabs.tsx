'use client';

import React from 'react';

interface Tab {
  id: string;
  label: string;
}

interface TabsProps {
  tabs: Tab[];
  activeId: string;
  onChange: (id: string) => void;
}

export function Tabs({ tabs, activeId, onChange }: TabsProps) {
  return (
    <div className="flex gap-2 border-b border-slate-200 text-xs">
      {tabs.map((t) => {
        const active = t.id === activeId;
        return (
          <button
            key={t.id}
            type="button"
            onClick={() => onChange(t.id)}
            className={`rounded-t-md px-3 py-1.5 ${
              active
                ? 'border border-b-white border-slate-200 bg-white font-semibold text-slate-900'
                : 'border border-transparent bg-slate-50 text-slate-500 hover:bg-slate-100'
            }`}
          >
            {t.label}
          </button>
        );
      })}
    </div>
  );
}
