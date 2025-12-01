import React from 'react';
import type { GeometryType } from '../shared/models/field_boundary';

interface Props {
  activeTool: GeometryType | 'select';
  onChangeTool: (t: GeometryType | 'select') => void;
  onRunAutoDetect: () => void;
}

const TOOLS = [
  ['select', 'Select / Edit'],
  ['Polygon', 'Polygon'],
  ['Rectangle', 'Rectangle'],
  ['Circle', 'Circle'],
  ['Pivot', 'Pivot'],
];

export const FieldToolbar: React.FC<Props> = ({ activeTool, onChangeTool, onRunAutoDetect }) => (
  <div>
    <h3>Tools</h3>
    {TOOLS.map(([id, label]) => (
      <button
        key={id}
        onClick={() => onChangeTool(id as any)}
        style={{
          width: '100%',
          marginBottom: 8,
          background: activeTool === id ? '#e0f3ff' : '#fff',
          padding: 8,
        }}
      >
        {label}
      </button>
    ))}

    <button style={{ width: '100%', padding: 8 }} onClick={onRunAutoDetect}>
      Auto Detect (Mock)
    </button>
  </div>
);
