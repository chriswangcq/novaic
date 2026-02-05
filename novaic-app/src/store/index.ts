/**
 * NovAIC Web Store
 * 
 * Zustand store with:
 * - Fire-and-forget chat via POST /api/chat/send
 * - SSE for real-time chat messages (/api/chat/messages)
 * - SSE for real-time execution logs (/api/logs/stream)
 */

import { create } from 'zustand';
import { api } from '../services';
import * as setup from '../services/setup';
import type { AICAgent, CreateAgentRequest } from '../services/api';
import { 
  Message, 
  LogEntry, 
  AppState, 
  LayoutMode,
  LayoutSettings,
  AvailableModel,
  ApiKeyInfo,
  ChatMode,
  ChatSSEMessage,
  MessageStatus,
  SetupProgressInfo,
} from '../types';

// Layout persistence key
const LAYOUT_STORAGE_KEY = 'novaic-layout';
const DEFAULT_LEFT_WIDTH = 400;

// Agent persistence key
const AGENT_STORAGE_KEY = 'novaic-current-agent-id';

function loadStoredAgentId(): string | null {
  try {
    return localStorage.getItem(AGENT_STORAGE_KEY);
  } catch {
    return null;
  }
}

function saveAgentId(agentId: string | null): void {
  try {
    if (agentId) {
      localStorage.setItem(AGENT_STORAGE_KEY, agentId);
    } else {
      localStorage.removeItem(AGENT_STORAGE_KEY);
    }
  } catch {}
}

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
  updateMessageStatus: (messageId: string, status: MessageStatus) => void;
  expandMessage: (messageId: string) => Promise<void>;
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
  setSelectedModel: (model: string) => Promise<void>;
  setChatMode: (mode: ChatMode) => void;
  loadModelsFromConfig: () => Promise<void>;
  // Agent actions
  loadAgents: () => Promise<void>;
  selectAgent: (agentId: string) => Promise<void>;
  createAgent: (data: CreateAgentRequest) => Promise<AICAgent>;
  deleteAgent: (agentId: string) => Promise<void>;
  setCreateAgentModalOpen: (open: boolean) => void;
  // Setup actions
  updateSetupProgress: (agentId: string, progress: SetupProgressInfo | undefined) => void;
  setAgentSetupComplete: (agentId: string, complete: boolean) => void;
  setupAgent: (agentId: string, config: {
    sourceImage: string;
    useCnMirrors: boolean;
  }) => Promise<void>;
  // SSE connection
  connectChatSSE: (agentId?: string) => void;
  connectLogsSSE: (agentId?: string) => void;
  disconnectSSE: () => void;
  // Message pagination
  hasMoreMessages: boolean;
  isLoadingMore: boolean;
  loadMoreMessages: () => Promise<void>;
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

// SSE connections (module level to persist across re-renders)
let chatEventSource: EventSource | null = null;
let logsEventSource: EventSource | null = null;

