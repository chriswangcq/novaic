/**
 * NovAIC Gateway API Client
 * 
 * Uses Tauri invoke to communicate with the Gateway over Unix Socket.
 */

import { invoke } from '@tauri-apps/api/core';

export interface AppConfig {
  version: number;
  api_keys: ApiKeyInfo[];
  available_models: AvailableModel[];
  max_tokens: number;
  max_iterations: number;
  visible_shell: boolean;
  mcp_port: number;  // 宿主机 MCP 端口 (QEMU 转发)
}

export interface ApiKeyInfo {
  id: string;
  name: string;
  provider: string;
  has_api_key: boolean;
  api_base?: string;
  deployment_name?: string;
  api_version?: string;
  created_at: string;
}

export interface AvailableModel {
  id: string;
  name: string;
  provider: string;
  api_key_id: string;
  enabled: boolean;
  is_custom: boolean;
}

export interface HealthStatus {
  status: string;
  version: string;
  agent_initialized: boolean;
  mcp_healthy: boolean;
  tools_count: number;
}

// ==================== AIC Agent Types ====================

export interface PortConfig {
  vnc: number;
  mcp: number;
  websocket: number;
  ssh: number;
}

export interface VmConfig {
  backend: string;
  image_path: string;
  os_type: string;
  os_version: string;
  memory: string;
  cpus: number;
  ports: PortConfig;
}

export interface AICAgent {
  id: string;
  name: string;
  created_at: string;
  vm: VmConfig;
  status: 'stopped' | 'starting' | 'running' | 'error';
}

export interface AgentListResponse {
  agents: AICAgent[];
  current_agent_id: string | null;
}

export interface CreateAgentRequest {
  name: string;
  backend?: string;
  os_type?: string;
  os_version?: string;
  memory?: string;
  cpus?: number;
  source_image?: string;
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
  async saveModelsForKey(keyId: string, models: AvailableModel[]): Promise<void> {
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
   */
  async initAgent(): Promise<void> {
    await invoke('gateway_post', { path: '/api/init', body: null });
  },

  /**
   * Clear chat history
   */
  async clearHistory(): Promise<void> {
    await invoke('gateway_post', { path: '/api/clear', body: null });
  },

  /**
   * Interrupt current execution
   */
  async interrupt(): Promise<void> {
    await invoke('gateway_post', { path: '/api/interrupt', body: null });
  },

  /**
   * Fetch models from provider API (for discovery)
   */
  async fetchModelsForKey(keyId: string): Promise<AvailableModel[]> {
    try {
      return invoke<AvailableModel[]>('gateway_get', { 
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
   * Get current agent
   */
  async getCurrentAgent(): Promise<AICAgent | null> {
    return invoke<AICAgent | null>('gateway_get', { path: '/api/agents/current' });
  },

  /**
   * Set current agent
   */
  async setCurrentAgent(agentId: string): Promise<void> {
    await invoke('gateway_post', { 
      path: '/api/agents/current', 
      body: { agent_id: agentId } 
    });
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
   */
  async updateAgent(agentId: string, data: Partial<{ name: string; vm: Partial<VmConfig> }>): Promise<AICAgent> {
    return invoke<AICAgent>('gateway_patch', { 
      path: `/api/agents/${agentId}`, 
      body: data 
    });
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

  // ==================== Chat API (Fire-and-Forget) ====================

  /**
   * Send a chat message (async, fire-and-forget style)
   */
  async sendChatMessage(message: string, options?: {
    model?: string;
    mode?: 'agent' | 'chat';
    api_key_id?: string;
  }): Promise<{ success: boolean; message_id: string; status: string; timestamp: string }> {
    return invoke('gateway_post', {
      path: '/api/chat/send',
      body: {
        message,
        model: options?.model,
        mode: options?.mode || 'agent',
        api_key_id: options?.api_key_id,
      }
    });
  },

  /**
   * Get chat history
   */
  async getChatHistory(options?: {
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
    }>;
    has_more: boolean;
  }> {
    const params = new URLSearchParams();
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
   */
  async getChatMessage(messageId: string): Promise<{
    success: boolean;
    id?: string;
    type?: string;
    content?: string;
    message?: string;
    timestamp?: string;
    error?: string;
  }> {
    return invoke('gateway_get', { path: `/api/chat/message/${messageId}` });
  },

  /**
   * Respond to an agent question
   */
  async respondToQuestion(requestId: string, response: string, selectedOption?: string): Promise<{
    success: boolean;
    request_id: string;
  }> {
    return invoke('gateway_post', {
      path: `/api/chat/respond/${requestId}`,
      body: {
        response,
        selected_option: selectedOption,
      }
    });
  },

  /**
   * Clear execution logs
   */
  async clearLogs(): Promise<{ success: boolean }> {
    return invoke('gateway_get', { path: '/api/logs/clear' });
  },
};

export default api;
