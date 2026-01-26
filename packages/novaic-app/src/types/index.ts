/**
 * NB-CC Type Definitions
 */

// User
export interface User {
  id: string;
  email: string;
  name?: string;
  plan: 'free' | 'pro' | 'pro_cloud';
}

// Agent Event Types - 扩展更多类型
export type AgentEventType = 
  | 'text' 
  | 'thinking'  // 思考过程
  | 'tool_start' 
  | 'tool_end' 
  | 'status' 
  | 'warning'
  | 'final' 
  | 'error';

export interface AgentEvent {
  type: AgentEventType;
  timestamp?: string;
  data: any;
}

// Tool Call - 更详细的结构
export interface ToolCallEvent {
  id: string;
  tool: string;
  input: Record<string, any>;
  status: 'pending' | 'running' | 'success' | 'error';
  startTime?: number;
  endTime?: number;
  result?: {
    success: boolean;
    output?: {
      stdout?: string;
      stderr?: string;
      return_code?: number;
      exit_code?: number;
      content?: string;
      path?: string;
      screenshot?: string;  // base64
      [key: string]: any;
    };
    observation?: Record<string, any>;
    error?: string;
    duration_ms?: number;
  };
}

// Message Block - 消息内的渲染块
export type MessageBlockType = 'text' | 'thinking' | 'tool' | 'code' | 'error' | 'warning';

export interface MessageBlock {
  id: string;
  type: MessageBlockType;
  content?: string;
  toolCall?: ToolCallEvent;
  language?: string;  // for code blocks
  isCollapsed?: boolean;
}

// Chat Message - 支持分块渲染
export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  attachments?: Attachment[];
  // Agent workflow
  events?: AgentEvent[];
  toolCalls?: ToolCallEvent[];
  blocks?: MessageBlock[];  // 渲染块
  isStreaming?: boolean;
  streamingText?: string;  // 当前正在流式输出的文本
  thinkingText?: string;   // 思考过程文本
}

// File Attachment
export interface Attachment {
  id: string;
  name: string;
  path: string;
  size: number;
  type: string;
}

// Log Entry for execution logs
export interface LogEntry {
  type: 'tool_start' | 'tool_end' | 'status' | 'stdout' | 'stderr' | 'progress' | 'text' | 'thinking' | 'final' | 'error' | 'warning';
  timestamp: string;
  data: LogData;
}

export type LogData = {
  tool?: string;
  input?: Record<string, unknown>;
  result?: Record<string, unknown>;
  message?: string;
  output?: string;
  progress?: number;
  error?: string;
  content?: string;
};

// Tool Information
export interface ToolInfo {
  name: string;
  description: string;
  input_schema: Record<string, unknown>;
}

// Layout Mode
export type LayoutMode = 'full' | 'normal' | 'mini';

// Layout Settings (persisted)
export interface LayoutSettings {
  mode: LayoutMode;
  leftWidth: number;
}

// App State
export interface AppState {
  messages: Message[];
  logs: LogEntry[];
  isExecuting: boolean;
  isInitialized: boolean;
  vncConnected: boolean;
  vncInteractive: boolean;
  vncLocked: boolean;  // View-only mode for VNC
  settingsOpen: boolean;
  user: User | null;
  // Layout
  layoutMode: LayoutMode;
  leftPanelWidth: number;
}

// API Response Types
export interface ChatResponse {
  results: Array<{
    type: string;
    data: unknown;
  }>;
}

export interface InitResponse {
  status: string;
  message: string;
}

export interface HealthResponse {
  status: string;
  agent_initialized: boolean;
  version: string;
}
