import { MessageList } from './MessageList';
import { ChatInput } from './ChatInput';
import { useAppStore } from '../../store';

export function ChatPanel() {
  const { messages, isExecuting, sendMessage, stopExecution } = useAppStore();

  return (
    <div className="flex flex-col h-full bg-[#0a0a0a]">
      {/* Messages - 让 MessageList 完全控制滚动，不要嵌套滚动容器 */}
      <div className="flex-1 min-h-0">
        <MessageList messages={messages} isLoading={isExecuting} />
      </div>

      {/* Input */}
      <ChatInput onSend={sendMessage} onStop={stopExecution} isLoading={isExecuting} />
    </div>
  );
}
