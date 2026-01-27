import { create } from 'zustand';
import { invoke } from '@tauri-apps/api/core';
import { listen } from '@tauri-apps/api/event';
import { 
  AgentEventType, 
  LogData, 
  Message, 
  LogEntry, 
  AppState, 
  AgentEvent,
  LayoutMode,
  LayoutSettings,
  AvailableModel,
  ApiKeyInfo,
  ChatMode
} from '../types';

// Layout persistence key
const LAYOUT_STORAGE_KEY = 'novaic-layout';
const DEFAULT_LEFT_WIDTH = 400;

// Load layout settings from localStorage
function loadLayoutSettings(): LayoutSettings {
  try {
    const saved = localStorage.getItem(LAYOUT_STORAGE_KEY);
    if (saved) {
      const parsed = JSON.parse(saved) as Partial<LayoutSettings>;
      return {
        mode: parsed.mode || 'normal',
        leftWidth: parsed.leftWidth || DEFAULT_LEFT_WIDTH,
      };
    }
  } catch (e) {
    console.warn('[Store] Failed to load layout settings:', e);
  }
  return { mode: 'normal', leftWidth: DEFAULT_LEFT_WIDTH };
}

// Save layout settings to localStorage
function saveLayoutSettings(settings: LayoutSettings): void {
  try {
    localStorage.setItem(LAYOUT_STORAGE_KEY, JSON.stringify(settings));
  } catch (e) {
    console.warn('[Store] Failed to save layout settings:', e);
  }
}

interface AppStore extends AppState {
  initialize: () => Promise<void>;
  sendMessage: (content: string) => Promise<void>;
  stopExecution: () => void;
  addMessage: (message: Message) => void;
  updateMessage: (id: string, updates: Partial<Message>) => void;
  addLog: (log: LogEntry) => void;
  clearLogs: () => void;
  clearMessages: () => void;
  setExecuting: (executing: boolean) => void;
  setVncConnected: (connected: boolean) => void;
  setVncInteractive: (interactive: boolean) => void;
  setVncLocked: (locked: boolean) => void;
  setSettingsOpen: (open: boolean) => void;
  // Layout actions
  setLayoutMode: (mode: LayoutMode) => void;
  setLeftPanelWidth: (width: number) => void;
  // Model & Mode actions
  setAvailableModels: (models: AvailableModel[]) => void;
  setSelectedModel: (model: string) => void;
  setChatMode: (mode: ChatMode) => void;
  loadModelsFromConfig: () => Promise<void>;
}

// SSE event from Agent API
interface SSEEvent {
  type: string;
  data: unknown;
  timestamp?: string;
}

// 转换事件类型
function toAgentEventType(t: string): AgentEventType {
  const validTypes: AgentEventType[] = [
    'text', 'thinking', 'tool_start', 'tool_end', 
    'status', 'warning', 'final', 'error'
  ];
  return validTypes.includes(t as AgentEventType) ? (t as AgentEventType) : 'status';
}

function toLogData(d: unknown): LogData {
  if (d && typeof d === 'object') return d as LogData;
  return { content: String(d) };
}

// Load initial layout
const initialLayout = loadLayoutSettings();

// Model selection persistence
const MODEL_STORAGE_KEY = 'novaic-selected-model';
const MODE_STORAGE_KEY = 'novaic-chat-mode';

function loadSelectedModel(): string {
  try {
    return localStorage.getItem(MODEL_STORAGE_KEY) || '';
  } catch {
    return '';
  }
}

function loadChatMode(): ChatMode {
  try {
    const saved = localStorage.getItem(MODE_STORAGE_KEY);
    if (saved === 'agent' || saved === 'chat') return saved;
  } catch {}
  return 'agent';
}

