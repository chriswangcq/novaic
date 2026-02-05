import { useEffect, useState, useCallback, useMemo } from 'react';
import { ChevronDown, ChevronRight, Search, Plus, X, Trash2, Database, HardDrive } from 'lucide-react';
import { api, type ApiKeyInfo, type CandidateModel } from '../../services/api';

// ==================== Tab Types ====================

type SettingsTab = 'models' | 'cache';

// ==================== Types ====================

type ProviderType = 'openai' | 'anthropic' | 'google' | 'azure' | 'openai_compatible';

// Use ApiKeyInfo from api.ts but cast provider to our local ProviderType for convenience
type ApiKeyEntryPublic = Omit<ApiKeyInfo, 'provider'> & { provider: ProviderType };

// Re-export CandidateModel with ProviderType
type LocalCandidateModel = Omit<CandidateModel, 'provider'> & { provider: ProviderType };

// App config with local types
interface AppConfigLocal {
  version: number;
  api_keys: ApiKeyEntryPublic[];
  candidate_models: LocalCandidateModel[];
  max_tokens: number;
  max_iterations: number;
  visible_shell: boolean;
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

function Toggle({ checked, onChange, disabled }: { checked: boolean; onChange: (v: boolean) => void | Promise<void>; disabled?: boolean }) {
  const [loading, setLoading] = useState(false);
  
  const handleClick = async (e: React.MouseEvent) => {
    // Prevent event from bubbling up to parent elements
    e.stopPropagation();
    
    if (disabled || loading) return;
    
    const result = onChange(!checked);
    // Handle both sync and async onChange
    if (result instanceof Promise) {
      setLoading(true);
      try {
        await result;
      } catch (error) {
        console.error('Toggle onChange error:', error);
        // Error is already handled in the parent's try-catch
      } finally {
        setLoading(false);
      }
    }
  };
  
  return (
    <button
      onClick={handleClick}
      disabled={disabled || loading}
      className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors flex-shrink-0 ${
        checked ? 'bg-green-500' : 'bg-nb-surface-2'
      } ${(disabled || loading) ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
    >
      <span
        className={`inline-block h-3.5 w-3.5 transform rounded-full bg-white transition-transform ${
          checked ? 'translate-x-5' : 'translate-x-1'
        } ${loading ? 'animate-pulse' : ''}`}
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
  onToggle,
  onAddCustomModel,
  onDeleteModel,
  onFetchModels,
  fetching,
}: {
  apiKeyId: string;
  models: LocalCandidateModel[];
  onToggle: (modelId: string, apiKeyId: string, enabled: boolean) => void | Promise<void>;
  onAddCustomModel: (apiKeyId: string, modelId: string, modelName: string) => void;
  onDeleteModel?: (modelId: string, apiKeyId: string) => void;
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
                key={`${model.api_key_id}:${model.id}`}
                model={model}
                onToggle={onToggle}
                onDelete={onDeleteModel}
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
                    key={`${model.api_key_id}:${model.id}`}
                    model={model}
                    onToggle={onToggle}
                    onDelete={onDeleteModel}
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
                    key={`${model.api_key_id}:${model.id}`}
                    model={model}
                    onToggle={onToggle}
                    onDelete={onDeleteModel}
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
          onToggle={onToggle}
          onDelete={onDeleteModel}
          onClose={() => setShowAllModels(false)}
        />
      )}
    </div>
  );
}

// ==================== Model Item ====================

function ModelItem({
  model,
  onToggle,
  onDelete,
}: {
  model: LocalCandidateModel;
  onToggle: (modelId: string, apiKeyId: string, enabled: boolean) => void | Promise<void>;
  onDelete?: (modelId: string, apiKeyId: string) => void;
}) {
  return (
    <div className="flex items-center justify-between py-1.5 px-2 rounded hover:bg-nb-surface-2/50 group">
      <div className="flex items-center gap-2 min-w-0 flex-1">
        <Toggle
          checked={model.enabled}
          onChange={(enabled) => onToggle(model.id, model.api_key_id, enabled)}
        />
        <span className="text-sm text-nb-text truncate" title={model.id}>
          {model.name}
        </span>
        {model.is_custom && (
          <span className="text-[9px] bg-nb-accent/20 text-nb-accent px-1 py-0.5 rounded flex-shrink-0">
            Custom
          </span>
        )}
      </div>
      
      {model.is_custom && onDelete && (
        <button
          onClick={(e) => {
            e.stopPropagation();
            onDelete(model.id, model.api_key_id);
          }}
          className="text-[10px] text-red-400 hover:text-red-300 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0"
        >
          Delete
        </button>
      )}
    </div>
  );
}

