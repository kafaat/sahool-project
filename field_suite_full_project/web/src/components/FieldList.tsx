import React from 'react';
import { useFieldContext } from '../context/FieldContext';

export const FieldList: React.FC = () => {
  const { state, selectField, deleteField, loadFields } = useFieldContext();

  return (
    <div className="toolbar-section">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
        <h3>Fields ({state.fields.length})</h3>
        <button
          className="icon-btn"
          onClick={loadFields}
          title="Refresh fields"
          disabled={state.isLoading}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M23 4v6h-6" />
            <path d="M1 20v-6h6" />
            <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15" />
          </svg>
        </button>
      </div>

      {state.fields.length === 0 ? (
        <div className="empty-state">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
            <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z" />
            <polyline points="3.27 6.96 12 12.01 20.73 6.96" />
            <line x1="12" y1="22.08" x2="12" y2="12" />
          </svg>
          <p>No fields yet</p>
          <p style={{ fontSize: '0.75rem', marginTop: 4 }}>
            Use drawing tools or auto-detect to add fields
          </p>
        </div>
      ) : (
        <div className="field-list">
          {state.fields.map((field) => (
            <div
              key={field.id}
              className={`field-item ${state.selectedFieldId === field.id ? 'selected' : ''}`}
              onClick={() => selectField(field.id || null)}
            >
              <div className="field-item-info">
                <h4>{field.name}</h4>
                <p>
                  {field.geometryType} •{' '}
                  {field.metadata?.source || 'unknown'}
                </p>
              </div>
              <div className="field-item-actions">
                <button
                  className="icon-btn danger"
                  onClick={(e) => {
                    e.stopPropagation();
                    if (confirm(`Delete "${field.name}"?`)) {
                      deleteField(field.id!);
                    }
                  }}
                  title="Delete field"
                >
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <polyline points="3 6 5 6 21 6" />
                    <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
                    <line x1="10" y1="11" x2="10" y2="17" />
                    <line x1="14" y1="11" x2="14" y2="17" />
                  </svg>
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
