import { useRef, useEffect } from 'react';
import { MessageList } from './MessageList';
import { ChatInput } from './ChatInput';
import { useAppStore } from '../../store';
import { Sparkles, Trash2 } from 'lucide-react';

export function ChatPanel() {
  const { messages, isExecuting, sendMessage } = useAppStore();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleClear = () => {
    // TODO: Add clear messages action
  };

  return (
    <div className="flex flex-col h-full bg-[#0d0d0d]">
      {/* Header - 极简 */}
      <div className="h-11 px-4 flex items-center justify-between border-b border-white/[0.06] bg-[#0d0d0d]">
        <div className="flex items-center gap-2">
          <Sparkles size={14} className="text-violet-400" />
          <span className="text-[13px] font-medium text-white/90">Agent</span>
        </div>
        <button 
          onClick={handleClear}
          className="p-1.5 rounded hover:bg-white/[0.06] transition-colors"
          title="Clear chat"
        >
          <Trash2 size={14} className="text-white/40" />
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
