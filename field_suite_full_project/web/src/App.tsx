import React from 'react';
import { FieldProvider, useFieldContext } from './context/FieldContext';
import { FieldToolbar } from './components/Toolbar';
import { FieldList } from './components/FieldList';
import { FieldMap } from './components/FieldMap';
import { ToastContainer } from './components/Toast';
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
          <div style={{ marginTop: 8 }}>
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
    </div>
  );
};

const App: React.FC = () => {
  return (
    <FieldProvider>
      <AppContent />
    </FieldProvider>
  );
};

export default App;
