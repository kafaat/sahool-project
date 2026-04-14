/**
 * AG-UI Protocol Types for Field Suite
 * Agent-User Interaction Protocol Implementation
 */

// AG-UI Event Types
export enum AGUIEventType {
  // Lifecycle Events
  RUN_STARTED = 'RUN_STARTED',
  RUN_FINISHED = 'RUN_FINISHED',
  RUN_ERROR = 'RUN_ERROR',

  // Streaming Events
  TEXT_MESSAGE_START = 'TEXT_MESSAGE_START',
  TEXT_MESSAGE_CONTENT = 'TEXT_MESSAGE_CONTENT',
  TEXT_MESSAGE_END = 'TEXT_MESSAGE_END',

  // Tool/Action Events
  TOOL_CALL_START = 'TOOL_CALL_START',
  TOOL_CALL_ARGS = 'TOOL_CALL_ARGS',
  TOOL_CALL_END = 'TOOL_CALL_END',

  // State Events
  STATE_SNAPSHOT = 'STATE_SNAPSHOT',
  STATE_DELTA = 'STATE_DELTA',

  // Custom Events
  CUSTOM = 'CUSTOM',
  RAW = 'RAW',
}

// Base Event Interface
export interface AGUIEvent {
  type: AGUIEventType;
  timestamp: number;
  runId?: string;
}

// Lifecycle Events
export interface RunStartedEvent extends AGUIEvent {
  type: AGUIEventType.RUN_STARTED;
  runId: string;
  threadId?: string;
}

export interface RunFinishedEvent extends AGUIEvent {
  type: AGUIEventType.RUN_FINISHED;
  runId: string;
}

export interface RunErrorEvent extends AGUIEvent {
  type: AGUIEventType.RUN_ERROR;
  runId: string;
  error: {
    code: string;
    message: string;
  };
}

// Text Message Events
export interface TextMessageStartEvent extends AGUIEvent {
  type: AGUIEventType.TEXT_MESSAGE_START;
  messageId: string;
  role: 'assistant' | 'user' | 'system';
}

export interface TextMessageContentEvent extends AGUIEvent {
  type: AGUIEventType.TEXT_MESSAGE_CONTENT;
  messageId: string;
  delta: string;
}

export interface TextMessageEndEvent extends AGUIEvent {
  type: AGUIEventType.TEXT_MESSAGE_END;
  messageId: string;
}

// Tool Call Events
export interface ToolCallStartEvent extends AGUIEvent {
  type: AGUIEventType.TOOL_CALL_START;
  toolCallId: string;
  toolName: string;
}

export interface ToolCallArgsEvent extends AGUIEvent {
  type: AGUIEventType.TOOL_CALL_ARGS;
  toolCallId: string;
  delta: string;
}

export interface ToolCallEndEvent extends AGUIEvent {
  type: AGUIEventType.TOOL_CALL_END;
  toolCallId: string;
  result?: unknown;
}

// State Events
export interface StateSnapshotEvent extends AGUIEvent {
  type: AGUIEventType.STATE_SNAPSHOT;
  snapshot: Record<string, unknown>;
}

export interface StateDeltaEvent extends AGUIEvent {
  type: AGUIEventType.STATE_DELTA;
  delta: Array<{
    op: 'add' | 'remove' | 'replace';
    path: string;
    value?: unknown;
  }>;
}

// Custom Event
export interface CustomEvent extends AGUIEvent {
  type: AGUIEventType.CUSTOM;
  name: string;
  value: unknown;
}

// Union type for all events
export type AGUIEventUnion =
  | RunStartedEvent
  | RunFinishedEvent
  | RunErrorEvent
  | TextMessageStartEvent
  | TextMessageContentEvent
  | TextMessageEndEvent
  | ToolCallStartEvent
  | ToolCallArgsEvent
  | ToolCallEndEvent
  | StateSnapshotEvent
  | StateDeltaEvent
  | CustomEvent;

// AG-UI Message Types
export interface AGUIMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  createdAt: Date;
  metadata?: {
    toolCalls?: AGUIToolCall[];
    isStreaming?: boolean;
  };
}

export interface AGUIToolCall {
  id: string;
  name: string;
  arguments: Record<string, unknown>;
  result?: unknown;
  status: 'pending' | 'running' | 'completed' | 'error';
}

// AG-UI Action Definition
export interface AGUIAction<T = unknown> {
  name: string;
  description: string;
  parameters: AGUIActionParameter[];
  handler: (args: T) => Promise<unknown>;
}

export interface AGUIActionParameter {
  name: string;
  type: 'string' | 'number' | 'boolean' | 'object' | 'array';
  description: string;
  required?: boolean;
  enum?: string[];
}

// AG-UI Readable State
export interface AGUIReadable<T = unknown> {
  name: string;
  description: string;
  value: T;
}

// AG-UI Context
export interface AGUIContext {
  runId: string | null;
  isRunning: boolean;
  messages: AGUIMessage[];
  actions: AGUIAction[];
  readables: AGUIReadable[];
  state: Record<string, unknown>;
}
