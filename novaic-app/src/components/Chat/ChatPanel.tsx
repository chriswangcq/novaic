import { useState, useCallback, useRef } from 'react';
import { MessageList } from './MessageList';
import { ChatInput } from './ChatInput';
import { useAppStore } from '../../store';

export function ChatPanel() {
  const { messages, isExecuting, sendMessage, stopExecution } = useAppStore();
  const [unreadCount, setUnreadCount] = useState(0);
  const scrollToBottomRef = useRef<(() => void) | null>(null);
  const clearUnreadRef = useRef<(() => void) | null>(null);

  // 稳定的回调引用
  const stableSetUnreadCount = useCallback((count: number) => {
    setUnreadCount(count);
  }, []);

  const handleScrollToBottom = useCallback(() => {
    // 先清除 MessageList 内部的未读计数
    clearUnreadRef.current?.();
    // 然后滚动
    scrollToBottomRef.current?.();
  }, []);

  return (
    <div className="flex flex-col h-full bg-[#0a0a0a]">
      {/* Messages - 让 MessageList 完全控制滚动，不要嵌套滚动容器 */}
      <div className="flex-1 min-h-0">
        <MessageList 
          messages={messages} 
          isLoading={isExecuting}
          onUnreadCountChange={stableSetUnreadCount}
          scrollToBottomRef={scrollToBottomRef}
          clearUnreadRef={clearUnreadRef}
        />
      </div>

      {/* Input */}
      <ChatInput 
        onSend={sendMessage} 
        onStop={stopExecution} 
        isLoading={isExecuting}
        unreadCount={unreadCount}
        onScrollToBottom={handleScrollToBottom}
      />
    </div>
  );
}