// Gateway base URL
const GATEWAY_URL = 'http://127.0.0.1:19999';

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
  currentAgentId: loadStoredAgentId(),  // Initialize from localStorage
  createAgentModalOpen: false,
  // Message pagination state
  hasMoreMessages: true,
  isLoadingMore: false,

  // Initialize app - connect to SSE streams
  initialize: async () => {
    const { loadModelsFromConfig, connectChatSSE, connectLogsSSE } = get();
    
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
      
      // Try to connect SSE streams (will only connect if currentAgentId is set)
      // If no agent is selected yet, SSE will be connected when selectAgent() is called
      connectChatSSE();
      connectLogsSSE();
      console.log('[Store] SSE connection attempted (requires agent selection)');
      
      // Load chat history (persisted messages with summary)
      // Note: At initialization, currentAgentId may not be set yet (will be loaded by loadAgents)
      // So we skip loading history here - it will be loaded when selectAgent is called
      const { currentAgentId } = get();
      if (currentAgentId) {
        try {
          const history = await api.getChatHistory({ agent_id: currentAgentId, limit: 50, summary_length: 100 });
          if (history.success && history.messages.length > 0) {
            const messages: Message[] = history.messages.map((msg) => ({
              id: msg.id,
              role: msg.type === 'USER_MESSAGE' ? 'user' : 'assistant',
              content: msg.summary || '',
              timestamp: new Date(msg.timestamp),
              isTruncated: msg.is_truncated,  // 保存截断状态
              // Use backend read status: read=true -> 'read', read=false -> 'delivered'
              status: msg.type === 'USER_MESSAGE' 
                ? (msg.read ? 'read' : 'delivered') as MessageStatus 
                : undefined,
            }));
            set({ messages, hasMoreMessages: history.has_more });
            console.log(`[Store] Loaded ${messages.length} messages from history, has_more: ${history.has_more}`);
          }
        } catch (e) {
          console.warn('[Store] Failed to load chat history:', e);
        }
      } else {
        console.log('[Store] No agent selected yet, skipping history load');
      }
      
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

  // Send message (fire-and-forget style, like WeChat/WhatsApp)
  sendMessage: async (content: string) => {
    const { addMessage, updateMessageStatus, isInitialized, initialize, selectedModel, chatMode, currentAgentId } = get();
    
    if (!isInitialized) {
      await initialize();
      if (!get().isInitialized) {
        console.log('[Store] Not initialized, cannot send message');
        return;
      }
    }
    
    // Check if agent is selected
    if (!currentAgentId) {
      console.error('[Store] No agent selected, cannot send message');
      return;
    }
    
    // Generate message ID locally
    const messageId = `user-${Date.now()}`;
    
    // Add user message immediately with 'sending' status
    const userMessage: Message = {
      id: messageId,
      role: 'user',
      content,
      timestamp: new Date(),
      status: 'sending',
    };
    addMessage(userMessage);
    
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
    
    // Send via API with timeout (fire-and-forget)
    const sendTimeout = 30000; // 30s timeout
    try {
      const timeoutPromise = new Promise<never>((_, reject) => 
        setTimeout(() => reject(new Error('Send timeout')), sendTimeout)
      );
      
      const result = await Promise.race([
        api.sendChatMessage(content, {
          agent_id: currentAgentId,
          model: modelId,
          mode: chatMode || 'agent',
          api_key_id: apiKeyId,
        }),
        timeoutPromise,
      ]);
      
      if (result.success) {
        // Update local message ID to match server's and set status to 'delivered'
        set((state) => ({
          messages: state.messages.map((msg) =>
            msg.id === messageId 
              ? { ...msg, id: result.message_id, status: 'delivered' as MessageStatus }
              : msg
          ),
        }));
        console.log('[Store] Message sent, id:', result.message_id);
      } else {
        // Update status to error
        updateMessageStatus(messageId, 'error');
        console.error('[Store] Failed to send message');
      }
    } catch (error) {
      console.error('[Store] Error sending message:', error);
      updateMessageStatus(messageId, 'error');
    }
    // Note: Agent response will come via SSE (connectChatSSE)
  },

  stopExecution: async () => {
    const { currentAgentId } = get();
    console.log('[Store] Stop execution requested for agent:', currentAgentId);
    try {
      await api.interruptAgent(currentAgentId || undefined);
      console.log('[Store] Agent interrupted via HTTP API');
    } catch (e) {
      console.error('[Store] Failed to interrupt agent:', e);
    }
    set({ isExecuting: false });
  },

  addMessage: (message: Message) => {
    set((state) => {
      // Check if message already exists (prevent duplicates from SSE)
      const exists = state.messages.some(m => m.id === message.id);
      if (exists) {
        console.log('[Store] Message already exists, skipping:', message.id);
        return state;
      }
      return { messages: [...state.messages, message] };
    });
  },

  updateMessage: (id: string, updates: Partial<Message>) => {
    set((state) => ({
      messages: state.messages.map((msg) =>
        msg.id === id ? { ...msg, ...updates } : msg
      ),
    }));
  },

  updateMessageStatus: (messageId: string, status: MessageStatus) => {
    set((state) => ({
      messages: state.messages.map((msg) =>
        msg.id === messageId ? { ...msg, status } : msg
      ),
    }));
  },

  // Expand truncated message - fetch full content
  expandMessage: async (messageId: string) => {
    const { currentAgentId } = get();
    try {
      const result = await api.getChatMessage(messageId, currentAgentId || undefined);
      if (result.success && result.content) {
        set((state) => ({
          messages: state.messages.map((msg) =>
            msg.id === messageId
              ? { ...msg, content: result.content!, isTruncated: false }
              : msg
          ),
        }));
        console.log('[Store] Expanded message:', messageId);
      } else {
        console.error('[Store] Failed to expand message:', result.error);
      }
    } catch (e) {
      console.error('[Store] Error expanding message:', e);
    }
  },

  addLog: (log: LogEntry) => {
    set((state) => ({ logs: [...state.logs, log] }));
  },

  clearLogs: () => {
    set({ logs: [] });
  },

  clearMessages: () => {
    // Only clear local state (no server-side clear needed)
    set({ messages: [], logs: [], hasMoreMessages: true });
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

  setSelectedModel: async (model: string) => {
    const { currentAgentId } = get();
    set({ selectedModel: model });
    
    // 保存到 localStorage（作为 fallback）
    try {
      localStorage.setItem(MODEL_STORAGE_KEY, model);
    } catch {}
    
    // 同步保存到当前 agent（如果有）
    if (currentAgentId && model) {
      try {
        // model 格式: "api_key_id:model_id"，后端只需要 model_id
        const colonIndex = model.indexOf(':');
        const modelId = colonIndex !== -1 ? model.substring(colonIndex + 1) : model;
        await api.setAgentModel(currentAgentId, modelId);
        console.log('[Store] Saved model to agent:', currentAgentId, modelId);
      } catch (error) {
        console.warn('[Store] Failed to save model to agent:', error);
      }
    }
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
      
      // Filter only enabled models from candidate_models
      const enabledModels = (config.candidate_models || []).filter(m => m.enabled);
      
      // Extract API key info
      const apiKeys: ApiKeyInfo[] = (config.api_keys || []).map(k => ({
        id: k.id,
        name: k.name,
        provider: k.provider as ApiKeyInfo['provider'],
      }));
      
      set({ availableModels: enabledModels as AvailableModel[], apiKeys });
      
      // Auto-select first enabled model if not already selected
      const { selectedModel } = get();
      if (!selectedModel && enabledModels.length > 0) {
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
      const { currentAgentId, selectAgent, isInitialized } = get();
      
      // 更新 agents 列表
      set({ agents: response.agents });
      console.log('[Store] Loaded agents:', response.agents.length);
      
      // 自动选择 agent（如果当前没有选择或选择的 agent 不存在）
      if (response.agents.length > 0) {
        const currentAgentExists = response.agents.some(a => a.id === currentAgentId);
        
        if (!currentAgentId || !currentAgentExists) {
          // 优先使用 localStorage 中保存的，否则选择第一个
          const storedAgentId = loadStoredAgentId();
          const storedAgentExists = storedAgentId && response.agents.some(a => a.id === storedAgentId);
          
          const targetAgentId = storedAgentExists ? storedAgentId! : response.agents[0].id;
          console.log('[Store] Auto-selecting agent:', targetAgentId);
          
          // 如果已初始化，调用完整的 selectAgent 以清空消息并加载新历史
          if (isInitialized) {
            // 使用 selectAgent 确保消息被清空、历史被加载
            await selectAgent(targetAgentId);
          } else {
            // 初始化前只设置 ID（SSE 和历史会在 initialize 时处理）
            set({ currentAgentId: targetAgentId });
            saveAgentId(targetAgentId);
          }
        }
      }
    } catch (error) {
      console.error('[Store] Failed to load agents:', error);
    }
  },

  selectAgent: async (agentId: string) => {
    const { currentAgentId, connectChatSSE, connectLogsSSE } = get();
    
    // 如果是同一个 agent，不需要切换
    if (currentAgentId === agentId) {
      console.log('[Store] Agent already selected:', agentId);
      return;
    }
    
    try {
      // 1. 更新本地状态并持久化到 localStorage
      set({ 
        currentAgentId: agentId,
        messages: [],
        logs: [],
        hasMoreMessages: true,
      });
      saveAgentId(agentId);  // Persist to localStorage
      console.log('[Store] Selected agent:', agentId);
      
      // 2. 重新连接 SSE（带 agent_id 参数，后端按 agent 过滤）
      connectChatSSE(agentId);
      connectLogsSSE(agentId);
      
      // 3. 加载新 agent 的模型配置
      try {
        const modelConfig = await api.getAgentModel(agentId);
        if (modelConfig && modelConfig.model_id && modelConfig.model) {
          // 构造 composite ID: api_key_id:model_id
          const compositeId = `${modelConfig.model.api_key_id}:${modelConfig.model_id}`;
          set({ selectedModel: compositeId });
          localStorage.setItem(MODEL_STORAGE_KEY, compositeId);
          console.log('[Store] Loaded model for agent:', agentId, compositeId);
        }
      } catch (e) {
        console.warn('[Store] Failed to load model for agent:', e);
      }
      
      // 4. 加载新 agent 的聊天历史
      try {
        const history = await api.getChatHistory({ agent_id: agentId, limit: 50, summary_length: 100 });
        if (history.success && history.messages.length > 0) {
          const messages: Message[] = history.messages.map((msg) => ({
            id: msg.id,
            role: msg.type === 'USER_MESSAGE' ? 'user' : 'assistant',
            content: msg.summary || '',
            timestamp: new Date(msg.timestamp),
            isTruncated: msg.is_truncated,
            // Use backend read status: read=true -> 'read', read=false -> 'delivered'
            status: msg.type === 'USER_MESSAGE' 
              ? (msg.read ? 'read' : 'delivered') as MessageStatus 
              : undefined,
          }));
          set({ messages, hasMoreMessages: history.has_more });
          console.log(`[Store] Loaded ${messages.length} messages for agent ${agentId}, has_more: ${history.has_more}`);
        }
      } catch (e) {
        console.warn('[Store] Failed to load chat history for new agent:', e);
      }
      
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
      console.log('[Store] Deleted agent:', agentId);
      
      // loadAgents 会检测到当前 agent 不存在，自动选择新 agent
      // 新的 loadAgents 会调用 selectAgent，包含清空消息、连接 SSE、加载历史
      const { loadAgents } = get();
      await loadAgents();
    } catch (error) {
      console.error('[Store] Failed to delete agent:', error);
      throw error;
    }
  },

  setCreateAgentModalOpen: (open: boolean) => {
    set({ createAgentModalOpen: open });
  },

  // Update setup progress (local state only, for UI)
  updateSetupProgress: (agentId: string, progress: SetupProgressInfo | undefined) => {
    set((state) => ({
      agents: state.agents.map((agent) =>
        agent.id === agentId
          ? { ...agent, setup_progress: progress }
          : agent
      ),
    }));
  },

  // Set agent setup complete (local state)
  setAgentSetupComplete: (agentId: string, complete: boolean) => {
    set((state) => ({
      agents: state.agents.map((agent) =>
        agent.id === agentId
          ? { ...agent, setup_complete: complete, setup_progress: undefined }
          : agent
      ),
    }));
  },

  // Setup agent - full setup flow (download, create VM, deploy)
  setupAgent: async (agentId: string, config: {
    sourceImage: string;
    useCnMirrors: boolean;
  }) => {
    const { updateSetupProgress, setAgentSetupComplete, agents } = get();
    const agent = agents.find(a => a.id === agentId);
    if (!agent) throw new Error('Agent not found');

    try {
      // Step 1: Get or generate SSH key
      let sshPubkey = await setup.getSshPubkey();
      if (!sshPubkey) {
        sshPubkey = await setup.generateSshKey();
      }

      // Step 2: Create VM disk and cloud-init
      updateSetupProgress(agentId, {
        stage: 'Creating VM',
        progress: 0,
        message: 'Creating virtual machine disk...',
      });

      await setup.setupVm(
        {
          agentId,
          sourceImage: config.sourceImage,
          diskSize: '40G',
          sshPubkey,
          useCnMirrors: config.useCnMirrors,
        },
        (progress) => {
          updateSetupProgress(agentId, progress);
        }
      );

      // Step 3: Start VM
      updateSetupProgress(agentId, {
        stage: 'Starting VM',
        progress: 90,
        message: 'Starting virtual machine...',
      });

      // 使用 vmService 启动 VM（通过 Gateway API）
      const { vmService } = await import('../services/vm');
      const agentIndex = agent.vm.agent_index ?? 0;
      await vmService.start(agentId, agentIndex);

      // Wait for VM to boot
      await new Promise(resolve => setTimeout(resolve, 3000));

      // Reload agents to get updated port info
      const { loadAgents } = get();
      await loadAgents();
      
      // Get updated agent with correct ports
      const updatedAgents = get().agents;
      const updatedAgent = updatedAgents.find(a => a.id === agentId);
      if (!updatedAgent) throw new Error('Agent not found after VM start');

      // Step 4: Mark setup as complete
      await api.updateAgent(agentId, { setup_complete: true });
      
      // Update local state
      setAgentSetupComplete(agentId, true);
      console.log('[Store] VM setup complete:', agentId);

    } catch (error) {
      console.error('[Store] Agent setup failed:', error);
      updateSetupProgress(agentId, {
        stage: 'Error',
        progress: 0,
        message: error instanceof Error ? error.message : String(error),
        error: error instanceof Error ? error.message : String(error),
      });
      throw error;
    }
  },

  // SSE Connection: Chat messages (Agent <-> User)
  connectChatSSE: (agentId?: string) => {
    const { addMessage, updateMessageStatus, setExecuting, currentAgentId } = get();
    
    // Use provided agentId or fallback to currentAgentId
    const targetAgentId = agentId || currentAgentId;
    
    // Don't connect if no agent selected
    if (!targetAgentId) {
      console.log('[Store] No agent selected, skipping Chat SSE connection');
      return;
    }
    
    // Close existing connection
    if (chatEventSource) {
      chatEventSource.close();
    }
    
    const sseUrl = `${GATEWAY_URL}/api/chat/messages?agent_id=${targetAgentId}`;
    console.log('[Store] Connecting to Chat SSE:', sseUrl);
    chatEventSource = new EventSource(sseUrl);
    
    chatEventSource.onmessage = (event) => {
      try {
        const msg: ChatSSEMessage = JSON.parse(event.data);
        console.log('[Store] Chat SSE message:', msg.type, msg.id, 'agent_id:', msg.agent_id);
        
        // Note: Backend already filters by agent_id, no client-side filtering needed
        
        switch (msg.type) {
          case 'USER_MESSAGE':
            // User message echoed back (skip if we already added it locally)
            // The message from server has the authoritative ID
            break;
            
          case 'SYSTEM_MESSAGE':
            // System-generated message (bootstrap, scheduled tasks, etc.)
            // Display as a special "system" message - using assistant role with system indicator
            addMessage({
              id: msg.id,
              role: 'assistant',
              content: `🔧 **System:** ${msg.message || msg.content || ''}`,
              timestamp: new Date(msg.timestamp),
              events: [{
                type: 'status',
                timestamp: msg.timestamp,
                data: { type: 'system', source: (msg as ChatSSEMessage & { source?: string }).source }
              }],
            });
            break;
            
          case 'AGENT_REPLY':
            // Agent replied - add as assistant message
            addMessage({
              id: msg.id,
              role: 'assistant',
              content: msg.message || msg.content || '',
              timestamp: new Date(msg.timestamp),
            });
            setExecuting(false);
            break;
            
          case 'AGENT_ASK':
            // Agent asking a question
            addMessage({
              id: msg.id,
              role: 'assistant',
              content: msg.question || '',
              timestamp: new Date(msg.timestamp),
              // Store request_id for responding
              events: [{
                type: 'status',
                timestamp: msg.timestamp,
                data: { 
                  request_id: msg.request_id,
                  options: msg.options,
                  type: 'question'
                }
              }],
            });
            break;
            
          case 'AGENT_NOTIFY':
            // Agent notification (info/warning/error)
            addMessage({
              id: msg.id,
              role: 'assistant',
              content: `[${msg.level?.toUpperCase() || 'INFO'}] ${msg.message || ''}`,
              timestamp: new Date(msg.timestamp),
            });
            break;
            
          case 'AGENT_IMAGE':
            // Agent showing an image
            addMessage({
              id: msg.id,
              role: 'assistant',
              content: msg.caption || 'Image',
              timestamp: new Date(msg.timestamp),
              // Store image URL in events (use 'image' type for rendering)
              events: [{
                type: 'image',
                timestamp: msg.timestamp,
                data: { 
                  image_url: msg.image_url || (msg as unknown as Record<string, unknown>).image_path,
                  caption: msg.caption 
                }
              }],
            });
            break;
            
          case 'STATUS_UPDATE':
            // Message status update (delivered, read)
            if (msg.message_id && msg.status) {
              updateMessageStatus(msg.message_id, msg.status);
              // If status is 'read', agent started processing
              if (msg.status === 'read') {
                setExecuting(true);
              }
            }
            break;
        }
      } catch (e) {
        console.error('[Store] Failed to parse Chat SSE message:', e);
      }
    };
    
    chatEventSource.onerror = (e) => {
      console.error('[Store] Chat SSE error:', e);
      // Reconnect after delay with same agentId
      setTimeout(() => {
        if (get().isInitialized && get().currentAgentId) {
          get().connectChatSSE(get().currentAgentId!);
        }
      }, 3000);
    };
  },

  // SSE Connection: Execution logs (for Log Window)
  connectLogsSSE: (agentId?: string) => {
    const { addLog, currentAgentId } = get();
    
    // Use provided agentId or fallback to currentAgentId
    const targetAgentId = agentId || currentAgentId;
    
    // Don't connect if no agent selected
    if (!targetAgentId) {
      console.log('[Store] No agent selected, skipping Logs SSE connection');
      return;
    }
    
    // Close existing connection
    if (logsEventSource) {
      logsEventSource.close();
    }
    
    const sseUrl = `${GATEWAY_URL}/api/logs/stream?agent_id=${targetAgentId}`;
    console.log('[Store] Connecting to Logs SSE:', sseUrl);
    logsEventSource = new EventSource(sseUrl);
    
    logsEventSource.onmessage = (event) => {
      try {
        const log = JSON.parse(event.data);
        addLog({
          type: log.type || 'status',
          timestamp: log.timestamp || new Date().toISOString(),
          data: log.data || {},
        });
      } catch (e) {
        console.error('[Store] Failed to parse Log SSE message:', e);
      }
    };
    
    logsEventSource.onerror = (e) => {
      console.error('[Store] Logs SSE error:', e);
      // Reconnect after delay with same agentId
      setTimeout(() => {
        if (get().isInitialized && get().currentAgentId) {
          get().connectLogsSSE(get().currentAgentId!);
        }
      }, 3000);
    };
  },

  // Disconnect SSE streams
  disconnectSSE: () => {
    if (chatEventSource) {
      chatEventSource.close();
      chatEventSource = null;
    }
    if (logsEventSource) {
      logsEventSource.close();
      logsEventSource = null;
    }
    console.log('[Store] SSE streams disconnected');
  },

  // Load more messages (pagination - load older messages)
  loadMoreMessages: async () => {
    const { messages, isLoadingMore, hasMoreMessages, currentAgentId } = get();
    
    // Skip if already loading or no more messages
    if (isLoadingMore || !hasMoreMessages || messages.length === 0) {
      return;
    }
    
    // Skip if no agent selected
    if (!currentAgentId) {
      console.warn('[Store] No agent selected, cannot load more messages');
      return;
    }
    
    set({ isLoadingMore: true });
    
    try {
      // Get the oldest message to use as pagination cursor
      const oldestMessage = messages[0];
      
      const history = await api.getChatHistory({
        agent_id: currentAgentId,
        limit: 20,
        before_id: oldestMessage.id,
        summary_length: 100,
      });
      
      if (history.success && history.messages.length > 0) {
        // Convert API messages to local Message format
        const olderMessages: Message[] = history.messages.map((msg) => ({
          id: msg.id,
          role: msg.type === 'USER_MESSAGE' ? 'user' : 'assistant',
          content: msg.summary || '',
          timestamp: new Date(msg.timestamp),
          isTruncated: msg.is_truncated,
          status: msg.type === 'USER_MESSAGE' 
            ? (msg.read ? 'read' : 'delivered') as MessageStatus 
            : undefined,
        }));
        
        // Prepend older messages to the list
        set((state) => ({
          messages: [...olderMessages, ...state.messages],
          hasMoreMessages: history.has_more,
          isLoadingMore: false,
        }));
        
        console.log(`[Store] Loaded ${olderMessages.length} older messages, has_more: ${history.has_more}`);
      } else {
        set({ hasMoreMessages: false, isLoadingMore: false });
      }
    } catch (e) {
      console.error('[Store] Failed to load more messages:', e);
      set({ isLoadingMore: false });
    }
  },
}));
