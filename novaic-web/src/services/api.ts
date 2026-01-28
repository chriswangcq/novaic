/**
 * NovAIC Gateway API Client
 * 
 * Replaces Tauri invoke calls with direct HTTP requests to the Gateway.
 */

const GATEWAY_URL = import.meta.env.VITE_GATEWAY_URL || 'http://127.0.0.1:9000';

export interface AppConfig {
  version: number;
  api_keys: ApiKeyInfo[];
  available_models: AvailableModel[];
  default_model: string;
  max_tokens: number;
  max_iterations: number;
  visible_shell: boolean;
  executor_url: string;
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

/**
 * Gateway API client
 */
export const api = {
  /**
   * Get health status
   */
  async getHealth(): Promise<HealthStatus> {
    const res = await fetch(`${GATEWAY_URL}/api/health`);
    if (!res.ok) throw new Error(`Health check failed: ${res.status}`);
    return res.json();
  },

  /**
   * Get configuration (public version)
   */
  async getConfig(): Promise<AppConfig> {
    const res = await fetch(`${GATEWAY_URL}/api/config`);
    if (!res.ok) throw new Error(`Get config failed: ${res.status}`);
    return res.json();
  },

  /**
   * Update settings
   */
  async updateSettings(settings: Partial<{
    default_model: string;
    max_tokens: number;
    max_iterations: number;
    visible_shell: boolean;
    executor_url: string;
  }>): Promise<void> {
    const res = await fetch(`${GATEWAY_URL}/api/config/settings`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(settings),
    });
    if (!res.ok) throw new Error(`Update settings failed: ${res.status}`);
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
    const res = await fetch(`${GATEWAY_URL}/api/config/api-keys`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error(`Add API key failed: ${res.status}`);
    return res.json();
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
    const res = await fetch(`${GATEWAY_URL}/api/config/api-keys/${keyId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error(`Update API key failed: ${res.status}`);
    return res.json();
  },

  /**
   * Delete API key
   */
  async deleteApiKey(keyId: string): Promise<void> {
    const res = await fetch(`${GATEWAY_URL}/api/config/api-keys/${keyId}`, {
      method: 'DELETE',
    });
    if (!res.ok) throw new Error(`Delete API key failed: ${res.status}`);
  },

  /**
   * Toggle model enabled state
   */
  async toggleModel(modelId: string, apiKeyId: string, enabled: boolean): Promise<void> {
    const res = await fetch(`${GATEWAY_URL}/api/config/models/toggle`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ model_id: modelId, api_key_id: apiKeyId, enabled }),
    });
    if (!res.ok) throw new Error(`Toggle model failed: ${res.status}`);
  },

  /**
   * Delete model
   */
  async deleteModel(apiKeyId: string, modelId: string): Promise<void> {
    const res = await fetch(`${GATEWAY_URL}/api/config/models/${apiKeyId}/${modelId}`, {
      method: 'DELETE',
    });
    if (!res.ok) throw new Error(`Delete model failed: ${res.status}`);
  },

  /**
   * Save models for API key
   */
  async saveModelsForKey(keyId: string, models: AvailableModel[]): Promise<void> {
    const res = await fetch(`${GATEWAY_URL}/api/config/api-keys/${keyId}/models`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(models),
    });
    if (!res.ok) throw new Error(`Save models failed: ${res.status}`);
  },

  /**
   * Set default model
   */
  async setDefaultModel(modelId: string): Promise<void> {
    const res = await fetch(`${GATEWAY_URL}/api/config/default-model`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ model_id: modelId }),
    });
    if (!res.ok) throw new Error(`Set default model failed: ${res.status}`);
  },

  /**
   * Initialize agent
   */
  async initAgent(): Promise<void> {
    const res = await fetch(`${GATEWAY_URL}/api/init`, { method: 'POST' });
    if (!res.ok) throw new Error(`Init agent failed: ${res.status}`);
  },

  /**
   * Clear chat history
   */
  async clearHistory(): Promise<void> {
    const res = await fetch(`${GATEWAY_URL}/api/clear`, { method: 'POST' });
    if (!res.ok) throw new Error(`Clear history failed: ${res.status}`);
  },

  /**
   * Interrupt current execution
   */
  async interrupt(): Promise<void> {
    const res = await fetch(`${GATEWAY_URL}/api/interrupt`, { method: 'POST' });
    if (!res.ok) throw new Error(`Interrupt failed: ${res.status}`);
  },

  /**
   * Fetch models from provider API (for discovery)
   */
  async fetchModelsForKey(keyId: string): Promise<AvailableModel[]> {
    // This would need to be implemented on the gateway side
    // For now, return empty array
    console.warn('[API] fetchModelsForKey not yet implemented on gateway');
    return [];
  },

  /**
   * Test API key connection
   */
  async testApiKeyConnection(keyId: string): Promise<{ success: boolean; error?: string }> {
    // This would need to be implemented on the gateway side
    // For now, return success
    console.warn('[API] testApiKeyConnection not yet implemented on gateway');
    return { success: true };
  },
};

export default api;
