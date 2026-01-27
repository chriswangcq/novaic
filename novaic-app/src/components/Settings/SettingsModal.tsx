import { useEffect, useState, useCallback, useMemo } from 'react';
import { invoke } from '@tauri-apps/api/core';
import { ChevronDown, ChevronRight, Search, Plus, X, Star } from 'lucide-react';

// ==================== Types ====================

type ProviderType = 'openai' | 'anthropic' | 'google' | 'azure' | 'openai_compatible';

interface ApiKeyEntryPublic {
  id: string;
  name: string;
  provider: ProviderType;
  has_api_key: boolean;
  api_base: string | null;
  deployment_name: string | null;
  api_version: string | null;
  created_at: string;
}

interface AvailableModel {
  id: string;
  name: string;
  provider: ProviderType;
  api_key_id: string;
  enabled: boolean;
  is_custom?: boolean;
}

interface AppConfigPublic {
  version: number;
  api_keys: ApiKeyEntryPublic[];
  available_models: AvailableModel[];
  default_model: string;
  max_tokens: number;
  max_iterations: number;
  visible_shell: boolean;
}

interface ModelInfo {
  id: string;
  name: string;
}

interface FetchModelsResult {
  ok: boolean;
  models: ModelInfo[];
  message: string;
}

interface TestConnectionResult {
  ok: boolean;
  message: string;
}

// ==================== Provider Info ====================

const PROVIDER_INFO: Record<ProviderType, { 
  name: string; 
  description: string; 
  docsUrl?: string;
  defaultBaseUrl?: string;
  icon: string;
  fields: ('api_key' | 'api_base' | 'deployment_name' | 'api_version')[];
}> = {
  openai: {
    name: 'OpenAI',
    description: 'GPT-4, GPT-4o, o1, etc.',
    docsUrl: 'https://platform.openai.com/api-keys',
    defaultBaseUrl: 'https://api.openai.com/v1',
    icon: '🤖',
    fields: ['api_key', 'api_base'],
  },
  anthropic: {
    name: 'Anthropic',
    description: 'Claude 3.5, Claude 3, etc.',
    docsUrl: 'https://console.anthropic.com/settings/keys',
    defaultBaseUrl: 'https://api.anthropic.com',
    icon: '🧠',
    fields: ['api_key', 'api_base'],
  },
  google: {
    name: 'Google AI',
    description: 'Gemini Pro, Gemini Flash, etc.',
    docsUrl: 'https://aistudio.google.com/app/apikey',
    defaultBaseUrl: 'https://generativelanguage.googleapis.com/v1beta',
    icon: '✨',
    fields: ['api_key', 'api_base'],
  },
  azure: {
    name: 'Azure OpenAI',
    description: 'OpenAI models via Azure',
    docsUrl: 'https://portal.azure.com/',
    icon: '☁️',
    fields: ['api_key', 'api_base', 'deployment_name', 'api_version'],
  },
  openai_compatible: {
    name: 'OpenAI Compatible',
    description: 'Ollama, vLLM, DeepSeek, etc.',
    icon: '🔗',
    fields: ['api_key', 'api_base'],
  },
};

// ==================== Small Components ====================

function Toggle({ checked, onChange, disabled }: { checked: boolean; onChange: (v: boolean) => void; disabled?: boolean }) {
  return (
    <button
      onClick={() => !disabled && onChange(!checked)}
      disabled={disabled}
      className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors flex-shrink-0 ${
        checked ? 'bg-green-500' : 'bg-nb-surface-2'
      } ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
    >
      <span
        className={`inline-block h-3.5 w-3.5 transform rounded-full bg-white transition-transform ${
          checked ? 'translate-x-5' : 'translate-x-1'
        }`}
      />
    </button>
  );
}

function FormField({ 
  label, 
  placeholder, 
  value, 
  onChange, 
  type = 'text',
  disabled
}: { 
  label: string; 
  placeholder?: string; 
  value: string; 
  onChange: (v: string) => void;
  type?: 'text' | 'password';
  disabled?: boolean;
}) {
  return (
    <div className="space-y-1">
      <label className="text-xs font-medium text-nb-text-muted">{label}</label>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        disabled={disabled}
        className="w-full rounded-lg border border-nb-border bg-nb-surface-2 px-3 py-2 text-sm text-nb-text outline-none focus:ring-2 focus:ring-nb-accent/50 disabled:opacity-50"
      />
    </div>
  );
}

