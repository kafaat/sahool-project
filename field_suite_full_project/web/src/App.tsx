import React, { useState } from 'react';
import type { FieldBoundary, GeometryType } from './shared/models/field_boundary';
import { FieldToolbar } from './components/Toolbar';
import { FieldMap } from './components/FieldMap';

const App: React.FC = () => {
  const [activeTool, setActiveTool] = useState<GeometryType | 'select'>('select');
  const [selectedField, setSelectedField] = useState<FieldBoundary | null>(null);

  return (
    <div style={{ display: 'flex', height: '100vh', fontFamily: 'sans-serif' }}>
      <aside style={{ width: 300, borderRight: '1px solid #ddd', padding: 16 }}>
        <h2>Field Tools (Web)</h2>

        <FieldToolbar
          activeTool={activeTool}
          onChangeTool={setActiveTool}
          onRunAutoDetect={async () => {
            try {
              const res = await fetch('http://localhost:8000/fields/auto-detect', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ mock: true }),
              });
              const data = await res.json();
              alert("Auto-detect returned " + data.fields.length);
            } catch (e) {
              alert("Backend unreachable");
            }
          }}
        />

        {selectedField && (
          <div style={{ marginTop: 16 }}>
            <h4>Selected Field</h4>
            <p>{selectedField.name}</p>
          </div>
        )}
      </aside>

      <main style={{ flex: 1 }}>
        <FieldMap
          activeTool={activeTool}
          onFieldSaved={setSelectedField}
        />
      </main>
    </div>
  );
};

export default App;
