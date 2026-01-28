/**
 * NovAIC Web Store
 * 
 * Zustand store that uses Gateway API and WebSocket instead of Tauri invoke.
 */

import { create } from 'zustand';
import { api, gateway } from '../services';
import type { AICAgent, CreateAgentRequest } from '../services/api';
import { 
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
  // Agent actions
  loadAgents: () => Promise<void>;
  selectAgent: (agentId: string) => Promise<void>;
  createAgent: (data: CreateAgentRequest) => Promise<AICAgent>;
  deleteAgent: (agentId: string) => Promise<void>;
  setCreateAgentModalOpen: (open: boolean) => void;
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

// Track current message being streamed
let currentAssistantId: string | null = null;
let currentEvents: AgentEvent[] = [];
let currentFinalContent = '';

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
  // Agent state
  agents: [],
  currentAgentId: null,
  createAgentModalOpen: false,

  // Initialize app - connect to Gateway WebSocket
  initialize: async () => {
    const { loadModelsFromConfig, addLog, updateMessage, setExecuting } = get();
    
    try {
      console.log('[Store] Waiting for Gateway to be ready...');
      
      // Wait for Gateway to be ready (poll health endpoint)
      const maxAttempts = 30;
      const delayMs = 1000;
      let gatewayReady = false;
      
      for (let attempt = 1; attempt <= maxAttempts; attempt++) {
        try {
          const health = await api.getHealth();
          if (health.status === 'healthy') {
            gatewayReady = true;
            console.log('[Store] Gateway is ready');
            break;
          }
        } catch (e) {
          console.log(`[Store] Gateway not ready (attempt ${attempt}/${maxAttempts})`);
        }
        
        if (attempt < maxAttempts) {
          await new Promise(resolve => setTimeout(resolve, delayMs));
        }
      }
      
      if (!gatewayReady) {
        console.error('[Store] Gateway failed to start');
        set({ settingsOpen: true });
        return;
      }
      
      // Connect to WebSocket
      await gateway.connect();
      console.log('[Store] WebSocket connected');
      
      // Set up event listeners
      gateway.on('thinking', (data) => {
        if (currentAssistantId) {
          const event: AgentEvent = {
            type: 'thinking',
            data,
            timestamp: new Date().toISOString(),
          };
          currentEvents = [...currentEvents, event];
          addLog({ type: 'thinking', timestamp: event.timestamp, data: toLogData(data) });
          updateMessage(currentAssistantId, { events: [...currentEvents] });
        }
      });
      
      gateway.on('tool_start', (data) => {
        if (currentAssistantId) {
          const event: AgentEvent = {
            type: 'tool_start',
            data,
            timestamp: new Date().toISOString(),
          };
          currentEvents = [...currentEvents, event];
          addLog({ type: 'tool_start', timestamp: event.timestamp, data: toLogData(data) });
          updateMessage(currentAssistantId, { events: [...currentEvents] });
        }
      });
      
      gateway.on('tool_end', (data) => {
        if (currentAssistantId) {
          const event: AgentEvent = {
            type: 'tool_end',
            data,
            timestamp: new Date().toISOString(),
          };
          currentEvents = [...currentEvents, event];
          addLog({ type: 'tool_end', timestamp: event.timestamp, data: toLogData(data) });
          updateMessage(currentAssistantId, { events: [...currentEvents] });
        }
      });
      
      gateway.on('status', (data) => {
        if (currentAssistantId) {
          const event: AgentEvent = {
            type: 'status',
            data,
            timestamp: new Date().toISOString(),
          };
          currentEvents = [...currentEvents, event];
          addLog({ type: 'status', timestamp: event.timestamp, data: toLogData(data) });
          updateMessage(currentAssistantId, { events: [...currentEvents] });
        }
      });
      
      gateway.on('warning', (data) => {
        if (currentAssistantId) {
          const event: AgentEvent = {
            type: 'warning',
            data,
            timestamp: new Date().toISOString(),
          };
          currentEvents = [...currentEvents, event];
          addLog({ type: 'warning', timestamp: event.timestamp, data: toLogData(data) });
          updateMessage(currentAssistantId, { events: [...currentEvents] });
        }
      });
      
      gateway.on('final', (data) => {
        if (currentAssistantId) {
          // Extract content from data
          if (typeof data === 'string') {
            currentFinalContent = data;
          } else if (data && typeof data === 'object') {
            currentFinalContent = String((data as Record<string, unknown>).content || 
                                        (data as Record<string, unknown>).data || data);
          }
          
          const event: AgentEvent = {
            type: 'final',
            data,
            timestamp: new Date().toISOString(),
          };
          currentEvents = [...currentEvents, event];
          addLog({ type: 'final', timestamp: event.timestamp, data: toLogData(data) });
          
          // Final update
          updateMessage(currentAssistantId, {
            content: currentFinalContent,
            events: [...currentEvents],
            isStreaming: false,
          });
          
          // Reset state
          currentAssistantId = null;
          currentEvents = [];
          currentFinalContent = '';
          setExecuting(false);
        }
      });
      
      gateway.on('error', (data) => {
        if (currentAssistantId) {
          const errorMsg = typeof data === 'string' ? data : 
                          (data as Record<string, unknown>)?.error || 'Unknown error';
          
          const event: AgentEvent = {
            type: 'error',
            data,
            timestamp: new Date().toISOString(),
          };
          currentEvents = [...currentEvents, event];
          addLog({ type: 'error', timestamp: event.timestamp, data: toLogData(data) });
          
          updateMessage(currentAssistantId, {
            content: `Error: ${errorMsg}`,
            events: [...currentEvents],
            isStreaming: false,
          });
          
          currentAssistantId = null;
          currentEvents = [];
          currentFinalContent = '';
          setExecuting(false);
        }
      });
      
      // Load models from config
      await loadModelsFromConfig();
      
      set({ isInitialized: true });
      console.log('[Store] Initialized successfully');
      
    } catch (error) {
      console.error('[Store] Initialization failed:', error);
      // Open settings if connection fails
      set({ settingsOpen: true });
    }
  },

  // Send message via WebSocket
  sendMessage: async (content: string) => {
    const { addMessage, setExecuting, isInitialized, initialize, selectedModel, chatMode } = get();
    
    if (!isInitialized) {
      await initialize();
      if (!get().isInitialized) {
        console.log('[Store] Not initialized, cannot send message');
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
    currentAssistantId = `assistant-${Date.now()}`;
    currentEvents = [];
    currentFinalContent = '';
    
    addMessage({
      id: currentAssistantId,
      role: 'assistant',
      content: '',
      timestamp: new Date(),
      events: [],
      isStreaming: true,
    });
    
    set({ logs: [] });
    setExecuting(true);
    
    // Parse selected model
    let modelId: string | undefined;
    let apiKeyId: string | undefined;
    
    if (selectedModel) {
      const colonIndex = selectedModel.indexOf(':');
      if (colonIndex !== -1) {
        apiKeyId = selectedModel.substring(0, colonIndex);
        modelId = selectedModel.substring(colonIndex + 1);
      } else {
        modelId = selectedModel;
      }
    }
    
    // Send via WebSocket
    gateway.sendChat(content, {
      model: modelId,
      mode: chatMode || 'agent',
      apiKeyId,
    });
  },

  stopExecution: () => {
    console.log('[Store] Stop execution requested');
    gateway.sendInterrupt();
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
    gateway.sendClear();
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
      const config = await api.getConfig();
      
      // Filter only enabled models
      const enabledModels = (config.available_models || []).filter(m => m.enabled);
      
      // Extract API key info
      const apiKeys: ApiKeyInfo[] = (config.api_keys || []).map(k => ({
        id: k.id,
        name: k.name,
        provider: k.provider as ApiKeyInfo['provider'],
      }));
      
      set({ availableModels: enabledModels as AvailableModel[], apiKeys });
      
      // Set default model if not already selected
      const { selectedModel } = get();
      if (!selectedModel && config.default_model) {
        set({ selectedModel: config.default_model });
      } else if (!selectedModel && enabledModels.length > 0) {
        // Use api_key_id:model_id format
        const firstModel = enabledModels[0];
        set({ selectedModel: `${firstModel.api_key_id}:${firstModel.id}` });
      }
      
      console.log('[Store] Loaded models:', enabledModels.length, 'apiKeys:', apiKeys.length);
    } catch (error) {
      console.error('[Store] Failed to load models from config:', error);
    }
  },

  // ==================== Agent Actions ====================

  loadAgents: async () => {
    try {
      const response = await api.listAgents();
      set({ 
        agents: response.agents,
        currentAgentId: response.current_agent_id 
      });
      console.log('[Store] Loaded agents:', response.agents.length);
    } catch (error) {
      console.error('[Store] Failed to load agents:', error);
    }
  },

  selectAgent: async (agentId: string) => {
    try {
      await api.setCurrentAgent(agentId);
      set({ currentAgentId: agentId });
      console.log('[Store] Selected agent:', agentId);
      // Note: VM switch is handled by Tauri, not here
    } catch (error) {
      console.error('[Store] Failed to select agent:', error);
      throw error;
    }
  },

  createAgent: async (data: CreateAgentRequest) => {
    try {
      const agent = await api.createAgent(data);
      const { loadAgents } = get();
      await loadAgents();
      console.log('[Store] Created agent:', agent.id);
      return agent;
    } catch (error) {
      console.error('[Store] Failed to create agent:', error);
      throw error;
    }
  },

  deleteAgent: async (agentId: string) => {
    try {
      await api.deleteAgent(agentId);
      const { loadAgents } = get();
      await loadAgents();
      console.log('[Store] Deleted agent:', agentId);
    } catch (error) {
      console.error('[Store] Failed to delete agent:', error);
      throw error;
    }
  },

  setCreateAgentModalOpen: (open: boolean) => {
    set({ createAgentModalOpen: open });
  },
}));
