'use client';

import React from 'react';

type LayoutProps = {
  children: React.ReactNode;
};

export function AppShell({ children }: LayoutProps) {
  return (
    <div className="min-h-screen bg-slate-100 text-slate-900">
      <header className="w-full border-b border-slate-200 bg-white/80 backdrop-blur-sm">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
          <div className="flex items-center gap-2">
            <div className="h-8 w-8 rounded bg-emerald-600" />
            <div>
              <div className="text-sm font-semibold uppercase tracking-wide text-emerald-700">
                Sahool
              </div>
              <div className="text-xs text-slate-500">
                Smart Agriculture Platform
              </div>
            </div>
          </div>
          <div className="text-xs text-slate-500">
            Farmer Dashboard (MVP)
          </div>
        </div>
      </header>
      <main className="mx-auto flex max-w-6xl gap-6 px-4 py-6">
        {children}
      </main>
    </div>
  );
}
