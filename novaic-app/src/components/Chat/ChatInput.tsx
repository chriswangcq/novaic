import { useState, useRef, KeyboardEvent, useEffect, useMemo, useCallback } from 'react';
import { Loader2, StopCircle, ArrowUp, ChevronDown, Bot, MessageSquare, X } from 'lucide-react';
import { useAppStore } from '../../store';
import { ChatMode, AvailableModel } from '../../types';

interface ChatInputProps {
  onSend: (content: string) => void;
  onStop?: () => void;
  isLoading: boolean;
  placeholder?: string;
}

// Mode display info
const MODE_INFO: Record<ChatMode, { icon: typeof Bot; label: string; description: string }> = {
  agent: { icon: Bot, label: 'Agent', description: 'Can use tools and execute actions' },
  chat: { icon: MessageSquare, label: 'Chat', description: 'Simple conversation mode' },
};

export function ChatInput({ 
  onSend, 
  onStop, 
  isLoading, 
  placeholder = "Ask anything..." 
}: ChatInputProps) {
  const [content, setContent] = useState('');
  const [isFocused, setIsFocused] = useState(false);
  const [showModelDropdown, setShowModelDropdown] = useState(false);
  const [showModeDropdown, setShowModeDropdown] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const modelDropdownRef = useRef<HTMLDivElement>(null);
  const modeDropdownRef = useRef<HTMLDivElement>(null);

  const { 
    availableModels,
    apiKeys,
    selectedModel, 
    setSelectedModel,
    chatMode,
    setChatMode,
    loadModelsFromConfig
  } = useAppStore();

  // Fetch latest models when dropdown opens
  const handleOpenModelDropdown = useCallback(async () => {
    if (!showModelDropdown) {
      // Fetch latest models from config before showing dropdown
      await loadModelsFromConfig();
    }
    setShowModelDropdown(!showModelDropdown);
  }, [showModelDropdown, loadModelsFromConfig]);

  // Focus on mount
  useEffect(() => {
    textareaRef.current?.focus();
  }, []);

  // Close dropdowns when clicking outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (modelDropdownRef.current && !modelDropdownRef.current.contains(e.target as Node)) {
        setShowModelDropdown(false);
      }
      if (modeDropdownRef.current && !modeDropdownRef.current.contains(e.target as Node)) {
        setShowModeDropdown(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Create API Key name map
  const apiKeyNameMap = useMemo(() => {
    const map: Record<string, string> = {};
    apiKeys.forEach(k => { map[k.id] = k.name; });
    return map;
  }, [apiKeys]);

  // Get current model info
  const currentModel = availableModels.find(m => m.id === selectedModel);
  const displayModelName = currentModel?.name || selectedModel || 'Select model';

  // Group models by API Key (not provider)
  const modelsByApiKey = useMemo(() => {
    const grouped: Record<string, AvailableModel[]> = {};
    availableModels.forEach(model => {
      const keyId = model.api_key_id;
      if (!grouped[keyId]) grouped[keyId] = [];
      grouped[keyId].push(model);
    });
    return grouped;
  }, [availableModels]);

  const handleSend = () => {
    const trimmed = content.trim();
    if (trimmed && !isLoading) {
      onSend(trimmed);
      setContent('');
      resetHeight();
    }
  };

  const handleStop = () => {
    onStop?.();
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    // Send on Enter (without Shift)
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const resetHeight = () => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleInput = () => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      textarea.style.height = `${Math.min(textarea.scrollHeight, 120)}px`;
    }
  };

  const ModeIcon = MODE_INFO[chatMode].icon;

  return (
    <div className="p-4 flex flex-col items-center gap-2">
      {/* Main input row */}
      <div className="flex items-center gap-3 w-full max-w-[480px]">
        {/* Input container */}
        <div 
          className={`
            relative flex-1 flex items-center
            bg-white/[0.04]
            border rounded-2xl
            transition-all duration-200
            ${isFocused 
              ? 'border-violet-500/50 bg-white/[0.06]' 
              : 'border-white/[0.08] hover:border-white/[0.12]'
            }
          `}
        >
          <textarea
            ref={textareaRef}
            value={content}
            onChange={(e) => setContent(e.target.value)}
            onKeyDown={handleKeyDown}
            onInput={handleInput}
            onFocus={() => setIsFocused(true)}
            onBlur={() => setIsFocused(false)}
            placeholder={placeholder}
            className="w-full bg-transparent text-white/85 placeholder-white/30 text-[13px] resize-none focus:outline-none h-[32px] max-h-[80px] py-[6px] px-4 leading-[20px]"
            rows={1}
            disabled={isLoading}
          />
        </div>

        {/* Send/Stop button */}
        {isLoading ? (
          <button
            onClick={handleStop}
            className="w-[32px] h-[32px] rounded-full bg-red-500/15 hover:bg-red-500/25 transition-all flex items-center justify-center shrink-0 border border-red-500/20"
            title="Stop"
          >
            <StopCircle size={14} className="text-red-400" />
          </button>
        ) : (
          <button
            onClick={handleSend}
            disabled={!content.trim()}
            className={`w-[32px] h-[32px] rounded-full transition-all flex items-center justify-center shrink-0 ${
              content.trim()
                ? 'bg-violet-500 hover:bg-violet-600 text-white'
                : 'bg-white/[0.04] text-white/25 cursor-not-allowed border border-white/[0.06]'
            }`}
            title="Send"
          >
            <ArrowUp size={14} strokeWidth={2.5} />
          </button>
        )}
      </div>

      {/* Mode & Model selector row */}
      <div className="flex items-center gap-3 w-full max-w-[480px]">
        {/* Mode selector */}
        <div className="relative" ref={modeDropdownRef}>
          <button
            onClick={() => setShowModeDropdown(!showModeDropdown)}
            className="flex items-center gap-1.5 px-2 py-1 rounded-lg hover:bg-white/[0.06] transition-colors text-white/60 hover:text-white/80"
          >
            <ModeIcon size={14} />
            <span className="text-xs">{MODE_INFO[chatMode].label}</span>
            <ChevronDown size={12} className={`transition-transform ${showModeDropdown ? 'rotate-180' : ''}`} />
          </button>
          
          {showModeDropdown && (
            <div className="absolute bottom-full left-0 mb-1 w-48 bg-[#1a1a1a] border border-white/10 rounded-lg shadow-xl overflow-hidden z-50">
              {(Object.keys(MODE_INFO) as ChatMode[]).map((mode) => {
                const info = MODE_INFO[mode];
                const Icon = info.icon;
                return (
                  <button
                    key={mode}
                    onClick={() => {
                      setChatMode(mode);
                      setShowModeDropdown(false);
                    }}
                    className={`w-full flex items-start gap-2 px-3 py-2 hover:bg-white/[0.06] transition-colors text-left ${
                      mode === chatMode ? 'bg-white/[0.04]' : ''
                    }`}
                  >
                    <Icon size={14} className="mt-0.5 text-white/60" />
                    <div>
                      <div className="text-xs text-white/80">{info.label}</div>
                      <div className="text-[10px] text-white/40">{info.description}</div>
                    </div>
                  </button>
                );
              })}
            </div>
          )}
        </div>

        {/* Model selector */}
        <div className="relative" ref={modelDropdownRef}>
          <button
            onClick={handleOpenModelDropdown}
            className="flex items-center gap-1.5 px-2 py-1 rounded-lg hover:bg-white/[0.06] transition-colors text-white/60 hover:text-white/80 max-w-[180px]"
          >
            <span className="text-xs truncate">{displayModelName}</span>
            <ChevronDown size={12} className={`transition-transform shrink-0 ${showModelDropdown ? 'rotate-180' : ''}`} />
          </button>
          
          {showModelDropdown && (
            <div className="absolute bottom-full left-0 mb-1 w-72 max-h-80 bg-[#1a1a1a] border border-white/10 rounded-lg shadow-xl z-50 flex flex-col">
              {/* Header with close button */}
              <div className="flex items-center justify-between px-3 py-2 border-b border-white/10 flex-shrink-0">
                <span className="text-[10px] font-medium text-white/50 uppercase tracking-wide">Select Model</span>
                <button
                  onClick={() => setShowModelDropdown(false)}
                  className="text-white/40 hover:text-white/70 transition-colors"
                >
                  <X size={14} />
                </button>
              </div>
              
              {/* Model list */}
              <div className="overflow-y-auto flex-1">
                {availableModels.length === 0 ? (
                  <div className="px-3 py-3 text-xs text-white/40 text-center">
                    No models enabled.<br/>
                    <span className="text-white/30">Configure in Settings →</span>
                  </div>
                ) : (
                  Object.entries(modelsByApiKey).map(([apiKeyId, models]) => (
                    <div key={apiKeyId}>
                      <div className="px-3 py-1.5 text-[10px] font-medium text-white/40 uppercase tracking-wide bg-white/[0.02] sticky top-0">
                        {apiKeyNameMap[apiKeyId] || 'Unknown'}
                      </div>
                      {models.map((model) => (
                        <button
                          key={model.id}
                          onClick={() => {
                            setSelectedModel(model.id);
                            // Don't auto-close dropdown - user can manually close it
                          }}
                          className={`w-full text-left px-3 py-2 hover:bg-white/[0.06] transition-colors flex items-center justify-between gap-2 ${
                            model.id === selectedModel ? 'bg-violet-500/20 border-l-2 border-violet-500' : ''
                          }`}
                        >
                          <span className="text-xs text-white/80 truncate">{model.name}</span>
                          <span className="text-[9px] text-white/30 bg-white/[0.04] px-1.5 py-0.5 rounded flex-shrink-0">
                            {apiKeyNameMap[model.api_key_id] || model.provider}
                          </span>
                        </button>
                      ))}
                    </div>
                  ))
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Loading indicator */}
      {isLoading && (
        <div className="absolute bottom-20 left-1/2 -translate-x-1/2">
          <span className="flex items-center gap-1.5 text-[10px] text-violet-400/70 bg-violet-500/10 px-2 py-1 rounded-full">
            <Loader2 size={10} className="animate-spin" />
            Running...
          </span>
        </div>
      )}
    </div>
  );
}

