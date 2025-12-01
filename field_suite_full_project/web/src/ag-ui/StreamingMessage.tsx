/**
 * AG-UI Streaming Message Component
 * Displays real-time streaming responses from the agent
 */

import React, { useEffect, useState } from 'react';
import { aguiEvents } from './events';
import { AGUIEventType, AGUIMessage } from './types';

interface StreamingMessageProps {
  messageId: string;
  className?: string;
}

export const StreamingMessage: React.FC<StreamingMessageProps> = ({
  messageId,
  className = '',
}) => {
  const [content, setContent] = useState('');
  const [isComplete, setIsComplete] = useState(false);

  useEffect(() => {
    const unsubscribeContent = aguiEvents.on(
      AGUIEventType.TEXT_MESSAGE_CONTENT,
      (event) => {
        if (event.type === AGUIEventType.TEXT_MESSAGE_CONTENT) {
          if (event.messageId === messageId) {
            setContent((prev) => prev + event.delta);
          }
        }
      }
    );

    const unsubscribeEnd = aguiEvents.on(
      AGUIEventType.TEXT_MESSAGE_END,
      (event) => {
        if (event.type === AGUIEventType.TEXT_MESSAGE_END) {
          if (event.messageId === messageId) {
            setIsComplete(true);
          }
        }
      }
    );

    return () => {
      unsubscribeContent();
      unsubscribeEnd();
    };
  }, [messageId]);

  return (
    <div className={`streaming-message ${className} ${isComplete ? 'complete' : 'streaming'}`}>
      {content}
      {!isComplete && <span className="cursor">▊</span>}
    </div>
  );
};

/**
 * AG-UI Tool Call Status Component
 */
interface ToolCallStatusProps {
  toolCallId: string;
  toolName: string;
  className?: string;
}

export const ToolCallStatus: React.FC<ToolCallStatusProps> = ({
  toolCallId,
  toolName,
  className = '',
}) => {
  const [status, setStatus] = useState<'running' | 'completed' | 'error'>('running');
  const [result, setResult] = useState<unknown>(null);

  useEffect(() => {
    const unsubscribe = aguiEvents.on(AGUIEventType.TOOL_CALL_END, (event) => {
      if (event.type === AGUIEventType.TOOL_CALL_END) {
        if (event.toolCallId === toolCallId) {
          setStatus('completed');
          setResult(event.result);
        }
      }
    });

    return unsubscribe;
  }, [toolCallId]);

  return (
    <div className={`tool-call-status ${className} ${status}`}>
      <div className="tool-call-header">
        <span className="tool-icon">
          {status === 'running' ? '⚙️' : status === 'completed' ? '✅' : '❌'}
        </span>
        <span className="tool-name">{toolName}</span>
        <span className="tool-status">{status}</span>
      </div>
      {status === 'completed' && result && (
        <div className="tool-result">
          <pre>{JSON.stringify(result, null, 2)}</pre>
        </div>
      )}
    </div>
  );
};

/**
 * AG-UI Message List Component
 */
interface MessageListProps {
  messages: AGUIMessage[];
  className?: string;
}

export const MessageList: React.FC<MessageListProps> = ({
  messages,
  className = '',
}) => {
  return (
    <div className={`message-list ${className}`}>
      {messages.map((message) => (
        <div
          key={message.id}
          className={`message ${message.role}`}
        >
          <div className="message-role">{message.role}</div>
          <div className="message-content">
            {message.metadata?.isStreaming ? (
              <StreamingMessage messageId={message.id} />
            ) : (
              message.content
            )}
          </div>
          {message.metadata?.toolCalls?.map((tc) => (
            <ToolCallStatus
              key={tc.id}
              toolCallId={tc.id}
              toolName={tc.name}
            />
          ))}
        </div>
      ))}
    </div>
  );
};
