/**
 * NovAIC Gateway API Client
 * 
 * Uses Tauri invoke to communicate with the Gateway over Unix Socket.
 */

import { invoke } from '@tauri-apps/api/core';

/**
 * AppConfig - Application configuration from backend.
 * 
 * This matches the output of AppConfig.to_public() in manager_db.py
 */
export interface AppConfig {
  version: number;
  api_keys: ApiKeyInfo[];
  candidate_models: CandidateModel[];
  max_tokens: number;
  max_iterations: number;
  visible_shell: boolean;
}

/**
 * ApiKeyInfo - API key public info from backend.
 * 
 * Matches ApiKeyEntry.to_public() output - sensitive api_key is hidden.
 */
export interface ApiKeyInfo {
  id: string;
  name: string;
  provider: string;
  has_api_key: boolean;
  api_base: string | null;
  deployment_name: string | null;
  api_version: string | null;
  created_at: string;
}

/**
 * CandidateModel - Unified model representation
 * 
 * Used across all model-related APIs:
 * - /api/config (candidate_models array)
 * - /api/agents/models/available (enabled models)
 * - /api/agents/{id}/model (agent's selected model)
 */
export interface CandidateModel {
  id: string;
  name: string;
  provider: string;         // Provider type: openai, anthropic, google, etc.
  api_key_id: string;       // API key ID this model belongs to
  api_key_name: string;     // API key name for display
  enabled: boolean;         // Whether model is enabled for selection
  is_custom: boolean;       // Custom model added by user
}

// Agent's current model configuration (matches AgentModelConfigResponse)
export interface AgentModelConfig {
  agent_id: string;
  model_id: string | null;
  model: CandidateModel | null;
  api_key?: string;
  api_base?: string;
}

export interface HealthStatus {
  status: string;
  version: string;
  agent_initialized: boolean;
  mcp_healthy: boolean;
  tools_count: number;
}

// ==================== AIC Agent Types ====================

// Port configuration - matches Python PortConfig in novaic-gateway/config/agents_db.py
export interface PortConfig {
  ssh: number;    // SSH port for VM access (0 = not assigned)
  vmuse: number;  // VMUSE HTTP API port (0 = not assigned)
}

export interface VmConfig {
  backend: string;
  image_path: string;
  os_type: string;
  os_version: string;
  memory: string;
  cpus: number;
  ports: PortConfig;
  android?: {
    device_serial: string;
    managed: boolean;
    avd_name?: string;
  };
}

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
  setup_progress?: SetupProgressInfo;
  android?: {
    device_serial: string;   // 如 "emulator-5554"
    managed?: boolean;       // 是否由 novaic 管理
    avd_name?: string;       // 托管模式下的 AVD 名称
  };
}

export interface AgentListResponse {
  agents: AICAgent[];
}

// Agent 类型
export type AgentType = 'linux' | 'android' | 'hybrid';

// Android 管理模式
export type AndroidManageMode = 'managed' | 'external';

// Android 配置
export interface AndroidConfig {
  manageMode: AndroidManageMode;
  // 托管模式配置
  systemImage?: string;      // 系统镜像包名
  deviceDefinition?: string; // 设备定义 ID
  avdName?: string;          // AVD 名称（可选，自动生成）
  // 外部设备模式配置
  deviceSerial?: string;     // 设备序列号
}

// VM 配置请求（用于创建/更新 Linux VM）
export interface VmConfigRequest {
  backend?: string;
  os_type?: string;
  os_version?: string;
  memory?: string;
  cpus?: number;
  source_image?: string;
}

// Android 配置请求
export interface AndroidConfigRequest {
  managed: boolean;           // 是否由 novaic 管理
  avd_name?: string;          // AVD 名称（托管模式）
  device_serial?: string;     // 设备序列号（外部模式）
}

export interface CreateAgentRequest {
  name: string;
  model?: string;             // LLM 模型 ID
  // Agent 类型: 'chat' | 'linux' | 'android' | 'hybrid'
  agent_type?: AgentType;
  // Linux VM 配置（新格式）
  vm_config?: VmConfigRequest;
  // Android 配置
  android?: AndroidConfigRequest;
  // Legacy fields for backward compatibility
  backend?: string;
  os_type?: string;
  os_version?: string;
  memory?: string;
  cpus?: number;
  source_image?: string;
}