// ==================== Model Section in API Key Card ====================

function ModelSection({
  apiKeyId,
  models,
  defaultModel,
  onToggle,
  onSetDefault,
  onAddCustomModel,
  onFetchModels,
  fetching,
}: {
  apiKeyId: string;
  models: AvailableModel[];
  defaultModel: string;
  onToggle: (modelId: string, enabled: boolean) => void;
  onSetDefault: (modelId: string) => void;
  onAddCustomModel: (apiKeyId: string, modelId: string, modelName: string) => void;
  onFetchModels: () => void;
  fetching: boolean;
}) {
  const [expanded, setExpanded] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [showAllModels, setShowAllModels] = useState(false);

  const enabledModels = models.filter(m => m.enabled);
  const disabledModels = models.filter(m => !m.enabled);
  
  // Filter models by search
  const filteredModels = useMemo(() => {
    if (!searchQuery.trim()) return null;
    const q = searchQuery.toLowerCase();
    return models.filter(m => 
      m.id.toLowerCase().includes(q) || 
      m.name.toLowerCase().includes(q)
    );
  }, [models, searchQuery]);

  // Top recommended models (first 10 disabled ones)
  const recommendedModels = disabledModels.slice(0, 10);

  // Check if search query matches any existing model
  const isCustomModel = searchQuery.trim() && 
    !models.some(m => m.id.toLowerCase() === searchQuery.toLowerCase().trim());

  const handleAddCustom = () => {
    const modelId = searchQuery.trim();
    if (modelId) {
      onAddCustomModel(apiKeyId, modelId, modelId);
      setSearchQuery('');
    }
  };

  // Collapsed view
  if (!expanded) {
    return (
      <button
        onClick={() => setExpanded(true)}
        className="w-full flex items-center justify-between py-2 px-3 -mx-3 rounded-lg hover:bg-nb-surface-2/50 transition-colors group"
      >
        <div className="flex items-center gap-2 text-sm text-nb-text-muted">
          <ChevronRight size={14} className="group-hover:text-nb-text transition-colors" />
          <span>
            {models.length === 0 ? (
              'No models loaded'
            ) : (
              <>
                <span className="text-nb-text">{enabledModels.length}</span>
                <span> / {models.length} models enabled</span>
              </>
            )}
          </span>
        </div>
        {models.length === 0 && (
          <span className="text-xs text-nb-accent">Fetch models →</span>
        )}
      </button>
    );
  }

  // Expanded view
  return (
    <div className="space-y-3 pt-2 border-t border-nb-border mt-3">
      {/* Header with collapse button */}
      <div className="flex items-center justify-between">
        <button
          onClick={() => setExpanded(false)}
          className="flex items-center gap-2 text-sm text-nb-text-muted hover:text-nb-text transition-colors"
        >
          <ChevronDown size={14} />
          <span>Models ({enabledModels.length}/{models.length})</span>
        </button>
        <button
          onClick={onFetchModels}
          disabled={fetching}
          className="text-xs text-nb-accent hover:underline disabled:opacity-50"
        >
          {fetching ? 'Fetching...' : 'Refresh'}
        </button>
      </div>

      {/* Search box */}
      <div className="relative">
        <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-nb-text-muted" />
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Search or add custom model..."
          className="w-full rounded-lg border border-nb-border bg-nb-surface-2 pl-9 pr-3 py-2 text-sm text-nb-text outline-none focus:ring-2 focus:ring-nb-accent/50"
        />
        {searchQuery && (
          <button
            onClick={() => setSearchQuery('')}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-nb-text-muted hover:text-nb-text"
          >
            <X size={14} />
          </button>
        )}
      </div>

      {/* Search results or default view */}
      {searchQuery.trim() ? (
        <div className="space-y-1 max-h-[200px] overflow-y-auto">
          {filteredModels && filteredModels.length > 0 ? (
            filteredModels.map(model => (
              <ModelItem
                key={model.id}
                model={model}
                isDefault={model.id === defaultModel}
                onToggle={onToggle}
                onSetDefault={onSetDefault}
              />
            ))
          ) : null}
          
          {/* Add custom model option */}
          {isCustomModel && (
            <button
              onClick={handleAddCustom}
              className="w-full flex items-center gap-2 py-2 px-3 rounded-lg hover:bg-nb-surface-2 transition-colors text-left"
            >
              <Plus size={14} className="text-nb-accent" />
              <span className="text-sm text-nb-text">
                Add custom model: <span className="text-nb-accent font-medium">{searchQuery.trim()}</span>
              </span>
            </button>
          )}

          {!filteredModels?.length && !isCustomModel && (
            <div className="text-sm text-nb-text-muted py-2 text-center">
              No matching models
            </div>
          )}
        </div>
      ) : (
        <>
          {/* Enabled models */}
          {enabledModels.length > 0 && (
            <div className="space-y-1">
              <div className="text-[11px] font-medium text-nb-text-muted uppercase tracking-wider">
                Enabled ({enabledModels.length})
              </div>
              <div className="space-y-0.5 max-h-[120px] overflow-y-auto">
                {enabledModels.map(model => (
                  <ModelItem
                    key={model.id}
                    model={model}
                    isDefault={model.id === defaultModel}
                    onToggle={onToggle}
                    onSetDefault={onSetDefault}
                  />
                ))}
              </div>
            </div>
          )}

          {/* Recommended/Available models */}
          {recommendedModels.length > 0 && (
            <div className="space-y-1">
              <div className="text-[11px] font-medium text-nb-text-muted uppercase tracking-wider">
                Available
              </div>
              <div className="space-y-0.5 max-h-[120px] overflow-y-auto">
                {recommendedModels.map(model => (
                  <ModelItem
                    key={model.id}
                    model={model}
                    isDefault={model.id === defaultModel}
                    onToggle={onToggle}
                    onSetDefault={onSetDefault}
                  />
                ))}
              </div>
            </div>
          )}

          {/* View all button */}
          {disabledModels.length > 10 && (
            <button
              onClick={() => setShowAllModels(true)}
              className="w-full py-2 text-xs text-nb-accent hover:underline"
            >
              View all {models.length} models
            </button>
          )}

          {/* Empty state */}
          {models.length === 0 && (
            <div className="text-sm text-nb-text-muted py-4 text-center">
              <button
                onClick={onFetchModels}
                disabled={fetching}
                className="text-nb-accent hover:underline disabled:opacity-50"
              >
                {fetching ? 'Fetching models...' : 'Click to fetch available models'}
              </button>
            </div>
          )}
        </>
      )}

      {/* All Models Modal */}
      {showAllModels && (
        <AllModelsModal
          models={models}
          defaultModel={defaultModel}
          onToggle={onToggle}
          onSetDefault={onSetDefault}
          onClose={() => setShowAllModels(false)}
        />
      )}
    </div>
  );
}