export const useAppStore = create<AppStore>((set, get) => ({
  // Initial state
  messages: [],
  logs: [],
  isExecuting: false,
  isInitialized: false,
  vncConnected: false,
  vncInteractive: false,
  vncLocked: false,
  settingsOpen: false,
  user: null,
  // Layout state (loaded from localStorage)
  layoutMode: initialLayout.mode,
  leftPanelWidth: initialLayout.leftWidth,
  // Model selection state
  availableModels: [],
  apiKeys: [],
  selectedModel: loadSelectedModel(),
  chatMode: loadChatMode(),

  // Initialize app
  initialize: async () => {
    const { loadModelsFromConfig } = get();
    const maxRetries = 5;
    const retryDelay = 2000;
    
    // Load available models from config first
    await loadModelsFromConfig();
    
    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        console.log(`[Store] Initializing agent (attempt ${attempt}/${maxRetries})...`);
        await invoke('init_agent_with_app_config');
        set({ isInitialized: true });
        console.log('[Store] Agent initialized successfully');
        return;
      } catch (error) {
        const errorStr = String(error);
        console.error(`[Store] Init attempt ${attempt} failed:`, error);
        
        // If no API key configured, open settings and stop retrying
        if (errorStr.includes('No API key') || errorStr.includes('not configured')) {
          console.log('[Store] No API key configured, opening settings...');
          set({ settingsOpen: true });
          return;
        }
        
        if (attempt < maxRetries) {
          await new Promise(resolve => setTimeout(resolve, retryDelay));
        }
      }
    }
    console.error('[Store] Failed to initialize after all retries');
  },

  // Send message - 简化版，核心是按顺序累积 events
  sendMessage: async (content: string) => {
    const { addMessage, updateMessage, addLog, setExecuting, isInitialized, initialize } = get();
    
    if (!isInitialized) {
      await initialize();
      // Check again after initialize attempt
      if (!get().isInitialized) {
        // Still not initialized, settings should be open
        console.log('[Store] Agent not initialized, cannot send message');
        return;
      }
    }
    
    // Add user message
    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: 'user',
      content,
      timestamp: new Date(),
    };
    addMessage(userMessage);
    
    // Create assistant message
    const assistantId = `assistant-${Date.now()}`;
    addMessage({
      id: assistantId,
      role: 'assistant',
      content: '',
      timestamp: new Date(),
      events: [],
      isStreaming: true,
    });
    
    set({ logs: [] });
    setExecuting(true);
    
    // 核心：按顺序累积所有事件
    let events: AgentEvent[] = [];
    let finalContent = '';
    let unlistenEvent: (() => void) | null = null;
    
    try {
      unlistenEvent = await listen<SSEEvent>('chat-event', (event) => {
        const sseEvent = event.payload;
        const ts = sseEvent.timestamp || new Date().toISOString();
        const eventType = toAgentEventType(sseEvent.type);
        
        // 创建事件对象
        const agentEvent: AgentEvent = {
          type: eventType,
          data: sseEvent.data,
          timestamp: ts,
        };
        
        // 添加到事件列表（保持顺序！）
        events = [...events, agentEvent];
        
        // 添加到日志
        addLog({
          type: eventType,
          timestamp: ts,
          data: toLogData(sseEvent.data),
        });
        
        // 提取最终内容
        if (eventType === 'final' || eventType === 'text') {
          const data = sseEvent.data;
          if (typeof data === 'string') {
            finalContent = data;
          } else if (data && typeof data === 'object') {
            finalContent = String((data as Record<string, unknown>).content || 
                                  (data as Record<string, unknown>).data || '');
          }
        }
        
        // 实时更新 - 只更新 events 和 content
        updateMessage(assistantId, {
          content: finalContent,
          events: [...events],
        });
      });
      
      // 开始流式请求 - 传递选中的模型ID和API Key ID
      // selectedModel 格式: {api_key_id}:{model_id}
      // Note: model_id may contain colons, so only split on FIRST colon
      const { selectedModel, chatMode } = get();
      let modelId: string | null = null;
      let apiKeyId: string | null = null;
      if (selectedModel) {
        const colonIndex = selectedModel.indexOf(':');
        if (colonIndex !== -1) {
          apiKeyId = selectedModel.substring(0, colonIndex);
          modelId = selectedModel.substring(colonIndex + 1);
        }
      }
      await invoke('send_message_stream', { 
        message: content,
        modelId,
        apiKeyId,
        mode: chatMode || 'agent'
      });
      
      // 最终更新
      updateMessage(assistantId, {
        content: finalContent,
        events,
        isStreaming: false,
      });
      
    } catch (error) {
      console.error('Send message error:', error);
      updateMessage(assistantId, {
        content: `Error: ${String(error)}`,
        isStreaming: false,
        events: [...events, {
          type: 'error',
          data: { error: String(error) },
          timestamp: new Date().toISOString(),
        }],
      });
    } finally {
      if (unlistenEvent) unlistenEvent();
      setExecuting(false);
    }
  },

  stopExecution: () => {
    console.log('[Store] Stop execution requested');
    set({ isExecuting: false });
  },

  addMessage: (message: Message) => {
    set((state) => ({ messages: [...state.messages, message] }));
  },

  updateMessage: (id: string, updates: Partial<Message>) => {
    set((state) => ({
      messages: state.messages.map((msg) =>
        msg.id === id ? { ...msg, ...updates } : msg
      ),
    }));
  },

  addLog: (log: LogEntry) => {
    set((state) => ({ logs: [...state.logs, log] }));
  },

  clearLogs: () => {
    set({ logs: [] });
  },

  clearMessages: () => {
    set({ messages: [], logs: [] });
  },

  setExecuting: (executing: boolean) => {
    set({ isExecuting: executing });
  },

  setVncConnected: (connected: boolean) => {
    set({ vncConnected: connected });
  },

  setVncInteractive: (interactive: boolean) => {
    set({ vncInteractive: interactive });
  },

  setVncLocked: (locked: boolean) => {
    set({ vncLocked: locked });
  },

  setSettingsOpen: (open: boolean) => {
    set({ settingsOpen: open });
  },

  // Layout actions
  setLayoutMode: (mode: LayoutMode) => {
    set({ layoutMode: mode });
    const { leftPanelWidth } = get();
    saveLayoutSettings({ mode, leftWidth: leftPanelWidth });
  },

  setLeftPanelWidth: (width: number) => {
    set({ leftPanelWidth: width });
    const { layoutMode } = get();
    saveLayoutSettings({ mode: layoutMode, leftWidth: width });
  },

  // Model & Mode actions
  setAvailableModels: (models: AvailableModel[]) => {
    set({ availableModels: models });
  },

  setSelectedModel: (model: string) => {
    set({ selectedModel: model });
    try {
      localStorage.setItem(MODEL_STORAGE_KEY, model);
    } catch {}
  },

  setChatMode: (mode: ChatMode) => {
    set({ chatMode: mode });
    try {
      localStorage.setItem(MODE_STORAGE_KEY, mode);
    } catch {}
  },

  loadModelsFromConfig: async () => {
    try {
      const config = await invoke<{
        available_models: AvailableModel[];
        api_keys: Array<{ id: string; name: string; provider: string }>;
        default_model: string;
      }>('get_app_config');
      
      // Filter only enabled models
      const enabledModels = (config.available_models || []).filter(m => m.enabled);
      
      // Extract API key info
      const apiKeys: ApiKeyInfo[] = (config.api_keys || []).map(k => ({
        id: k.id,
        name: k.name,
        provider: k.provider as ApiKeyInfo['provider'],
      }));
      
      set({ availableModels: enabledModels, apiKeys });
      
      // Set default model if not already selected
      const { selectedModel } = get();
      if (!selectedModel && config.default_model) {
        set({ selectedModel: config.default_model });
      } else if (!selectedModel && enabledModels.length > 0) {
        set({ selectedModel: enabledModels[0].id });
      }
      
      console.log('[Store] Loaded models:', enabledModels.length, 'apiKeys:', apiKeys.length);
    } catch (error) {
      console.error('[Store] Failed to load models from config:', error);
    }
  },
}));
