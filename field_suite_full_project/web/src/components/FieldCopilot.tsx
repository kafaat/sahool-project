/**
 * Field Copilot Component
 * AI-powered assistant for field management using AG-UI protocol
 */

import React, { useState } from 'react';
import { useCopilotChat } from '@copilotkit/react-core';
import { useFieldActions } from '../ag-ui/useFieldActions';

interface QuickAction {
  id: string;
  label: string;
  prompt: string;
  icon: React.ReactNode;
}

const QUICK_ACTIONS: QuickAction[] = [
  {
    id: 'list',
    label: 'List Fields',
    prompt: 'Show me all my fields with their details',
    icon: (
      <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2">
        <line x1="8" y1="6" x2="21" y2="6" />
        <line x1="8" y1="12" x2="21" y2="12" />
        <line x1="8" y1="18" x2="21" y2="18" />
        <line x1="3" y1="6" x2="3.01" y2="6" />
        <line x1="3" y1="12" x2="3.01" y2="12" />
        <line x1="3" y1="18" x2="3.01" y2="18" />
      </svg>
    ),
  },
  {
    id: 'detect',
    label: 'Auto Detect',
    prompt: 'Auto-detect field boundaries from satellite imagery',
    icon: (
      <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2">
        <circle cx="11" cy="11" r="8" />
        <line x1="21" y1="21" x2="16.65" y2="16.65" />
      </svg>
    ),
  },
  {
    id: 'stats',
    label: 'Statistics',
    prompt: 'Show me statistics about all my fields',
    icon: (
      <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2">
        <line x1="18" y1="20" x2="18" y2="10" />
        <line x1="12" y1="20" x2="12" y2="4" />
        <line x1="6" y1="20" x2="6" y2="14" />
      </svg>
    ),
  },
  {
    id: 'recommend',
    label: 'Recommendations',
    prompt: 'Give me crop recommendations for my selected field',
    icon: (
      <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M12 2v4m0 12v4M4.93 4.93l2.83 2.83m8.48 8.48l2.83 2.83M2 12h4m12 0h4M4.93 19.07l2.83-2.83m8.48-8.48l2.83-2.83" />
      </svg>
    ),
  },
];

export const FieldCopilot: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [inputValue, setInputValue] = useState('');

  // Register field actions with CopilotKit
  useFieldActions();

  const { appendMessage, messages, isLoading } = useCopilotChat();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (inputValue.trim() && !isLoading) {
      appendMessage({ role: 'user', content: inputValue });
      setInputValue('');
    }
  };

  const handleQuickAction = (action: QuickAction) => {
    appendMessage({ role: 'user', content: action.prompt });
  };

  return (
    <>
      {/* Floating Action Button */}
      <button
        className="copilot-fab"
        onClick={() => setIsOpen(!isOpen)}
        title="Field Assistant"
      >
        {isOpen ? (
          <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="18" y1="6" x2="6" y2="18" />
            <line x1="6" y1="6" x2="18" y2="18" />
          </svg>
        ) : (
          <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
          </svg>
        )}
      </button>

      {/* Chat Panel */}
      {isOpen && (
        <div className="copilot-panel">
          <div className="copilot-header">
            <div className="copilot-title">
              <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M12 2L2 7l10 5 10-5-10-5z" />
                <path d="M2 17l10 5 10-5" />
                <path d="M2 12l10 5 10-5" />
              </svg>
              <span>Field Assistant</span>
            </div>
            <button className="copilot-close" onClick={() => setIsOpen(false)}>
              <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="18" y1="6" x2="6" y2="18" />
                <line x1="6" y1="6" x2="18" y2="18" />
              </svg>
            </button>
          </div>

          {/* Quick Actions */}
          <div className="copilot-quick-actions">
            {QUICK_ACTIONS.map((action) => (
              <button
                key={action.id}
                className="quick-action-btn"
                onClick={() => handleQuickAction(action)}
                disabled={isLoading}
              >
                {action.icon}
                <span>{action.label}</span>
              </button>
            ))}
          </div>

          {/* Messages */}
          <div className="copilot-messages">
            {messages.length === 0 ? (
              <div className="copilot-welcome">
                <svg viewBox="0 0 24 24" width="48" height="48" fill="none" stroke="currentColor" strokeWidth="1.5">
                  <circle cx="12" cy="12" r="10" />
                  <path d="M8 14s1.5 2 4 2 4-2 4-2" />
                  <line x1="9" y1="9" x2="9.01" y2="9" />
                  <line x1="15" y1="9" x2="15.01" y2="9" />
                </svg>
                <h3>Welcome to Field Assistant</h3>
                <p>I can help you manage your agricultural fields. Ask me anything or use the quick actions above.</p>
              </div>
            ) : (
              messages.map((msg, idx) => (
                <div key={idx} className={`copilot-message ${msg.role}`}>
                  <div className="message-avatar">
                    {msg.role === 'user' ? '👤' : '🤖'}
                  </div>
                  <div className="message-content">
                    {typeof msg.content === 'string'
                      ? msg.content
                      : JSON.stringify(msg.content, null, 2)}
                  </div>
                </div>
              ))
            )}
            {isLoading && (
              <div className="copilot-message assistant loading">
                <div className="message-avatar">🤖</div>
                <div className="message-content">
                  <div className="typing-indicator">
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Input */}
          <form className="copilot-input" onSubmit={handleSubmit}>
            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder="Ask about your fields..."
              disabled={isLoading}
            />
            <button type="submit" disabled={!inputValue.trim() || isLoading}>
              <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="22" y1="2" x2="11" y2="13" />
                <polygon points="22 2 15 22 11 13 2 9 22 2" />
              </svg>
            </button>
          </form>
        </div>
      )}
    </>
  );
};
