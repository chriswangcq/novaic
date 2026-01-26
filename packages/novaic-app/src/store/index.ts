import { create } from 'zustand';
import { invoke } from '@tauri-apps/api/core';
import { listen } from '@tauri-apps/api/event';
import { 
  AgentEventType, 
  LogData, 
  Message, 
  LogEntry, 
  AppState, 
  AgentEvent
} from '../types';

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

export const useAppStore = create<AppStore>((set, get) => ({
  // Initial state
  messages: [],
  logs: [],
  isExecuting: false,
  isInitialized: false,
  vncConnected: false,
  vncInteractive: false,
  user: null,

  // Initialize app
  initialize: async () => {
    const maxRetries = 5;
    const retryDelay = 2000;
    
    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        console.log(`[Store] Initializing agent (attempt ${attempt}/${maxRetries})...`);
        await invoke('init_agent_with_app_config');
        set({ isInitialized: true });
        console.log('[Store] Agent initialized successfully');
        return;
      } catch (error) {
        console.error(`[Store] Init attempt ${attempt} failed:`, error);
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
      
      // 开始流式请求
      await invoke('send_message_stream', { message: content });
      
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
}));
