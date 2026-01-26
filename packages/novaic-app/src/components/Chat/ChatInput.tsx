import { useState, useRef, KeyboardEvent, useEffect } from 'react';
import { Send, Paperclip, Loader2, StopCircle } from 'lucide-react';

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
  placeholder = "Ask Agent anything..." 
}: ChatInputProps) {
  const [content, setContent] = useState('');
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
      textarea.style.height = `${Math.min(textarea.scrollHeight, 200)}px`;
    }
  };

  return (
    <div className="p-3 border-t border-white/[0.06] bg-[#0d0d0d]">
      <div className="relative flex items-end gap-2 bg-white/[0.03] border border-white/[0.08] rounded-xl p-2 focus-within:border-violet-500/30 transition-colors">
        {/* Attachment button */}
        <button
          className="p-2 rounded-lg hover:bg-white/[0.04] transition-colors flex-shrink-0"
          title="Attach file"
        >
          <Paperclip size={18} className="text-white/30 hover:text-white/50" />
        </button>

        {/* Textarea */}
        <textarea
          ref={textareaRef}
          value={content}
          onChange={(e) => setContent(e.target.value)}
          onKeyDown={handleKeyDown}
          onInput={handleInput}
          placeholder={placeholder}
          className="flex-1 bg-transparent text-white/90 placeholder-white/30 text-sm resize-none focus:outline-none min-h-[40px] max-h-[200px] py-2"
          rows={1}
          disabled={isLoading}
        />

        {/* Send/Stop button */}
        {isLoading ? (
          <button
            onClick={handleStop}
            className="p-2 rounded-lg bg-red-500/20 hover:bg-red-500/30 transition-colors flex-shrink-0"
            title="Stop"
          >
            <StopCircle size={18} className="text-red-400" />
          </button>
        ) : (
          <button
            onClick={handleSend}
            disabled={!content.trim()}
            className={`p-2 rounded-lg transition-colors flex-shrink-0 ${
              content.trim()
                ? 'bg-violet-500 hover:bg-violet-600 text-white'
                : 'bg-white/[0.04] text-white/20 cursor-not-allowed'
            }`}
            title="Send (Enter)"
          >
            <Send size={18} />
          </button>
        )}
      </div>

      {/* Hint */}
      <div className="flex items-center justify-between mt-2 px-1">
        <span className="text-[11px] text-white/20">
          Enter to send · Shift+Enter for new line
        </span>
        {isLoading && (
          <span className="flex items-center gap-1.5 text-[11px] text-violet-400">
            <Loader2 size={12} className="animate-spin" />
            Running...
          </span>
        )}
      </div>
    </div>
  );
}