// ==================== Model Item ====================

function ModelItem({
  model,
  isDefault,
  onToggle,
  onSetDefault,
}: {
  model: AvailableModel;
  isDefault: boolean;
  onToggle: (modelId: string, enabled: boolean) => void;
  onSetDefault: (modelId: string) => void;
}) {
  return (
    <div className="flex items-center justify-between py-1.5 px-2 rounded hover:bg-nb-surface-2/50 group">
      <div className="flex items-center gap-2 min-w-0 flex-1">
        <Toggle
          checked={model.enabled}
          onChange={(enabled) => onToggle(model.id, enabled)}
        />
        <span className="text-sm text-nb-text truncate" title={model.id}>
          {model.name}
        </span>
        {model.is_custom && (
          <span className="text-[9px] bg-nb-accent/20 text-nb-accent px-1 py-0.5 rounded flex-shrink-0">
            Custom
          </span>
        )}
        {isDefault && (
          <Star size={12} className="text-yellow-500 fill-yellow-500 flex-shrink-0" />
        )}
      </div>
      
      {model.enabled && !isDefault && (
        <button
          onClick={() => onSetDefault(model.id)}
          className="text-[10px] text-nb-text-muted hover:text-nb-accent opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0"
        >
          Set default
        </button>
      )}
    </div>
  );
}

