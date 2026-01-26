import { useState, useRef, KeyboardEvent, useEffect } from 'react';
import { Send, Loader2, StopCircle, ArrowUp } from 'lucide-react';

interface ChatInputProps {
  onSend: (content: string) => void;
  onStop?: () => void;
  isLoading: boolean;
  placeholder?: string;
}

export function ChatInput({ 
  onSend, 
  onStop, 
  isLoading, 
  placeholder = "Ask anything..." 
}: ChatInputProps) {
  const [content, setContent] = useState('');
  const [isFocused, setIsFocused] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Focus on mount
  useEffect(() => {
    textareaRef.current?.focus();
  }, []);

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

  return (
    <div className="p-4 flex justify-center">
      <div className="flex items-center gap-3 w-full max-w-[360px]">
        {/* Input container */}
        <div 
          className={`
            relative flex-1 flex items-center
            bg-white/[0.04]
            border rounded-full
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

      {/* Loading indicator */}
      {isLoading && (
        <div className="absolute bottom-16 left-1/2 -translate-x-1/2">
          <span className="flex items-center gap-1.5 text-[10px] text-violet-400/70 bg-violet-500/10 px-2 py-1 rounded-full">
            <Loader2 size={10} className="animate-spin" />
            Running...
          </span>
        </div>
      )}
    </div>
  );
}

