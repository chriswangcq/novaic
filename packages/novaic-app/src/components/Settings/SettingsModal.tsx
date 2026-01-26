import { useEffect, useMemo, useState } from 'react';
import { invoke } from '@tauri-apps/api/core';

type AppConfigPublic = {
  version: number;
  llm_api_base: string;
  has_llm_api_key: boolean;
  llm_model: string;
  llm_max_tokens?: number | null;
  api_style: string;
  enable_prefix_caching: boolean;
  enable_thinking: boolean;
  max_iterations: number;
  visible_shell: boolean;
};

type AppConfigUpdate = {
  llm_api_base: string;
  llm_api_key?: string | null;
  llm_model: string;
  llm_max_tokens?: number | null;
  api_style?: string;
  enable_prefix_caching?: boolean;
  enable_thinking?: boolean;
  max_iterations?: number;
  visible_shell?: boolean;
};

type TestConnectionResult = {
  ok: boolean;
  message: string;
};

type FetchModelsResult = {
  ok: boolean;
  models: string[];
  message: string;
};

export function SettingsModal(props: { open: boolean; onClose: () => void }) {
  const { open, onClose } = props;

  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [fetchingModels, setFetchingModels] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [info, setInfo] = useState<string | null>(null);

  const [apiBase, setApiBase] = useState('https://api.nuwaapi.com');
  const [apiKey, setApiKey] = useState('');
  const [model, setModel] = useState('gpt-5');
  const [maxTokens, setMaxTokens] = useState<string>('4096');
  const [hasKey, setHasKey] = useState(false);
  const [modelList, setModelList] = useState<string[]>([]);
  
  // API Style settings
  const [apiStyle, setApiStyle] = useState<'chat_completions' | 'responses'>('chat_completions');
  const [enablePrefixCaching, setEnablePrefixCaching] = useState(true);
  const [enableThinking, setEnableThinking] = useState(false);
  
  // Agent settings
  const [maxIterations, setMaxIterations] = useState<string>('20');
  const [visibleShell, setVisibleShell] = useState(false);

  const maxTokensNum = useMemo(() => {
    const n = Number(maxTokens);
    if (!Number.isFinite(n) || n <= 0) return null;
    return Math.floor(n);
  }, [maxTokens]);

  const maxIterationsNum = useMemo(() => {
    const n = Number(maxIterations);
    if (!Number.isFinite(n) || n <= 0) return 20;
    return Math.min(Math.max(Math.floor(n), 1), 100); // Clamp 1-100
  }, [maxIterations]);

  useEffect(() => {
    if (!open) return;

    setLoading(true);
    setError(null);
    setInfo(null);

    invoke<AppConfigPublic>('get_app_config')
      .then((cfg) => {
        setApiBase(cfg.llm_api_base || 'https://api.nuwaapi.com');
        setModel(cfg.llm_model || 'gpt-5');
        setMaxTokens(String(cfg.llm_max_tokens ?? 4096));
        setHasKey(Boolean(cfg.has_llm_api_key));
        setApiKey('');
        // API Style settings
        setApiStyle((cfg.api_style as 'chat_completions' | 'responses') || 'chat_completions');
        setEnablePrefixCaching(cfg.enable_prefix_caching ?? true);
        setEnableThinking(cfg.enable_thinking ?? false);
        // Agent settings
        setMaxIterations(String(cfg.max_iterations ?? 20));
        setVisibleShell(cfg.visible_shell ?? false);
      })
      .catch((e) => setError(String(e)))
      .finally(() => setLoading(false));
  }, [open]);

  if (!open) return null;

  const onSave = async () => {
    setSaving(true);
    setError(null);
    setInfo(null);

    const update: AppConfigUpdate = {
      llm_api_base: apiBase,
      llm_model: model,
      llm_max_tokens: maxTokensNum,
      api_style: apiStyle,
      enable_prefix_caching: enablePrefixCaching,
      enable_thinking: enableThinking,
      max_iterations: maxIterationsNum,
      visible_shell: visibleShell,
    };

    // If user typed a key, overwrite; otherwise keep existing key.
    if (apiKey.trim().length > 0) update.llm_api_key = apiKey;

    try {
      const cfg = await invoke<AppConfigPublic>('set_app_config', { update });
      setHasKey(Boolean(cfg.has_llm_api_key));
      setApiKey('');
      setInfo('Saved.');
      // Re-init agent with local config if possible
      await invoke('init_agent_with_app_config');
      setInfo('Saved and agent initialized.');
    } catch (e) {
      setError(String(e));
    } finally {
      setSaving(false);
    }
  };

  const onTest = async () => {
    setTesting(true);
    setError(null);
    setInfo(null);
    try {
      const res = await invoke<TestConnectionResult>('test_llm_connection');
      if (res.ok) setInfo(res.message);
      else setError(res.message);
    } catch (e) {
      setError(String(e));
    } finally {
      setTesting(false);
    }
  };

  const onFetchModels = async () => {
    setFetchingModels(true);
    setError(null);
    setInfo(null);

    // Use the input key if provided, otherwise we need to tell user to enter key
    const keyToUse = apiKey.trim() || '';
    
    if (!apiBase.trim()) {
      setError('Please enter API Base URL first');
      setFetchingModels(false);
      return;
    }

    if (!keyToUse && !hasKey) {
      setError('Please enter API Key first');
      setFetchingModels(false);
      return;
    }

    try {
      // If user hasn't entered a new key but has one configured, we need to read from config
      let effectiveKey = keyToUse;
      if (!effectiveKey && hasKey) {
        // We can't access the stored key from frontend, so we need the user to re-enter it
        setError('Please re-enter your API Key to fetch models');
        setFetchingModels(false);
        return;
      }

      const res = await invoke<FetchModelsResult>('fetch_models', {
        apiBase: apiBase.trim(),
        apiKey: effectiveKey,
      });

      if (res.ok) {
        setModelList(res.models);
        setInfo(`Found ${res.models.length} models`);
        // If current model is not in the list and list is not empty, select the first one
        if (res.models.length > 0 && !res.models.includes(model)) {
          setModel(res.models[0]);
        }
      } else {
        setError(res.message);
      }
    } catch (e) {
      setError(String(e));
    } finally {
      setFetchingModels(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50">
      <div className="absolute inset-0 bg-black/40" onClick={onClose} />

      <div className="absolute left-1/2 top-1/2 w-[720px] max-w-[95vw] -translate-x-1/2 -translate-y-1/2 rounded-xl border border-nb-border bg-nb-surface shadow-xl">
        <div className="flex items-center justify-between border-b border-nb-border px-4 py-3">
          <div className="text-sm font-semibold text-nb-text">Settings</div>
          <button
            onClick={onClose}
            className="rounded-lg px-2 py-1 text-xs text-nb-text-muted hover:bg-nb-surface-2"
          >
            Close
          </button>
        </div>

        <div className="p-4">
          {loading ? (
            <div className="text-sm text-nb-text-muted">Loading...</div>
          ) : (
            <>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <div className="text-xs font-medium text-nb-text-muted mb-1">LLM API Base</div>
                  <input
                    value={apiBase}
                    onChange={(e) => setApiBase(e.target.value)}
                    className="w-full rounded-lg border border-nb-border bg-nb-surface-2 px-3 py-2 text-sm text-nb-text outline-none focus:ring-2 focus:ring-nb-accent/50"
                    placeholder="https://api.nuwaapi.com"
                  />
                </div>

                <div>
                  <div className="text-xs font-medium text-nb-text-muted mb-1">Model</div>
                  <div className="flex gap-2">
                    {modelList.length > 0 ? (
                      <select
                        value={model}
                        onChange={(e) => setModel(e.target.value)}
                        className="flex-1 rounded-lg border border-nb-border bg-nb-surface-2 px-3 py-2 text-sm text-nb-text outline-none focus:ring-2 focus:ring-nb-accent/50"
                      >
                        {modelList.map((m) => (
                          <option key={m} value={m}>
                            {m}
                          </option>
                        ))}
                      </select>
                    ) : (
                      <input
                        value={model}
                        onChange={(e) => setModel(e.target.value)}
                        className="flex-1 rounded-lg border border-nb-border bg-nb-surface-2 px-3 py-2 text-sm text-nb-text outline-none focus:ring-2 focus:ring-nb-accent/50"
                        placeholder="gpt-5"
                      />
                    )}
                    <button
                      onClick={onFetchModels}
                      disabled={loading || saving || testing || fetchingModels}
                      className="rounded-lg border border-nb-border bg-nb-surface-2 px-3 py-2 text-sm text-nb-text hover:bg-nb-surface disabled:opacity-50 whitespace-nowrap"
                      title="Fetch available models from API"
                    >
                      {fetchingModels ? '...' : '↻'}
                    </button>
                  </div>
                  <div className="mt-1 text-[11px] text-nb-text-muted">
                    {modelList.length > 0 
                      ? `${modelList.length} models available` 
                      : 'Enter API Base & Key, then click ↻ to load models'}
                  </div>
                </div>

                <div>
                  <div className="text-xs font-medium text-nb-text-muted mb-1">Max tokens</div>
                  <input
                    value={maxTokens}
                    onChange={(e) => setMaxTokens(e.target.value)}
                    className="w-full rounded-lg border border-nb-border bg-nb-surface-2 px-3 py-2 text-sm text-nb-text outline-none focus:ring-2 focus:ring-nb-accent/50"
                    placeholder="4096"
                    inputMode="numeric"
                  />
                </div>

                <div>
                  <div className="text-xs font-medium text-nb-text-muted mb-1">LLM API Key</div>
                  <input
                    value={apiKey}
                    onChange={(e) => setApiKey(e.target.value)}
                    className="w-full rounded-lg border border-nb-border bg-nb-surface-2 px-3 py-2 text-sm text-nb-text outline-none focus:ring-2 focus:ring-nb-accent/50"
                    placeholder={hasKey ? 'Configured (enter new key to overwrite)' : 'Enter your API key'}
                    type="password"
                    autoComplete="off"
                  />
                  <div className="mt-1 text-[11px] text-nb-text-muted">
                    Stored locally on this machine. Current key: {hasKey ? 'configured' : 'not set'}.
                  </div>
                </div>
              </div>

              {/* API Style Settings */}
              <div className="mt-4 pt-4 border-t border-nb-border">
                <div className="text-xs font-semibold text-nb-text-muted mb-3">API Style</div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <div className="text-xs font-medium text-nb-text-muted mb-1">API Mode</div>
                    <select
                      value={apiStyle}
                      onChange={(e) => setApiStyle(e.target.value as 'chat_completions' | 'responses')}
                      className="w-full rounded-lg border border-nb-border bg-nb-surface-2 px-3 py-2 text-sm text-nb-text outline-none focus:ring-2 focus:ring-nb-accent/50"
                    >
                      <option value="chat_completions">Chat Completions (OpenAI)</option>
                      <option value="responses">Responses (Doubao)</option>
                    </select>
                    <div className="mt-1 text-[11px] text-nb-text-muted">
                      {apiStyle === 'responses' 
                        ? 'Uses previous_response_id for conversation chaining' 
                        : 'Sends full message history each request'}
                    </div>
                  </div>

                  {apiStyle === 'responses' && (
                    <div className="space-y-3">
                      <label className="flex items-center gap-2 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={enablePrefixCaching}
                          onChange={(e) => setEnablePrefixCaching(e.target.checked)}
                          className="w-4 h-4 rounded border-nb-border bg-nb-surface-2 text-nb-accent focus:ring-nb-accent/50"
                        />
                        <span className="text-sm text-nb-text">Enable Prefix Caching</span>
                      </label>
                      <label className="flex items-center gap-2 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={enableThinking}
                          onChange={(e) => setEnableThinking(e.target.checked)}
                          className="w-4 h-4 rounded border-nb-border bg-nb-surface-2 text-nb-accent focus:ring-nb-accent/50"
                        />
                        <span className="text-sm text-nb-text">Enable Thinking Mode</span>
                      </label>
                    </div>
                  )}
                </div>
              </div>

              {/* Agent Settings */}
              <div className="mt-4 pt-4 border-t border-nb-border">
                <div className="text-xs font-semibold text-nb-text-muted mb-3">Agent Settings</div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <div className="text-xs font-medium text-nb-text-muted mb-1">Max Iterations</div>
                    <input
                      value={maxIterations}
                      onChange={(e) => setMaxIterations(e.target.value)}
                      className="w-full rounded-lg border border-nb-border bg-nb-surface-2 px-3 py-2 text-sm text-nb-text outline-none focus:ring-2 focus:ring-nb-accent/50"
                      placeholder="20"
                      inputMode="numeric"
                      min="1"
                      max="100"
                    />
                    <div className="mt-1 text-[11px] text-nb-text-muted">
                      Maximum tool calls per task (1-100). Increase for complex tasks.
                    </div>
                  </div>
                  <div className="flex items-start pt-5">
                    <label className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={visibleShell}
                        onChange={(e) => setVisibleShell(e.target.checked)}
                        className="w-4 h-4 rounded border-nb-border bg-nb-surface-2 text-nb-accent focus:ring-nb-accent/50"
                      />
                      <div>
                        <span className="text-sm text-nb-text">Show Shell in Desktop</span>
                        <div className="text-[11px] text-nb-text-muted">
                          Display terminal window on VNC when running commands
                        </div>
                      </div>
                    </label>
                  </div>
                </div>
              </div>

              {(error || info) && (
                <div className="mt-4">
                  {error && (
                    <div className="rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-xs text-red-200">
                      {error}
                    </div>
                  )}
                  {info && (
                    <div className="rounded-lg border border-nb-border bg-nb-surface-2 px-3 py-2 text-xs text-nb-text">
                      {info}
                    </div>
                  )}
                </div>
              )}
            </>
          )}
        </div>

        <div className="flex items-center justify-between border-t border-nb-border px-4 py-3">
          <button
            onClick={onTest}
            disabled={loading || saving || testing}
            className="rounded-lg border border-nb-border bg-nb-surface-2 px-3 py-2 text-sm text-nb-text hover:bg-nb-surface disabled:opacity-50"
          >
            {testing ? 'Testing...' : 'Test connection'}
          </button>

          <button
            onClick={onSave}
            disabled={loading || saving || testing}
            className="rounded-lg bg-nb-accent px-4 py-2 text-sm font-medium text-white hover:opacity-90 disabled:opacity-50"
          >
            {saving ? 'Saving...' : 'Save'}
          </button>
        </div>
      </div>
    </div>
  );
}


