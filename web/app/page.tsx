import Link from 'next/link';

export default function HomePage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-100">
      <div className="rounded-lg border border-slate-200 bg-white px-6 py-5 text-center shadow-sm">
        <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">
          Sahool
        </div>
        <div className="mt-1 text-lg font-semibold text-slate-900">
          Farmer Dashboard
        </div>
        <p className="mt-2 max-w-xs text-xs text-slate-500">
          Go to the field monitoring view for a specific tenant.
        </p>
        <div className="mt-4 space-y-2 text-xs">
          <div className="text-[10px] text-slate-400">
            Example (tenant_id = 1):
          </div>
          <Link
            href="/tenant/1"
            className="inline-flex items-center rounded-md bg-emerald-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-emerald-700"
          >
            Open Tenant #1 dashboard
          </Link>
        </div>
      </div>
    </div>
  );
}
