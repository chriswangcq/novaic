import { useRef, useEffect } from 'react';
import { MessageList } from './MessageList';
import { ChatInput } from './ChatInput';
import { useAppStore } from '../../store';
import { Sparkles, Trash2 } from 'lucide-react';

export function ChatPanel() {
  const { messages, isExecuting, sendMessage, clearMessages } = useAppStore();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className="flex flex-col h-full bg-[#0a0a0a]">
      {/* Header with Logo */}
      <div className="h-10 px-3 flex items-center justify-between border-b border-white/[0.04] bg-[#0f0f0f] shrink-0" data-tauri-drag-region>
        {/* Logo + Agent */}
        <div className="flex items-center gap-2.5">
          <div className="flex items-center gap-2">
            <div className="w-5 h-5 rounded bg-gradient-to-br from-violet-500/90 to-purple-600/90 flex items-center justify-center">
              <span className="text-white font-semibold text-[8px]">NA</span>
            </div>
            <span className="font-medium text-white/80 text-[12px]">NovAIC</span>
          </div>
          <div className="w-px h-3 bg-white/[0.06]" />
          <div className="flex items-center gap-1">
            <Sparkles size={10} className="text-violet-400/70" />
            <span className="text-[11px] text-white/40">Agent</span>
          </div>
        </div>
        {/* Clear button */}
        <button 
          onClick={clearMessages}
          className="p-1.5 rounded hover:bg-white/[0.06] transition-colors"
          title="Clear chat"
        >
          <Trash2 size={12} className="text-white/30" />
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto">
        <MessageList messages={messages} isLoading={isExecuting} />
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <ChatInput onSend={sendMessage} isLoading={isExecuting} />
    </div>
  );
}
