/**
 * AG-UI Event System
 * Handles bi-directional communication between agent and user interface
 */

import { AGUIEventType, AGUIEventUnion, AGUIMessage, AGUIToolCall } from './types';

type EventCallback = (event: AGUIEventUnion) => void;

class AGUIEventEmitter {
  private listeners: Map<AGUIEventType | '*', Set<EventCallback>> = new Map();
  private messageBuffer: AGUIMessage[] = [];
  private currentRunId: string | null = null;
  private toolCallBuffer: Map<string, AGUIToolCall> = new Map();

  // Subscribe to events
  on(eventType: AGUIEventType | '*', callback: EventCallback): () => void {
    if (!this.listeners.has(eventType)) {
      this.listeners.set(eventType, new Set());
    }
    this.listeners.get(eventType)!.add(callback);

    // Return unsubscribe function
    return () => {
      this.listeners.get(eventType)?.delete(callback);
    };
  }

  // Emit an event
  emit(event: AGUIEventUnion): void {
    // Process event internally
    this.processEvent(event);

    // Notify specific listeners
    this.listeners.get(event.type)?.forEach((cb) => cb(event));

    // Notify wildcard listeners
    this.listeners.get('*')?.forEach((cb) => cb(event));
  }

  // Process events internally
  private processEvent(event: AGUIEventUnion): void {
    switch (event.type) {
      case AGUIEventType.RUN_STARTED:
        this.currentRunId = event.runId;
        break;

      case AGUIEventType.RUN_FINISHED:
      case AGUIEventType.RUN_ERROR:
        this.currentRunId = null;
        break;

      case AGUIEventType.TEXT_MESSAGE_START:
        this.messageBuffer.push({
          id: event.messageId,
          role: event.role,
          content: '',
          createdAt: new Date(event.timestamp),
          metadata: { isStreaming: true },
        });
        break;

      case AGUIEventType.TEXT_MESSAGE_CONTENT:
        const msgIndex = this.messageBuffer.findIndex((m) => m.id === event.messageId);
        if (msgIndex !== -1) {
          this.messageBuffer[msgIndex].content += event.delta;
        }
        break;

      case AGUIEventType.TEXT_MESSAGE_END:
        const endMsgIndex = this.messageBuffer.findIndex((m) => m.id === event.messageId);
        if (endMsgIndex !== -1) {
          this.messageBuffer[endMsgIndex].metadata = {
            ...this.messageBuffer[endMsgIndex].metadata,
            isStreaming: false,
          };
        }
        break;

      case AGUIEventType.TOOL_CALL_START:
        this.toolCallBuffer.set(event.toolCallId, {
          id: event.toolCallId,
          name: event.toolName,
          arguments: {},
          status: 'running',
        });
        break;

      case AGUIEventType.TOOL_CALL_ARGS:
        const toolCall = this.toolCallBuffer.get(event.toolCallId);
        if (toolCall) {
          try {
            const args = JSON.parse(event.delta);
            toolCall.arguments = { ...toolCall.arguments, ...args };
          } catch {
            // Handle partial JSON
          }
        }
        break;

      case AGUIEventType.TOOL_CALL_END:
        const endToolCall = this.toolCallBuffer.get(event.toolCallId);
        if (endToolCall) {
          endToolCall.status = 'completed';
          endToolCall.result = event.result;
        }
        break;
    }
  }

  // Get current messages
  getMessages(): AGUIMessage[] {
    return [...this.messageBuffer];
  }

  // Get current run ID
  getCurrentRunId(): string | null {
    return this.currentRunId;
  }

  // Check if running
  isRunning(): boolean {
    return this.currentRunId !== null;
  }

  // Get tool calls
  getToolCalls(): AGUIToolCall[] {
    return Array.from(this.toolCallBuffer.values());
  }

  // Clear state
  clear(): void {
    this.messageBuffer = [];
    this.toolCallBuffer.clear();
    this.currentRunId = null;
  }
}

// Singleton instance
export const aguiEvents = new AGUIEventEmitter();

// Helper to create events
export function createAGUIEvent<T extends AGUIEventUnion>(
  type: T['type'],
  data: Omit<T, 'type' | 'timestamp'>
): T {
  return {
    type,
    timestamp: Date.now(),
    ...data,
  } as T;
}

// Helper to generate unique IDs
export function generateId(): string {
  return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}
