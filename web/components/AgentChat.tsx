'use client';

import React, { useState } from 'react';
import type { FieldSummary } from '@/lib/api';
import { askAgentFieldAdvice, type AgentReply } from '@/lib/api';

interface Props {
  tenantId: number;
  field?: FieldSummary | null;
}

export function AgentChat({ tenantId, field }: Props) {
  const [message, setMessage] = useState('');
  const [reply, setReply] = useState<AgentReply | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const canSend = !!field && message.trim().length > 0 && !loading;

  const handleSend = async () => {
    if (!field) return;
    setLoading(true);
    setError(null);
    try {
      const res = await askAgentFieldAdvice({
        tenantId,
        fieldId: field.id,
        message,
      });
      setReply(res);
    } catch (e) {
      console.error(e);
      setError('Failed to contact field assistant.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4 text-xs shadow-sm">
      <div className="mb-2 flex items-center justify-between">
        <div className="text-[10px] font-semibold uppercase tracking-wide text-slate-500">
          Field Assistant (Agent-AI)
        </div>
        {field && (
          <div className="text-[10px] text-slate-400">
            Field: <span className="font-medium text-slate-700">{field.name || `#${field.id}`}</span>
          </div>
        )}
      </div>
      {!field && (
        <div className="mb-2 text-[11px] text-slate-400">
          Select a field first to start a conversation.
        </div>
      )}
      <textarea
        className="mt-1 w-full rounded-md border border-slate-200 bg-slate-50 p-2 text-[11px] outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500"
        rows={3}
        placeholder="Ask about irrigation, NDVI drop, stress, or recommendations for this field..."
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        disabled={!field || loading}
      />
      <div className="mt-2 flex items-center justify-between">
        <button
          type="button"
          onClick={handleSend}
          disabled={!canSend}
          className={`inline-flex items-center rounded-md px-3 py-1.5 text-[11px] font-medium ${
            canSend
              ? 'bg-emerald-600 text-white hover:bg-emerald-700'
              : 'bg-slate-200 text-slate-500'
          }`}
        >
          {loading ? 'Thinking…' : 'Ask Assistant'}
        </button>
        {error && (
          <div className="text-[10px] text-rose-600">
            {error}
          </div>
        )}
      </div>
      {reply && (
        <div className="mt-3 rounded-md border border-emerald-100 bg-emerald-50 p-2 text-[11px] text-slate-800">
          <div className="mb-1 flex items-center justify-between">
            <span className="text-[10px] font-semibold uppercase tracking-wide text-emerald-700">
              Assistant reply
            </span>
            {reply.priority && (
              <span className="rounded-full bg-emerald-600 px-2 py-[1px] text-[9px] font-semibold text-white">
                {reply.priority}
              </span>
            )}
          </div>
          <pre className="whitespace-pre-wrap text-[11px] text-slate-800">
            {reply.reply}
          </pre>
        </div>
      )}
    </div>
  );
}
