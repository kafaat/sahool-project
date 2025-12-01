import React from 'react';
import { CopilotKit } from '@copilotkit/react-core';
import { FieldProvider, useFieldContext } from './context/FieldContext';
import { FieldToolbar } from './components/Toolbar';
import { FieldList } from './components/FieldList';
import { FieldMap } from './components/FieldMap';
import { ToastContainer } from './components/Toast';
import { FieldCopilot } from './components/FieldCopilot';
import './styles/main.css';

const AppContent: React.FC = () => {
  const { state } = useFieldContext();

  return (
    <div className="app-container">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-header">
          <h1>Field Suite</h1>
          <p>Agricultural Field Management</p>
          <div style={{ marginTop: 8, display: 'flex', gap: 8 }}>
            <span className={`status-badge ${state.isApiConnected ? 'online' : 'offline'}`}>
              <span
                style={{
                  width: 6,
                  height: 6,
                  borderRadius: '50%',
                  background: 'currentColor',
                  display: 'inline-block',
                }}
              />
              {state.isApiConnected ? 'API Connected' : 'API Offline'}
            </span>
            <span className="status-badge online" style={{ background: '#e0e7ff', color: '#4f46e5' }}>
              <svg width="10" height="10" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 2L2 7l10 5 10-5-10-5z" />
                <path d="M2 17l10 5 10-5" />
                <path d="M2 12l10 5 10-5" />
              </svg>
              AG-UI
            </span>
          </div>
        </div>

        <div style={{ flex: 1, overflowY: 'auto' }}>
          <FieldToolbar />
          <div style={{ padding: '0 16px 16px' }}>
            <FieldList />
          </div>
        </div>
      </aside>

      {/* Main Map Area */}
      <main className="main-content">
        <FieldMap />
      </main>

      {/* Toast Notifications */}
      <ToastContainer />

      {/* AG-UI Copilot Assistant */}
      <FieldCopilot />
    </div>
  );
};

const App: React.FC = () => {
  return (
    <CopilotKit runtimeUrl="/api/copilotkit">
      <FieldProvider>
        <AppContent />
      </FieldProvider>
    </CopilotKit>
  );
};

export default App;