// ==================== All Models Modal ====================

function AllModelsModal({
  models,
  onToggle,
  onDelete,
  onClose,
}: {
  models: LocalCandidateModel[];
  onToggle: (modelId: string, apiKeyId: string, enabled: boolean) => void | Promise<void>;
  onDelete?: (modelId: string, apiKeyId: string) => void;
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
                  key={`${model.api_key_id}:${model.id}`}
                  model={model}
                  onToggle={onToggle}
                  onDelete={onDelete}
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
                  key={`${model.api_key_id}:${model.id}`}
                  model={model}
                  onToggle={onToggle}
                  onDelete={onDelete}
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
  onEdit, 
  onDelete, 
  onTest,
  onFetchModels,
  onToggleModel,
  onAddCustomModel,
  onDeleteModel,
  testing,
  fetching
}: { 
  entry: ApiKeyEntryPublic;
  models: LocalCandidateModel[];
  onEdit: () => void;
  onDelete: () => void;
  onTest: () => void;
  onFetchModels: () => void;
  onToggleModel: (modelId: string, apiKeyId: string, enabled: boolean) => void | Promise<void>;
  onAddCustomModel: (apiKeyId: string, modelId: string, modelName: string) => void;
  onDeleteModel?: (modelId: string, apiKeyId: string) => void;
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
        onToggle={onToggleModel}
        onAddCustomModel={onAddCustomModel}
        onDeleteModel={onDeleteModel}
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

  // Tab state
  const [activeTab, setActiveTab] = useState<SettingsTab>('models');

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [info, setInfo] = useState<string | null>(null);

  // Config state
  const [config, setConfig] = useState<AppConfigLocal | null>(null);
  
  // Form state
  const [showAddForm, setShowAddForm] = useState(false);
  const [editingKeyId, setEditingKeyId] = useState<string | null>(null);
  const [newProvider, setNewProvider] = useState<ProviderType>('openai');
  const [submitting, setSubmitting] = useState(false);
  const [testingKeyId, setTestingKeyId] = useState<string | null>(null);
  const [fetchingKeyId, setFetchingKeyId] = useState<string | null>(null);

  // Cleanup state
  const [cleaning, setCleaning] = useState(false);
  const [cleanupResult, setCleanupResult] = useState<{
    logs: number;
    metadata_files: number;
    temp_files: number;
    empty_dirs: number;
    database_vacuumed: boolean;
    orphaned_agents: number;
    vm_images: number;
  } | null>(null);

  // Load config
  const loadConfig = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const cfg = await api.getConfig() as unknown as AppConfigLocal;
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
    return config?.candidate_models?.filter(m => m.api_key_id === apiKeyId) || [];
  }, [config]);

  if (!open) return null;

  // Handlers
  const handleAddKey = async (data: Record<string, string>) => {
    setSubmitting(true);
    setError(null);
    try {
      const result = await api.addApiKey({ 
        provider: newProvider, 
        ...data 
      });
      setShowAddForm(false);
      setNewProvider('openai');
      setInfo('API key added. Fetching models...');
      await loadConfig();
      
      // Auto-fetch models for the new key
      if (result?.id && data.api_key) {
        try {
          const models = await api.fetchModelsForKey(result.id);
          if (models.length > 0) {
            await api.saveModelsForKey(result.id, models);
            setInfo(`Added ${models.length} models.`);
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
      await api.updateApiKey(id, data);
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
      await api.deleteApiKey(id);
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
      const result = await api.testApiKeyConnection(id);
      if (result.success) {
        setInfo('✓ Connection successful');
      } else {
        setError(`✗ ${result.error || 'Connection failed'}`);
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
      const models = await api.fetchModelsForKey(id);
      if (models.length > 0) {
        await api.saveModelsForKey(id, models);
        setInfo(`Found ${models.length} models`);
        await loadConfig();
      } else {
        setError('No models found');
      }
    } catch (e) {
      setError(String(e));
    } finally {
      setFetchingKeyId(null);
    }
  };

  const handleToggleModel = async (modelId: string, apiKeyId: string, enabled: boolean) => {
    setError(null);
    try {
      await api.toggleModel(modelId, apiKeyId, enabled);
      await loadConfig();
    } catch (e) {
      setError(String(e));
    }
  };

  const handleDeleteModel = async (modelId: string, apiKeyId: string) => {
    if (!confirm(`Delete custom model "${modelId}"?`)) return;
    setError(null);
    try {
      await api.deleteModel(apiKeyId, modelId);
      await loadConfig();
    } catch (e) {
      setError(String(e));
    }
  };

  const handleAddCustomModel = async (apiKeyId: string, modelId: string, modelName: string) => {
    setError(null);
    try {
      await api.addModel(apiKeyId, modelId, modelName);
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
      await api.initAgent();
      setInfo('Agent initialized!');
      setTimeout(() => onClose(), 800);
    } catch (e) {
      setError(String(e));
    }
  };

  // Cleanup handlers
  const handleCleanup = async (deep: boolean, cleanVmCache: boolean) => {
    setCleaning(true);
    setError(null);
    setInfo(null);
    setCleanupResult(null);
    try {
      const result = await api.cleanupGarbage({ deep, clean_vm_cache: cleanVmCache });
      setCleanupResult(result.details);
      setInfo(result.message);
    } catch (e) {
      setError(String(e));
    } finally {
      setCleaning(false);
    }
  };

  // Count total enabled models
  const totalEnabledModels = config?.candidate_models?.filter(m => m.enabled).length || 0;

  return (
    <div className="fixed inset-0 z-50">
      <div className="absolute inset-0 bg-black/40" onClick={onClose} />

      <div className="absolute left-1/2 top-1/2 w-[720px] max-w-[95vw] max-h-[90vh] -translate-x-1/2 -translate-y-1/2 rounded-xl border border-nb-border bg-nb-surface shadow-xl flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-nb-border px-4 py-3 flex-shrink-0">
          <div className="text-sm font-semibold text-nb-text">Settings</div>
          <button
            onClick={onClose}
            className="text-nb-text-muted hover:text-nb-text"
          >
            <X size={18} />
          </button>
        </div>

        {/* Main Content with Sidebar */}
        <div className="flex flex-1 overflow-hidden">
          {/* Left Sidebar - Tab Navigation */}
          <div className="w-40 border-r border-nb-border flex flex-col py-2 flex-shrink-0">
            <button
              onClick={() => setActiveTab('models')}
              className={`flex items-center gap-2 px-4 py-2.5 text-sm transition-colors ${
                activeTab === 'models'
                  ? 'bg-nb-accent/10 text-nb-accent border-r-2 border-nb-accent'
                  : 'text-nb-text-muted hover:text-nb-text hover:bg-nb-surface-2'
              }`}
            >
              <Database size={16} />
              <span>Models</span>
            </button>
            <button
              onClick={() => setActiveTab('cache')}
              className={`flex items-center gap-2 px-4 py-2.5 text-sm transition-colors ${
                activeTab === 'cache'
                  ? 'bg-nb-accent/10 text-nb-accent border-r-2 border-nb-accent'
                  : 'text-nb-text-muted hover:text-nb-text hover:bg-nb-surface-2'
              }`}
            >
              <Trash2 size={16} />
              <span>清理缓存</span>
            </button>
          </div>

          {/* Right Content Area */}
          <div className="flex-1 flex flex-col overflow-hidden">
            {/* Models Tab */}
            {activeTab === 'models' && (
              <>
                {/* Tab Header */}
                <div className="px-4 py-3 border-b border-nb-border flex-shrink-0">
                  <div className="text-xs text-nb-text-muted">
                    {config?.api_keys.length || 0} API keys · {totalEnabledModels} models enabled
                  </div>
                </div>

                {/* Tab Content */}
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
                              onEdit={() => setEditingKeyId(entry.id)}
                              onDelete={() => handleDeleteKey(entry.id)}
                              onTest={() => handleTestKey(entry.id)}
                              onFetchModels={() => handleFetchModels(entry.id)}
                              onToggleModel={handleToggleModel}
                              onAddCustomModel={handleAddCustomModel}
                              onDeleteModel={handleDeleteModel}
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
                    </>
                  ) : null}
                </div>

                {/* Tab Footer */}
                <div className="flex items-center justify-between border-t border-nb-border px-4 py-3 flex-shrink-0">
                  {/* Messages */}
                  <div className="flex-1 mr-4">
                    {error && (
                      <div className="rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-1.5 text-xs text-red-200">
                        {error}
                      </div>
                    )}
                    {info && !error && (
                      <div className="rounded-lg border border-green-500/30 bg-green-500/10 px-3 py-1.5 text-xs text-green-200">
                        {info}
                      </div>
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
              </>
            )}

            {/* Cache Cleanup Tab */}
            {activeTab === 'cache' && (
              <>
                {/* Tab Header */}
                <div className="px-4 py-3 border-b border-nb-border flex-shrink-0">
                  <div className="text-xs text-nb-text-muted">
                    清理临时文件、日志和虚拟机缓存
                  </div>
                </div>

                {/* Tab Content */}
                <div className="p-4 overflow-y-auto flex-1 space-y-4">
                  {/* Quick Cleanup Card */}
                  <div className="border border-nb-border rounded-lg p-4 space-y-3">
                    <div className="flex items-start gap-3">
                      <div className="p-2 rounded-lg bg-nb-surface-2">
                        <Trash2 size={20} className="text-nb-text-muted" />
                      </div>
                      <div className="flex-1">
                        <div className="text-sm font-medium text-nb-text">普通清理</div>
                        <div className="text-xs text-nb-text-muted mt-1">
                          清理 7 天前的日志、临时文件 (.tmp, .bak)、系统元数据文件 (.DS_Store) 和空目录
                        </div>
                      </div>
                    </div>
                    <button
                      onClick={() => handleCleanup(false, false)}
                      disabled={cleaning}
                      className="w-full py-2 rounded-lg border border-nb-border text-sm text-nb-text hover:bg-nb-surface-2 transition-colors disabled:opacity-50"
                    >
                      {cleaning ? '清理中...' : '执行普通清理'}
                    </button>
                  </div>

                  {/* Deep Cleanup Card */}
                  <div className="border border-orange-500/30 rounded-lg p-4 space-y-3 bg-orange-500/5">
                    <div className="flex items-start gap-3">
                      <div className="p-2 rounded-lg bg-orange-500/10">
                        <HardDrive size={20} className="text-orange-400" />
                      </div>
                      <div className="flex-1">
                        <div className="text-sm font-medium text-nb-text">深度清理</div>
                        <div className="text-xs text-nb-text-muted mt-1">
                          包含普通清理的所有操作，另外还会：
                        </div>
                        <ul className="text-xs text-nb-text-muted mt-2 space-y-1 list-disc list-inside">
                          <li>清理所有日志文件（不保留近期）</li>
                          <li>清理孤立的 Agent 数据</li>
                          <li>优化数据库（VACUUM）</li>
                          <li>清理虚拟机基础镜像缓存（需重新下载）</li>
                        </ul>
                      </div>
                    </div>
                    <button
                      onClick={() => handleCleanup(true, true)}
                      disabled={cleaning}
                      className="w-full py-2 rounded-lg bg-orange-500/20 border border-orange-500/30 text-sm text-orange-300 hover:bg-orange-500/30 transition-colors disabled:opacity-50"
                    >
                      {cleaning ? '清理中...' : '执行深度清理'}
                    </button>
                  </div>

                  {/* Cleanup Result */}
                  {cleanupResult && (
                    <div className="border border-green-500/30 rounded-lg p-4 bg-green-500/5">
                      <div className="text-sm font-medium text-green-400 mb-3">清理完成</div>
                      <div className="grid grid-cols-2 gap-2 text-xs">
                        <div className="flex justify-between">
                          <span className="text-nb-text-muted">日志文件</span>
                          <span className="text-nb-text">{cleanupResult.logs} 个</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-nb-text-muted">元数据文件</span>
                          <span className="text-nb-text">{cleanupResult.metadata_files} 个</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-nb-text-muted">临时文件</span>
                          <span className="text-nb-text">{cleanupResult.temp_files} 个</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-nb-text-muted">空目录</span>
                          <span className="text-nb-text">{cleanupResult.empty_dirs} 个</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-nb-text-muted">孤立 Agent</span>
                          <span className="text-nb-text">{cleanupResult.orphaned_agents} 个</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-nb-text-muted">VM 镜像</span>
                          <span className="text-nb-text">{cleanupResult.vm_images} 个</span>
                        </div>
                        <div className="flex justify-between col-span-2">
                          <span className="text-nb-text-muted">数据库优化</span>
                          <span className="text-nb-text">{cleanupResult.database_vacuumed ? '✓ 已完成' : '未执行'}</span>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Error/Info Messages */}
                  {error && (
                    <div className="rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-xs text-red-200">
                      {error}
                    </div>
                  )}
                  {info && !cleanupResult && (
                    <div className="rounded-lg border border-green-500/30 bg-green-500/10 px-3 py-2 text-xs text-green-200">
                      {info}
                    </div>
                  )}
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
