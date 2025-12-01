import React, { useState } from 'react';
import { useFieldContext, DrawingTool } from '../context/FieldContext';

interface ToolConfig {
  id: DrawingTool;
  label: string;
  icon: React.ReactNode;
}

const TOOLS: ToolConfig[] = [
  {
    id: 'select',
    label: 'Select',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M3 3l7.07 16.97 2.51-7.39 7.39-2.51L3 3z" />
      </svg>
    ),
  },
  {
    id: 'Polygon',
    label: 'Polygon',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <polygon points="12,2 22,8.5 22,15.5 12,22 2,15.5 2,8.5" />
      </svg>
    ),
  },
  {
    id: 'Rectangle',
    label: 'Rectangle',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <rect x="3" y="3" width="18" height="18" rx="2" />
      </svg>
    ),
  },
  {
    id: 'Circle',
    label: 'Circle',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <circle cx="12" cy="12" r="10" />
      </svg>
    ),
  },
  {
    id: 'Pivot',
    label: 'Pivot',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <circle cx="12" cy="12" r="10" />
        <line x1="12" y1="2" x2="12" y2="12" />
        <circle cx="12" cy="12" r="2" fill="currentColor" />
      </svg>
    ),
  },
];

export const FieldToolbar: React.FC = () => {
  const { state, setTool, autoDetect, splitIntoZones } = useFieldContext();
  const [zonesCount, setZonesCount] = useState(3);

  const selectedField = state.fields.find((f) => f.id === state.selectedFieldId);

  return (
    <div className="sidebar-content">
      {/* Drawing Tools */}
      <div className="toolbar-section">
        <h3>Drawing Tools</h3>
        <div className="tool-grid">
          {TOOLS.map((tool) => (
            <button
              key={tool.id}
              className={`tool-btn ${state.activeTool === tool.id ? 'active' : ''}`}
              onClick={() => setTool(tool.id)}
            >
              {tool.icon}
              <span>{tool.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Auto Detection */}
      <div className="toolbar-section">
        <h3>Auto Detection</h3>
        <button
          className="action-btn primary"
          onClick={autoDetect}
          disabled={state.isLoading}
        >
          {state.isLoading ? (
            <span className="spinner" />
          ) : (
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="11" cy="11" r="8" />
              <line x1="21" y1="21" x2="16.65" y2="16.65" />
            </svg>
          )}
          Auto Detect Fields
        </button>
      </div>

      {/* Zone Management */}
      {selectedField && (
        <div className="toolbar-section">
          <h3>Zone Management</h3>
          <div className="form-group">
            <label>Number of Zones</label>
            <select
              className="form-select"
              value={zonesCount}
              onChange={(e) => setZonesCount(Number(e.target.value))}
            >
              {[2, 3, 4, 5, 6, 8, 10].map((n) => (
                <option key={n} value={n}>
                  {n} Zones
                </option>
              ))}
            </select>
          </div>
          <button
            className="action-btn secondary"
            onClick={() => splitIntoZones(selectedField.id!, zonesCount)}
            disabled={state.isLoading}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <rect x="3" y="3" width="7" height="7" />
              <rect x="14" y="3" width="7" height="7" />
              <rect x="3" y="14" width="7" height="7" />
              <rect x="14" y="14" width="7" height="7" />
            </svg>
            Split "{selectedField.name}" into Zones
          </button>
        </div>
      )}

      {/* Selected Field Info */}
      {selectedField && (
        <div className="toolbar-section">
          <h3>Selected Field</h3>
          <div className="field-item selected" style={{ cursor: 'default' }}>
            <div className="field-item-info">
              <h4>{selectedField.name}</h4>
              <p>
                {selectedField.geometryType} •{' '}
                {selectedField.metadata?.source || 'unknown'}
              </p>
              {selectedField.metadata?.cropType && (
                <p>Crop: {selectedField.metadata.cropType}</p>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
