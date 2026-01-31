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
  timestamp: string;
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
    // Screenshot can be at top level or nested
    screenshot?: string;  // base64
    // Browser/HTML related
    html?: string;
    expandable?: string[];
    state_id?: string;
    url?: string;
    title?: string;
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
    [key: string]: any;
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

// Message status for tracking delivery and read state
export type MessageStatus = 'sending' | 'delivered' | 'read' | 'error';

// Chat Message - 支持分块渲染
export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  isTruncated?: boolean;  // 消息是否被截断（历史消息摘要）
  attachments?: Attachment[];
  // Message status (for user messages)
  status?: MessageStatus;
  // Agent workflow
  events?: AgentEvent[];
  toolCalls?: ToolCallEvent[];
  blocks?: MessageBlock[];  // 渲染块
  isStreaming?: boolean;
  streamingText?: string;  // 当前正在流式输出的文本
  thinkingText?: string;   // 思考过程文本
}

// Chat SSE Message types (from backend)
export type ChatMessageType = 
  | 'USER_MESSAGE'
  | 'SYSTEM_MESSAGE'  // System-generated messages (bootstrap, scheduled tasks, etc.)
  | 'AGENT_REPLY' 
  | 'AGENT_ASK'
  | 'AGENT_NOTIFY'
  | 'AGENT_IMAGE'
  | 'STATUS_UPDATE';

export interface ChatSSEMessage {
  id: string;
  type: ChatMessageType;
  timestamp: string;
  // Agent ID for filtering messages
  agent_id?: string;
  // For USER_MESSAGE and AGENT_REPLY
  content?: string;
  message?: string;
  // For AGENT_ASK
  question?: string;
  options?: Array<{ id: string; label: string }>;
  request_id?: string;
  // For AGENT_NOTIFY
  level?: 'info' | 'success' | 'warning' | 'error';
  // For AGENT_IMAGE
  image_url?: string;
  caption?: string;
  // For STATUS_UPDATE
  message_id?: string;
  status?: MessageStatus;
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
  success?: boolean;
  message?: string;
  output?: string;
  progress?: number;
  error?: string;
  content?: string;
  [key: string]: unknown;  // Allow additional properties
};

// Tool Information
export interface ToolInfo {
  name: string;
  description: string;
  input_schema: Record<string, unknown>;
}

// Layout Mode
export type LayoutMode = 'full' | 'normal' | 'mini';

// Chat Mode
export type ChatMode = 'agent' | 'chat';

// Provider Type
export type ProviderType = 'openai' | 'anthropic' | 'google' | 'azure' | 'openai_compatible';

// Available Model
export interface AvailableModel {
  id: string;
  name: string;
  provider: ProviderType;
  api_key_id: string;
  enabled: boolean;
  is_custom?: boolean;  // Whether this is a custom model (manually added)
}

// API Key Info (public, for display)
export interface ApiKeyInfo {
  id: string;
  name: string;
  provider: ProviderType;
}

// Layout Settings (persisted)
export interface LayoutSettings {
  mode: LayoutMode;
  leftWidth: number;
}

// AIC Agent Types - Port Configuration
// Matches Python PortConfig in novaic-gateway/config/agents.py
export interface PortConfig {
  // MCP服务端口
  vm: number;           // VM内MCP (vmuse)
  session: number;      // 会话管理MCP
  local: number;        // 本地文件MCP
  memory: number;       // 记忆管理MCP
  chat: number;         // 用户通信MCP
  qemudebug: number;    // QEMU调试MCP
  // VM连接端口
  vnc: number;          // VNC服务
  websocket: number;    // noVNC WebSocket
  ssh: number;          // SSH转发
}

export interface VmConfig {
  backend: string;
  image_path: string;
  os_type: string;
  os_version: string;
  memory: string;
  cpus: number;
  ports: PortConfig;
  // VM内部端口 (固定)
  mcp_vm_port: number;   // VM内部MCP端口 (固定 8080)
  vnc_vm_port: number;   // VM内部VNC端口 (固定 5900)
  ws_vm_port: number;    // VM内部WebSocket端口 (固定 6080)
  agent_index: number;   // Agent索引，用于端口分配
}

// UI display status (derived from setup_complete + VM status)
export type AgentDisplayStatus = 
  | 'needs_setup'    // setup_complete=false, needs setup
  | 'setting_up'     // setup in progress (has setup_progress)
  | 'stopped'        // VM not running
  | 'starting'       // VM starting
  | 'running'        // VM running
  | 'stopping'       // VM stopping
  | 'error';         // Error state

// Setup progress info (for UI display during setup, not persisted)
export interface SetupProgressInfo {
  stage: string;
  progress: number;
  message: string;
  error?: string;
}

export interface AICAgent {
  id: string;
  name: string;
  created_at: string;
  vm: VmConfig;
  setup_complete: boolean;
  // Setup progress (only in memory, for UI display)
  setup_progress?: SetupProgressInfo;
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
  // Model selection
  availableModels: AvailableModel[];
  apiKeys: ApiKeyInfo[];
  selectedModel: string;
  chatMode: ChatMode;
  // AIC Agents
  agents: AICAgent[];
  currentAgentId: string | null;
  createAgentModalOpen: boolean;
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