// ==================== All Models Modal ====================

function AllModelsModal({
  models,
  defaultModel,
  onToggle,
  onSetDefault,
  onClose,
}: {
  models: AvailableModel[];
  defaultModel: string;
  onToggle: (modelId: string, enabled: boolean) => void;
  onSetDefault: (modelId: string) => void;
  onClose: () => void;
}) {
  const [searchQuery, setSearchQuery] = useState('');
  
  const filteredModels = useMemo(() => {
    if (!searchQuery.trim()) return models;
    const q = searchQuery.toLowerCase();
    return models.filter(m => 
      m.id.toLowerCase().includes(q) || 
      m.name.toLowerCase().includes(q)
    );
  }, [models, searchQuery]);

  const enabledModels = filteredModels.filter(m => m.enabled);
  const disabledModels = filteredModels.filter(m => !m.enabled);

  return (
    <div className="fixed inset-0 z-[60]">
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />
      <div className="absolute left-1/2 top-1/2 w-[480px] max-w-[95vw] max-h-[80vh] -translate-x-1/2 -translate-y-1/2 rounded-xl border border-nb-border bg-nb-surface shadow-xl flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-nb-border px-4 py-3 flex-shrink-0">
          <div className="text-sm font-semibold text-nb-text">
            All Models ({models.length})
          </div>
          <button onClick={onClose} className="text-nb-text-muted hover:text-nb-text">
            <X size={18} />
          </button>
        </div>

        {/* Search */}
        <div className="px-4 py-3 border-b border-nb-border">
          <div className="relative">
            <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-nb-text-muted" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search models..."
              className="w-full rounded-lg border border-nb-border bg-nb-surface-2 pl-9 pr-3 py-2 text-sm text-nb-text outline-none focus:ring-2 focus:ring-nb-accent/50"
              autoFocus
            />
          </div>
        </div>

        {/* Model list */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {enabledModels.length > 0 && (
            <div className="space-y-1">
              <div className="text-[11px] font-medium text-nb-text-muted uppercase tracking-wider sticky top-0 bg-nb-surface py-1">
                Enabled ({enabledModels.length})
              </div>
              {enabledModels.map(model => (
                <ModelItem
                  key={model.id}
                  model={model}
                  isDefault={model.id === defaultModel}
                  onToggle={onToggle}
                  onSetDefault={onSetDefault}
                />
              ))}
            </div>
          )}

          {disabledModels.length > 0 && (
            <div className="space-y-1">
              <div className="text-[11px] font-medium text-nb-text-muted uppercase tracking-wider sticky top-0 bg-nb-surface py-1">
                Available ({disabledModels.length})
              </div>
              {disabledModels.map(model => (
                <ModelItem
                  key={model.id}
                  model={model}
                  isDefault={model.id === defaultModel}
                  onToggle={onToggle}
                  onSetDefault={onSetDefault}
                />
              ))}
            </div>
          )}

          {filteredModels.length === 0 && (
            <div className="text-sm text-nb-text-muted py-8 text-center">
              No models found
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ==================== API Key Card ====================

function ApiKeyCard({ 
  entry,
  models,
  defaultModel,
  onEdit, 
  onDelete, 
  onTest,
  onFetchModels,
  onToggleModel,
  onSetDefaultModel,
  onAddCustomModel,
  testing,
  fetching
}: { 
  entry: ApiKeyEntryPublic;
  models: AvailableModel[];
  defaultModel: string;
  onEdit: () => void;
  onDelete: () => void;
  onTest: () => void;
  onFetchModels: () => void;
  onToggleModel: (modelId: string, enabled: boolean) => void;
  onSetDefaultModel: (modelId: string) => void;
  onAddCustomModel: (apiKeyId: string, modelId: string, modelName: string) => void;
  testing: boolean;
  fetching: boolean;
}) {
  const providerInfo = PROVIDER_INFO[entry.provider];
  
  return (
    <div className="border border-nb-border rounded-lg p-4 space-y-2">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <span className="text-xl">{providerInfo.icon}</span>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium text-nb-text">{entry.name}</span>
              {entry.has_api_key ? (
                <span className="text-[10px] bg-green-500/20 text-green-400 px-1.5 py-0.5 rounded">
                  Connected
                </span>
              ) : (
                <span className="text-[10px] bg-yellow-500/20 text-yellow-400 px-1.5 py-0.5 rounded">
                  No Key
                </span>
              )}
            </div>
            <div className="text-xs text-nb-text-muted mt-0.5">
              {providerInfo.description}
              {entry.api_base && ` • ${entry.api_base}`}
            </div>
          </div>
        </div>
        
        {/* Actions */}
        <div className="flex items-center gap-1">
          <button
            onClick={onTest}
            disabled={testing || !entry.has_api_key}
            className="px-2 py-1 text-xs text-nb-text-muted hover:text-nb-text hover:bg-nb-surface-2 rounded disabled:opacity-50"
          >
            {testing ? '...' : 'Test'}
          </button>
          <button
            onClick={onEdit}
            className="px-2 py-1 text-xs text-nb-text-muted hover:text-nb-text hover:bg-nb-surface-2 rounded"
          >
            Edit
          </button>
          <button
            onClick={onDelete}
            className="px-2 py-1 text-xs text-red-400 hover:text-red-300 hover:bg-red-500/10 rounded"
          >
            Delete
          </button>
        </div>
      </div>
      
      {/* Models Section */}
      <ModelSection
        apiKeyId={entry.id}
        models={models}
        defaultModel={defaultModel}
        onToggle={onToggleModel}
        onSetDefault={onSetDefaultModel}
        onAddCustomModel={onAddCustomModel}
        onFetchModels={onFetchModels}
        fetching={fetching}
      />
    </div>
  );
}

// ==================== Add/Edit API Key Form ====================

function ApiKeyForm({ 
  mode,
  provider,
  initialValues,
  onProviderChange,
  onSubmit,
  onCancel,
  submitting
}: { 
  mode: 'add' | 'edit';
  provider: ProviderType;
  initialValues?: {
    name?: string;
    api_key?: string;
    api_base?: string;
    deployment_name?: string;
    api_version?: string;
  };
  onProviderChange?: (p: ProviderType) => void;
  onSubmit: (data: Record<string, string>) => void;
  onCancel: () => void;
  submitting: boolean;
}) {
  const providerInfo = PROVIDER_INFO[provider];
  
  const [name, setName] = useState(initialValues?.name || '');
  const [apiKey, setApiKey] = useState(initialValues?.api_key || '');
  const [apiBase, setApiBase] = useState(initialValues?.api_base || '');
  const [deploymentName, setDeploymentName] = useState(initialValues?.deployment_name || '');
  const [apiVersion, setApiVersion] = useState(initialValues?.api_version || '2024-02-01');

  const handleSubmit = () => {
    const data: Record<string, string> = {};
    if (name) data.name = name;
    if (apiKey) data.api_key = apiKey;
    if (apiBase) data.api_base = apiBase;
    if (deploymentName) data.deployment_name = deploymentName;
    if (apiVersion) data.api_version = apiVersion;
    onSubmit(data);
  };

  return (
    <div className="border border-nb-border rounded-lg p-4 space-y-4 bg-nb-surface/50">
      <div className="flex items-center gap-2">
        <span className="text-xl">{providerInfo.icon}</span>
        <span className="text-sm font-medium text-nb-text">
          {mode === 'add' ? 'Add New API Key' : 'Edit API Key'}
        </span>
      </div>

      {mode === 'add' && onProviderChange && (
        <div className="grid grid-cols-5 gap-2">
          {Object.entries(PROVIDER_INFO).map(([key, info]) => (
            <button
              key={key}
              onClick={() => onProviderChange(key as ProviderType)}
              className={`flex flex-col items-center gap-1 p-2 rounded-lg border transition-colors ${
                provider === key 
                  ? 'border-nb-accent bg-nb-accent/10' 
                  : 'border-nb-border hover:border-nb-text-muted'
              }`}
            >
              <span className="text-lg">{info.icon}</span>
              <span className="text-[10px] text-nb-text-muted">{info.name}</span>
            </button>
          ))}
        </div>
      )}

      <FormField
        label="Name"
        placeholder={`${providerInfo.name} #1`}
        value={name}
        onChange={setName}
      />

      {providerInfo.fields.includes('api_key') && (
        <FormField
          label="API Key"
          placeholder={mode === 'edit' ? 'Enter new key to update' : 'Enter your API key'}
          value={apiKey}
          onChange={setApiKey}
          type="password"
        />
      )}

      {providerInfo.fields.includes('api_base') && (
        <FormField
          label="Base URL (optional)"
          placeholder={providerInfo.defaultBaseUrl || 'https://your-endpoint.com'}
          value={apiBase}
          onChange={setApiBase}
        />
      )}

      {providerInfo.fields.includes('deployment_name') && (
        <FormField
          label="Deployment Name"
          placeholder="gpt-4o-deployment"
          value={deploymentName}
          onChange={setDeploymentName}
        />
      )}

      {providerInfo.fields.includes('api_version') && (
        <FormField
          label="API Version"
          placeholder="2024-02-01"
          value={apiVersion}
          onChange={setApiVersion}
        />
      )}

      {mode === 'add' && providerInfo.docsUrl && (
        <a 
          href={providerInfo.docsUrl} 
          target="_blank" 
          rel="noopener noreferrer"
          className="text-xs text-nb-accent hover:underline inline-block"
        >
          Get API Key →
        </a>
      )}

      <div className="flex justify-end gap-2 pt-2">
        <button
          onClick={onCancel}
          className="px-3 py-1.5 text-sm text-nb-text-muted hover:text-nb-text"
        >
          Cancel
        </button>
        <button
          onClick={handleSubmit}
          disabled={submitting}
          className="px-4 py-1.5 text-sm font-medium bg-nb-accent text-white rounded-lg hover:opacity-90 disabled:opacity-50"
        >
          {submitting ? 'Saving...' : (mode === 'add' ? 'Add' : 'Save')}
        </button>
      </div>
    </div>
  );
}

// ==================== Main Component ====================

export function SettingsModal(props: { open: boolean; onClose: () => void }) {
  const { open, onClose } = props;

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [info, setInfo] = useState<string | null>(null);

  // Config state
  const [config, setConfig] = useState<AppConfigPublic | null>(null);
  
  // Form state
  const [showAddForm, setShowAddForm] = useState(false);
  const [editingKeyId, setEditingKeyId] = useState<string | null>(null);
  const [newProvider, setNewProvider] = useState<ProviderType>('openai');
  const [submitting, setSubmitting] = useState(false);
  const [testingKeyId, setTestingKeyId] = useState<string | null>(null);
  const [fetchingKeyId, setFetchingKeyId] = useState<string | null>(null);

  // Load config
  const loadConfig = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const cfg = await invoke<AppConfigPublic>('get_app_config');
      setConfig(cfg);
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (open) {
      loadConfig();
    }
  }, [open, loadConfig]);

  // Get models for a specific API key
  const getModelsForKey = useCallback((apiKeyId: string) => {
    return config?.available_models.filter(m => m.api_key_id === apiKeyId) || [];
  }, [config]);

  if (!open) return null;

  // Handlers
  const handleAddKey = async (data: Record<string, string>) => {
    setSubmitting(true);
    setError(null);
    try {
      const result = await invoke<{ id: string }>('add_api_key', { 
        create: { 
          provider: newProvider, 
          ...data 
        } 
      });
      setShowAddForm(false);
      setNewProvider('openai');
      setInfo('API key added. Fetching models...');
      await loadConfig();
      
      // Auto-fetch models for the new key
      if (result?.id && data.api_key) {
        try {
          const modelsResult = await invoke<FetchModelsResult>('fetch_models_for_key', { apiKeyId: result.id });
          if (modelsResult.ok && modelsResult.models.length > 0) {
            await invoke('save_models_for_key', { apiKeyId: result.id, models: modelsResult.models });
            setInfo(`Added ${modelsResult.models.length} models.`);
            await loadConfig();
          }
        } catch {
          // Ignore fetch errors
        }
      }
    } catch (e) {
      setError(String(e));
    } finally {
      setSubmitting(false);
    }
  };

  const handleUpdateKey = async (id: string, data: Record<string, string>) => {
    setSubmitting(true);
    setError(null);
    try {
      await invoke('update_api_key', { update: { id, ...data } });
      setEditingKeyId(null);
      setInfo('API key updated');
      await loadConfig();
    } catch (e) {
      setError(String(e));
    } finally {
      setSubmitting(false);
    }
  };

  const handleDeleteKey = async (id: string) => {
    if (!confirm('Delete this API key and all its models?')) return;
    setError(null);
    try {
      await invoke('delete_api_key', { id });
      setInfo('API key deleted');
      await loadConfig();
    } catch (e) {
      setError(String(e));
    }
  };

  const handleTestKey = async (id: string) => {
    setTestingKeyId(id);
    setError(null);
    setInfo(null);
    try {
      const result = await invoke<TestConnectionResult>('test_api_key_connection', { apiKeyId: id });
      if (result.ok) {
        setInfo(`✓ ${result.message}`);
      } else {
        setError(`✗ ${result.message}`);
      }
    } catch (e) {
      setError(String(e));
    } finally {
      setTestingKeyId(null);
    }
  };

  const handleFetchModels = async (id: string) => {
    setFetchingKeyId(id);
    setError(null);
    setInfo(null);
    try {
      const result = await invoke<FetchModelsResult>('fetch_models_for_key', { apiKeyId: id });
      if (result.ok && result.models.length > 0) {
        await invoke('save_models_for_key', { apiKeyId: id, models: result.models });
        setInfo(`Found ${result.models.length} models`);
        await loadConfig();
      } else {
        setError(result.message || 'No models found');
      }
    } catch (e) {
      setError(String(e));
    } finally {
      setFetchingKeyId(null);
    }
  };

  const handleToggleModel = async (modelId: string, enabled: boolean) => {
    setError(null);
    try {
      await invoke('toggle_model', { toggle: { model_id: modelId, enabled } });
      await loadConfig();
    } catch (e) {
      setError(String(e));
    }
  };

  const handleSetDefaultModel = async (modelId: string) => {
    setError(null);
    try {
      await invoke('set_default_model', { modelId });
      await loadConfig();
    } catch (e) {
      setError(String(e));
    }
  };

  const handleAddCustomModel = async (apiKeyId: string, modelId: string, modelName: string) => {
    setError(null);
    try {
      // Add single custom model (enabled by default since user manually adds it)
      await invoke('save_models_for_key', { 
        apiKeyId, 
        models: [{ id: modelId, name: modelName }],
        append: true,
        isCustom: true  // Mark as custom model so it won't be removed on refresh
      });
      // Enable the custom model immediately after adding
      await invoke('toggle_model', { toggle: { model_id: modelId, enabled: true } });
      setInfo(`Added custom model: ${modelId}`);
      await loadConfig();
    } catch (e) {
      setError(String(e));
    }
  };

  const handleInitAgent = async () => {
    setError(null);
    setInfo(null);
    try {
      await invoke('init_agent_with_app_config');
      setInfo('Agent initialized!');
      setTimeout(() => onClose(), 800);
    } catch (e) {
      setError(String(e));
    }
  };

  // Count total enabled models
  const totalEnabledModels = config?.available_models.filter(m => m.enabled).length || 0;

  return (
    <div className="fixed inset-0 z-50">
      <div className="absolute inset-0 bg-black/40" onClick={onClose} />

      <div className="absolute left-1/2 top-1/2 w-[580px] max-w-[95vw] max-h-[90vh] -translate-x-1/2 -translate-y-1/2 rounded-xl border border-nb-border bg-nb-surface shadow-xl flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-nb-border px-4 py-3 flex-shrink-0">
          <div>
          <div className="text-sm font-semibold text-nb-text">Settings</div>
            <div className="text-xs text-nb-text-muted">
              {config?.api_keys.length || 0} API keys · {totalEnabledModels} models enabled
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-nb-text-muted hover:text-nb-text"
          >
            <X size={18} />
          </button>
        </div>

        {/* Content */}
        <div className="p-4 overflow-y-auto flex-1 space-y-4">
          {loading ? (
            <div className="text-sm text-nb-text-muted py-8 text-center">Loading...</div>
          ) : config ? (
            <>
              {/* API Keys with Models */}
              <div className="space-y-3">
                {config.api_keys.map((entry) => (
                  editingKeyId === entry.id ? (
                    <ApiKeyForm
                      key={entry.id}
                      mode="edit"
                      provider={entry.provider}
                      initialValues={{
                        name: entry.name,
                        api_base: entry.api_base || '',
                        deployment_name: entry.deployment_name || '',
                        api_version: entry.api_version || '',
                      }}
                      onSubmit={(data) => handleUpdateKey(entry.id, data)}
                      onCancel={() => setEditingKeyId(null)}
                      submitting={submitting}
                    />
                  ) : (
                    <ApiKeyCard
                      key={entry.id}
                      entry={entry}
                      models={getModelsForKey(entry.id)}
                      defaultModel={config.default_model}
                      onEdit={() => setEditingKeyId(entry.id)}
                      onDelete={() => handleDeleteKey(entry.id)}
                      onTest={() => handleTestKey(entry.id)}
                      onFetchModels={() => handleFetchModels(entry.id)}
                      onToggleModel={handleToggleModel}
                      onSetDefaultModel={handleSetDefaultModel}
                      onAddCustomModel={handleAddCustomModel}
                      testing={testingKeyId === entry.id}
                      fetching={fetchingKeyId === entry.id}
                    />
                  )
                ))}

                {config.api_keys.length === 0 && !showAddForm && (
                  <div className="text-center py-8">
                    <div className="text-nb-text-muted text-sm mb-2">No API keys configured</div>
                    <button
                      onClick={() => setShowAddForm(true)}
                      className="text-nb-accent text-sm hover:underline"
                    >
                      Add your first API key to get started
                    </button>
                  </div>
                )}
              </div>

              {/* Add API Key Section */}
              {showAddForm ? (
                <ApiKeyForm
                  mode="add"
                  provider={newProvider}
                  onProviderChange={setNewProvider}
                  onSubmit={handleAddKey}
                  onCancel={() => setShowAddForm(false)}
                  submitting={submitting}
                />
              ) : config.api_keys.length > 0 && (
                <button
                  onClick={() => setShowAddForm(true)}
                  className="w-full py-3 border border-dashed border-nb-border rounded-lg text-sm text-nb-text-muted hover:text-nb-text hover:border-nb-text-muted transition-colors flex items-center justify-center gap-2"
                >
                  <Plus size={14} />
                  Add API Key
                </button>
              )}

              {/* Messages */}
              {(error || info) && (
                <div className="space-y-2">
                  {error && (
                    <div className="rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-xs text-red-200">
                      {error}
                    </div>
                  )}
                  {info && (
                    <div className="rounded-lg border border-green-500/30 bg-green-500/10 px-3 py-2 text-xs text-green-200">
                      {info}
                    </div>
                  )}
                </div>
              )}
            </>
          ) : null}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between border-t border-nb-border px-4 py-3 flex-shrink-0">
          <div className="text-xs text-nb-text-muted">
            {config?.default_model && (
              <>Default: <span className="text-nb-text">{config.default_model}</span></>
            )}
          </div>
          <button
            onClick={handleInitAgent}
            disabled={!config || totalEnabledModels === 0}
            className="rounded-lg bg-nb-accent px-4 py-2 text-sm font-medium text-white hover:opacity-90 disabled:opacity-50"
          >
            Initialize Agent
          </button>
        </div>
      </div>
    </div>
  );
}
