import { useState, useCallback, useRef } from 'react';
import { MessageList } from './MessageList';
import { ChatInput } from './ChatInput';
import { CollapsibleExecutionLog } from '../Visual/CollapsibleExecutionLog';
import { useAppStore } from '../../store';

export function ChatPanel() {
  const { messages, sendMessage } = useAppStore();
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
    <div className="relative flex flex-col h-full bg-nb-bg/50">
      {/* 浮动的 Execution Log - 不占用垂直空间 */}
      <CollapsibleExecutionLog />
      
      {/* Messages - 让 MessageList 完全控制滚动，不要嵌套滚动容器 */}
      <div className="flex-1 min-h-0">
        <MessageList 
          messages={messages} 
          onUnreadCountChange={stableSetUnreadCount}
          scrollToBottomRef={scrollToBottomRef}
          clearUnreadRef={clearUnreadRef}
        />
      </div>

      {/* Input */}
      <ChatInput 
        onSend={sendMessage} 
        unreadCount={unreadCount}
        onScrollToBottom={handleScrollToBottom}
      />
    </div>
  );
}