// 更新 Agent 请求
export interface UpdateAgentRequest {
  name?: string;
  vm_config?: VmConfigRequest;  // 添加/更新 VM 配置
  android?: AndroidConfigRequest;  // 添加/更新 Android 配置
  setup_complete?: boolean;
}

export interface AvailableImage {
  path: string;
  name: string;
  size: number;
  source: string;
}

/**
 * Gateway API client using Tauri IPC → Unix Socket
 */
export const api = {
  /**
   * Get health status
   */
  async getHealth(): Promise<HealthStatus> {
    return invoke<HealthStatus>('gateway_get', { path: '/api/health' });
  },

  /**
   * Check if Gateway is healthy
   */
  async isHealthy(): Promise<boolean> {
    return invoke<boolean>('gateway_health');
  },

  /**
   * Get configuration (public version)
   */
  async getConfig(): Promise<AppConfig> {
    return invoke<AppConfig>('gateway_get', { path: '/api/config' });
  },

  /**
   * Update settings
   */
  async updateSettings(settings: Partial<{
    max_tokens: number;
    max_iterations: number;
    visible_shell: boolean;
  }>): Promise<void> {
    await invoke('gateway_patch', { 
      path: '/api/config/settings', 
      body: settings 
    });
  },

  /**
   * Add API key
   */
  async addApiKey(data: {
    provider: string;
    name?: string;
    api_key?: string;
    api_base?: string;
    deployment_name?: string;
    api_version?: string;
  }): Promise<ApiKeyInfo> {
    return invoke<ApiKeyInfo>('gateway_post', { 
      path: '/api/config/api-keys', 
      body: data 
    });
  },

  /**
   * Update API key
   */
  async updateApiKey(keyId: string, data: {
    name?: string;
    api_key?: string;
    api_base?: string;
    deployment_name?: string;
    api_version?: string;
  }): Promise<ApiKeyInfo> {
    return invoke<ApiKeyInfo>('gateway_patch', { 
      path: `/api/config/api-keys/${keyId}`, 
      body: data 
    });
  },

  /**
   * Delete API key
   */
  async deleteApiKey(keyId: string): Promise<void> {
    await invoke('gateway_delete', { path: `/api/config/api-keys/${keyId}` });
  },

  /**
   * Toggle model enabled state
   */
  async toggleModel(modelId: string, apiKeyId: string, enabled: boolean): Promise<void> {
    await invoke('gateway_post', { 
      path: '/api/config/models/toggle', 
      body: { model_id: modelId, api_key_id: apiKeyId, enabled } 
    });
  },

  /**
   * Delete model
   */
  async deleteModel(apiKeyId: string, modelId: string): Promise<void> {
    await invoke('gateway_delete', { 
      path: `/api/config/models/${apiKeyId}/${modelId}` 
    });
  },

  /**
   * Save models for API key (merges with existing, keeps custom models)
   */
  async saveModelsForKey(keyId: string, models: CandidateModel[]): Promise<void> {
    await invoke('gateway_post', { 
      path: `/api/config/api-keys/${keyId}/models`, 
      body: models 
    });
  },

  /**
   * Add a single custom model
   */
  async addModel(keyId: string, modelId: string, modelName: string): Promise<void> {
    await invoke('gateway_post', { 
      path: `/api/config/api-keys/${keyId}/models/add`, 
      body: { id: modelId, name: modelName }
    });
  },

  /**
   * Initialize agent
   * @param agent_id - Optional agent ID to initialize specific agent
   */
  async initAgent(agent_id?: string): Promise<void> {
    const params = new URLSearchParams();
    if (agent_id) params.set('agent_id', agent_id);
    const queryString = params.toString();
    const path = queryString ? `/api/init?${queryString}` : '/api/init';
    await invoke('gateway_post', { path, body: null });
  },

  /**
   * Clear chat history
   * @param agent_id - Optional agent ID to clear history for specific agent
   */
  async clearHistory(agent_id?: string): Promise<void> {
    const params = new URLSearchParams();
    if (agent_id) params.set('agent_id', agent_id);
    const queryString = params.toString();
    const path = queryString ? `/api/clear?${queryString}` : '/api/clear';
    await invoke('gateway_post', { path, body: null });
  },

  /**
   * Interrupt current execution
   * @param agent_id - Optional agent ID to interrupt specific agent
   */
  async interrupt(agent_id?: string): Promise<void> {
    const params = new URLSearchParams();
    if (agent_id) params.set('agent_id', agent_id);
    const queryString = params.toString();
    const path = queryString ? `/api/interrupt?${queryString}` : '/api/interrupt';
    await invoke('gateway_post', { path, body: null });
  },

  /**
   * Fetch models from provider API (for discovery)
   */
  async fetchModelsForKey(keyId: string): Promise<CandidateModel[]> {
    try {
      return invoke<CandidateModel[]>('gateway_get', { 
        path: `/api/config/api-keys/${keyId}/fetch-models` 
      });
    } catch {
      console.warn('[API] fetchModelsForKey not yet implemented on gateway');
      return [];
    }
  },

  /**
   * Test API key connection
   */
  async testApiKeyConnection(keyId: string): Promise<{ success: boolean; error?: string }> {
    try {
      return invoke<{ success: boolean; error?: string }>('gateway_post', { 
        path: `/api/config/api-keys/${keyId}/test`,
        body: null
      });
    } catch {
      console.warn('[API] testApiKeyConnection not yet implemented on gateway');
      return { success: true };
    }
  },

  /**
   * Gateway management
   */
  async startGateway(): Promise<string> {
    return invoke<string>('start_gateway');
  },

  async stopGateway(): Promise<string> {
    return invoke<string>('stop_gateway');
  },

  async getGatewayStatus(): Promise<boolean> {
    return invoke<boolean>('get_gateway_status');
  },

  // ==================== AIC Agent API ====================

  /**
   * List all AIC agents
   */
  async listAgents(): Promise<AgentListResponse> {
    return invoke<AgentListResponse>('gateway_get', { path: '/api/agents' });
  },

  /**
   * Get agent by ID
   */
  async getAgent(agentId: string): Promise<AICAgent> {
    return invoke<AICAgent>('gateway_get', { path: `/api/agents/${agentId}` });
  },

  /**
   * Create a new agent
   */
  async createAgent(data: CreateAgentRequest): Promise<AICAgent> {
    return invoke<AICAgent>('gateway_post', { 
      path: '/api/agents', 
      body: data 
    });
  },

  /**
   * Update an agent
   * 
   * Supports partial updates:
   * - name: Update agent name
   * - vm_config: Add or update Linux VM configuration
   * - android: Add or update Android configuration
   * - setup_complete: Mark VM setup as complete
   */
  async updateAgent(agentId: string, data: UpdateAgentRequest): Promise<AICAgent> {
    return invoke<AICAgent>('gateway_patch', { 
      path: `/api/agents/${agentId}`, 
      body: data 
    });
  },

  /**
   * Add Linux VM configuration to an existing agent
   */
  async addVmConfig(agentId: string, vmConfig: VmConfigRequest): Promise<AICAgent> {
    return this.updateAgent(agentId, { vm_config: vmConfig });
  },

  /**
   * Add Android configuration to an existing agent
   */
  async addAndroidConfig(agentId: string, androidConfig: AndroidConfigRequest): Promise<AICAgent> {
    return this.updateAgent(agentId, { android: androidConfig });
  },

  /**
   * Delete an agent
   */
  async deleteAgent(agentId: string): Promise<void> {
    await invoke('gateway_delete', { path: `/api/agents/${agentId}` });
  },

  /**
   * Get available VM images
   */
  async getAvailableImages(): Promise<AvailableImage[]> {
    return invoke<AvailableImage[]>('gateway_get', { path: '/api/agents/images' });
  },

  /**
   * List all available (enabled) models for selection.
   * Returns CandidateModel[] with enabled=true and valid API keys.
   */
  async listAvailableModels(): Promise<CandidateModel[]> {
    const result = await invoke<CandidateModel[]>('gateway_get', { 
      path: '/api/agents/models/available' 
    });
    return result || [];
  },

  /**
   * Set the model for an agent
   * @param agentId - The agent ID
   * @param modelId - The model ID to set
   */
  async setAgentModel(agentId: string, modelId: string): Promise<void> {
    await invoke('gateway_put', {
      path: `/api/agents/${agentId}/model`,
      body: { model_id: modelId }
    });
  },

  /**
   * Get the current model configuration for an agent
   * @param agentId - The agent ID
   */
  async getAgentModel(agentId: string): Promise<AgentModelConfig> {
    return invoke<AgentModelConfig>('gateway_get', { 
      path: `/api/agents/${agentId}/model` 
    });
  },

  // ==================== Chat API (Fire-and-Forget) ====================

  /**
   * Send a chat message (async, fire-and-forget style)
   * @param message - The message content to send
   * @param options - Optional parameters
   * @param options.agent_id - Target agent ID
   * @param options.model - Model to use for the response
   * @param options.mode - Chat mode ('agent' or 'chat')
   * @param options.api_key_id - API key ID to use
   */
  async sendChatMessage(message: string, options?: {
    agent_id?: string;
    model?: string;
    mode?: 'agent' | 'chat';
    api_key_id?: string;
  }): Promise<{ success: boolean; message_id: string; status: string; timestamp: string }> {
    return invoke('gateway_post', {
      path: '/api/chat/send',
      body: {
        message,
        agent_id: options?.agent_id,
        model: options?.model,
        mode: options?.mode || 'agent',
        api_key_id: options?.api_key_id,
      }
    });
  },

  /**
   * Get chat history
   * @param options - Optional parameters
   * @param options.agent_id - Target agent ID
   * @param options.limit - Maximum number of messages to return
   * @param options.before_id - Return messages before this ID (pagination)
   * @param options.message_type - Filter by message type
   * @param options.summary_length - Maximum length of message summaries
   */
  async getChatHistory(options?: {
    agent_id?: string;
    limit?: number;
    before_id?: string;
    message_type?: string;
    summary_length?: number;
  }): Promise<{
    success: boolean;
    messages: Array<{
      id: string;
      type: string;
      timestamp: string;
      summary: string;
      is_truncated: boolean;
      read: boolean;
    }>;
    has_more: boolean;
  }> {
    const params = new URLSearchParams();
    if (options?.agent_id) params.set('agent_id', options.agent_id);
    if (options?.limit) params.set('limit', options.limit.toString());
    if (options?.before_id) params.set('before_id', options.before_id);
    if (options?.message_type) params.set('message_type', options.message_type);
    if (options?.summary_length) params.set('summary_length', options.summary_length.toString());
    
    const queryString = params.toString();
    const path = queryString ? `/api/chat/history?${queryString}` : '/api/chat/history';
    return invoke('gateway_get', { path });
  },

  /**
   * Get full message content by ID
   * @param messageId - The message ID to retrieve
   * @param agentId - Optional agent ID for the message
   */
  async getChatMessage(messageId: string, agentId?: string): Promise<{
    success: boolean;
    id?: string;
    type?: string;
    content?: string;
    message?: string;
    timestamp?: string;
    error?: string;
  }> {
    const params = new URLSearchParams();
    if (agentId) params.set('agent_id', agentId);
    const queryString = params.toString();
    const path = queryString 
      ? `/api/chat/message/${messageId}?${queryString}` 
      : `/api/chat/message/${messageId}`;
    return invoke('gateway_get', { path });
  },

  /**
   * Respond to an agent question
   * @param requestId - The request ID to respond to
   * @param response - The response text
   * @param selectedOption - Optional selected option for multiple choice questions
   * @param agentId - Optional agent ID
   */
  async respondToQuestion(requestId: string, response: string, selectedOption?: string, agentId?: string): Promise<{
    success: boolean;
    request_id: string;
  }> {
    return invoke('gateway_post', {
      path: `/api/chat/respond/${requestId}`,
      body: {
        response,
        selected_option: selectedOption,
        agent_id: agentId,
      }
    });
  },

  /**
   * Interrupt agent execution
   * @param agentId - Optional agent ID to interrupt specific agent
   */
  async interruptAgent(agentId?: string): Promise<{ success: boolean; message?: string; error?: string }> {
    return invoke('gateway_post', {
      path: '/api/agent/interrupt',
      body: { agent_id: agentId }
    });
  },

  /**
   * Fetch execution log entries (initial, incremental, or paginated).
   * SSE 只推送「有更新」通知，前端用此接口拉取内容。
   * @param agentId - Agent ID
   * @param options.after_id - 只返回 id > after_id 的条目（增量）
   * @param options.before_id - 只返回 id < before_id 的条目（向前翻页）
   * @param options.limit - 条数上限
   * @param options.subagent_id - 只返回指定 subagent 的日志（可选）
   */
  async getLogEntries(
    agentId: string,
    options?: { after_id?: number; before_id?: number; limit?: number; subagent_id?: string }
  ): Promise<{ success: boolean; entries: Array<{ id: number; type: string; timestamp: string; data: Record<string, unknown>; subagent_id?: string; status?: 'running' | 'complete'; kind?: 'think' | 'tool'; event_key?: string; input?: any; result?: any; updated_at?: string }>; has_more: boolean }> {
    const params = new URLSearchParams();
    params.set('agent_id', agentId);
    if (options?.after_id != null) params.set('after_id', String(options.after_id));
    if (options?.before_id != null) params.set('before_id', String(options.before_id));
    if (options?.limit != null) params.set('limit', String(options.limit));
    if (options?.subagent_id != null) params.set('subagent_id', options.subagent_id);
    return invoke('gateway_get', { path: `/api/logs/entries?${params.toString()}` });
  },

  /**
   * Get list of subagent IDs that have logs for the given agent.
   * @param agentId - Agent ID
   */
  async getLogSubagents(agentId: string): Promise<{ success: boolean; subagents: string[] }> {
    const params = new URLSearchParams();
    params.set('agent_id', agentId);
    return invoke('gateway_get', { path: `/api/logs/subagents?${params.toString()}` });
  },

  /**
   * Clear execution logs
   * @param agentId - Optional agent ID to clear logs for specific agent
   */
  async clearLogs(agentId?: string): Promise<{ success: boolean }> {
    const params = new URLSearchParams();
    if (agentId) params.set('agent_id', agentId);
    const queryString = params.toString();
    const path = queryString ? `/api/logs/clear?${queryString}` : '/api/logs/clear';
    return invoke('gateway_get', { path });
  },

  // ==================== Skills ====================

  async getSkills(includeBuiltin: boolean = true): Promise<{ 
    skills: any[]; 
    builtin_skills: any[];
    custom_skills: any[];
    count: number;
    builtin_count: number;
    custom_count: number;
  }> {
    const params = new URLSearchParams();
    params.set('include_builtin', includeBuiltin.toString());
    return invoke('gateway_get', { path: `/api/skills?${params.toString()}` });
  },

  async getSkill(skillId: string): Promise<any> {
    return invoke('gateway_get', { path: `/api/skills/${encodeURIComponent(skillId)}` });
  },

  async createSkill(data: any): Promise<any> {
    return invoke('gateway_post', { path: '/api/skills', body: data });
  },

  async forkSkill(skillId: string, newName?: string): Promise<any> {
    return invoke('gateway_post', { 
      path: `/api/skills/${encodeURIComponent(skillId)}/fork`, 
      body: newName ? { name: newName } : {} 
    });
  },

  async updateSkill(skillId: string, data: any): Promise<any> {
    return invoke('gateway_put', { path: `/api/skills/${encodeURIComponent(skillId)}`, body: data });
  },

  async deleteSkill(skillId: string): Promise<any> {
    return invoke('gateway_delete', { path: `/api/skills/${encodeURIComponent(skillId)}` });
  },

  async getAgentSkills(agentId: string): Promise<{ skills: any[]; count: number }> {
    return invoke('gateway_get', { path: `/api/agents/${agentId}/skills` });
  },

  async setAgentSkills(agentId: string, skillIds: string[]): Promise<any> {
    return invoke('gateway_post', { path: `/api/agents/${agentId}/skills`, body: { skill_ids: skillIds } });
  },

  async matchSkillsForTask(task: string, maxSkills: number = 3): Promise<{ matched_skills: any[]; count: number }> {
    return invoke('gateway_post', { path: '/api/skills/match', body: { task, max_skills: maxSkills } });
  },

  async getAgentToolsConfig(agentId: string): Promise<any> {
    return invoke('gateway_get', { path: `/api/agents/${agentId}/tools-config` });
  },

  async saveAgentToolsConfig(agentId: string, data: any): Promise<any> {
    return invoke('gateway_post', { path: `/api/agents/${agentId}/tools-config`, body: data });
  },

  async getPromptsPreview(agentId: string): Promise<any> {
    return invoke('gateway_get', { path: `/api/agents/${agentId}/prompts-preview` });
  },

  async getToolCategories(): Promise<any> {
    return invoke('gateway_get', { path: '/api/tools/categories' });
  },

  // ==================== Bootstrap Files API ====================

  /**
   * Get bootstrap files for an agent
   */
  async getBootstrapFiles(agentId: string): Promise<{
    soul_md: string;
    heartbeat_md: string;
    memory_md: string;
    user_md: string;
    active_hours_start: string;
    active_hours_end: string;
    active_hours_timezone: string;
  }> {
    return invoke('gateway_get', { path: `/api/agents/${agentId}/bootstrap-files` });
  },

  /**
   * Save bootstrap files for an agent
   */
  async saveBootstrapFiles(agentId: string, data: {
    soul_md?: string;
    heartbeat_md?: string;
    memory_md?: string;
    user_md?: string;
    active_hours_start?: string;
    active_hours_end?: string;
    active_hours_timezone?: string;
  }): Promise<{ success: boolean }> {
    return invoke('gateway_post', {
      path: `/api/agents/${agentId}/bootstrap-files`,
      body: data,
    });
  },

  // ==================== Cleanup API ====================

  // ==================== Android VM API ====================

  /**
   * Start Android emulator via Gateway
   */
  async startAndroid(agentId: string): Promise<{ success: boolean; device_serial?: string; message?: string }> {
    return invoke('gateway_post', {
      path: '/api/vm/android/start',
      body: { agent_id: agentId },
    });
  },

  /**
   * Stop Android emulator via Gateway
   */
  async stopAndroid(agentId: string): Promise<{ success: boolean; message?: string }> {
    return invoke('gateway_post', {
      path: '/api/vm/android/stop',
      body: { agent_id: agentId },
    });
  },

  /**
   * Get Android emulator status via Gateway
   */
  async getAndroidStatus(agentId: string): Promise<{
    agent_id: string;
    has_android: boolean;
    avd_name?: string;
    device_serial?: string;
    running: boolean;
  }> {
    return invoke('gateway_get', {
      path: `/api/vm/android/status/${agentId}`,
    });
  },

  /**
   * Clean up garbage files and cache
   */
  async cleanupGarbage(options?: {
    deep?: boolean;
    days?: number;
    clean_vm_cache?: boolean;
  }): Promise<{
    status: string;
    message: string;
    details: {
      logs: number;
      metadata_files: number;
      temp_files: number;
      empty_dirs: number;
      database_vacuumed: boolean;
      orphaned_agents: number;
      vm_images: number;
    };
  }> {
    const params = new URLSearchParams();
    if (options?.deep) params.set('deep', 'true');
    if (options?.days) params.set('days', options.days.toString());
    if (options?.clean_vm_cache) params.set('clean_vm_cache', 'true');
    
    const queryString = params.toString();
    const path = queryString ? `/api/config/cleanup?${queryString}` : '/api/config/cleanup';
    return invoke('gateway_post', { path, body: {} });
  },
};

export default api;
