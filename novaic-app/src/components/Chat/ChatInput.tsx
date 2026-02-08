import { useState, useRef, KeyboardEvent, useEffect, useMemo, useCallback } from 'react';
import { ArrowUp, ChevronDown, Bot, X, ArrowDown } from 'lucide-react';
import { useAppStore } from '../../store';
import { CandidateModel } from '../../types';

interface ChatInputProps {
  onSend: (content: string) => void;
  placeholder?: string;
  unreadCount?: number;
  onScrollToBottom?: () => void;
}

export function ChatInput({ 
  onSend, 
  placeholder = "Ask anything...",
  unreadCount = 0,
  onScrollToBottom
}: ChatInputProps) {
  const [content, setContent] = useState('');
  const [isFocused, setIsFocused] = useState(false);
  const [showModelDropdown, setShowModelDropdown] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const modelDropdownRef = useRef<HTMLDivElement>(null);

  const { 
    availableModels,
    apiKeys,
    selectedModel, 
    setSelectedModel,
    loadModelsFromConfig,
    currentAgentId
  } = useAppStore();

  // Check if agent is selected
  const hasAgent = !!currentAgentId;

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

  // Get current model info - selectedModel is composite ID: {api_key_id}:{model_id}
  // Note: model_id may contain colons, so only split on FIRST colon
  const currentModel = useMemo(() => {
    if (!selectedModel) return null;
    const colonIndex = selectedModel.indexOf(':');
    if (colonIndex === -1) return null;
    const apiKeyId = selectedModel.substring(0, colonIndex);
    const modelId = selectedModel.substring(colonIndex + 1);
    if (!apiKeyId || !modelId) return null;
    return availableModels.find(m => m.api_key_id === apiKeyId && m.id === modelId);
  }, [selectedModel, availableModels]);
  const displayModelName = currentModel?.name || (selectedModel?.includes(':') ? selectedModel.substring(selectedModel.indexOf(':') + 1) : selectedModel) || 'Select model';

  // Group models by API Key (not provider)
  const modelsByApiKey = useMemo(() => {
    const grouped: Record<string, CandidateModel[]> = {};
    availableModels.forEach(model => {
      const keyId = model.api_key_id;
      if (!grouped[keyId]) grouped[keyId] = [];
      grouped[keyId].push(model);
    });
    return grouped;
  }, [availableModels]);

  const handleSend = () => {
    // Check if agent is selected
    if (!hasAgent) {
      return;
    }
    const trimmed = content.trim();
    if (trimmed) {
      // Fire-and-forget: allow sending even when agent is busy
      onSend(trimmed);
      setContent('');
      resetHeight();
    }
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

  return (
    <div className="p-4 flex flex-col items-center gap-2 relative">
      {/* 新消息提示胶囊按钮 - 在输入框上方 */}
      {unreadCount > 0 && (
        <button
          onClick={() => {
            onScrollToBottom?.();
          }}
          className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-4 py-2 bg-white/10 hover:bg-white/15 hover:scale-105 text-white text-sm rounded-full shadow-lg flex items-center gap-2 z-10 transition-all animate-fade-in border border-white/20"
        >
          <span>{unreadCount}条新消息</span>
          <ArrowDown size={16} />
        </button>
      )}

      {/* No agent selected hint */}
      {!hasAgent && (
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-400/80 text-xs mb-1">
          <Bot size={14} />
          <span>Select an agent from the sidebar to start chatting</span>
        </div>
      )}
      
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
              ? 'border-white/30 bg-white/[0.06]' 
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
            placeholder={hasAgent ? placeholder : "Please select an agent first..."}
            disabled={!hasAgent}
            className={`w-full bg-transparent text-white/85 placeholder-white/30 text-[13px] resize-none focus:outline-none h-[32px] max-h-[80px] py-[6px] px-4 leading-[20px] ${!hasAgent ? 'cursor-not-allowed opacity-50' : ''}`}
            rows={1}
          />
        </div>

        {/* Send button - always available (fire-and-forget mode) */}
        <button
          onClick={handleSend}
          disabled={!hasAgent || !content.trim()}
          className={`w-[32px] h-[32px] rounded-full transition-all flex items-center justify-center shrink-0 ${
            hasAgent && content.trim()
              ? 'bg-white/20 hover:bg-white/25 text-white'
              : 'bg-white/[0.04] text-white/25 cursor-not-allowed border border-white/[0.06]'
          }`}
          title={hasAgent ? "Send" : "Please select an agent first"}
        >
          <ArrowUp size={14} strokeWidth={2.5} />
        </button>

      </div>

      {/* Model selector row */}
      <div className="flex items-center gap-3 w-full max-w-[480px]">
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
                      {models.map((model) => {
                        // Use composite ID: {api_key_id}:{model_id} to uniquely identify
                        const compositeId = `${model.api_key_id}:${model.id}`;
                        return (
                          <button
                            key={compositeId}
                            onClick={() => {
                              setSelectedModel(compositeId);
                              setShowModelDropdown(false);
                            }}
                            className={`w-full text-left px-3 py-2 hover:bg-white/[0.06] transition-colors flex items-center justify-between gap-2 ${
                              compositeId === selectedModel ? 'bg-white/10 border-l-2 border-white/40' : ''
                            }`}
                          >
                            <span className="text-xs text-white/80 truncate">{model.name}</span>
                            <span className="text-[9px] text-white/30 bg-white/[0.04] px-1.5 py-0.5 rounded flex-shrink-0">
                              {model.api_key_name || apiKeyNameMap[model.api_key_id] || model.provider}
                            </span>
                          </button>
                        );
                      })}
                    </div>
                  ))
                )}
              </div>
            </div>
          )}
        </div>
      </div>

    </div>
  );
}

