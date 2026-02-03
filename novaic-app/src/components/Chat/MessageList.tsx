import { useRef, useEffect, useCallback } from 'react';
import { useVirtualizer } from '@tanstack/react-virtual';
import { Loader2 } from 'lucide-react';
import { Message } from '../../types';
import { UserMessage } from './UserMessage';
import { AssistantMessage } from './AssistantMessage';
import { WelcomeScreen } from './WelcomeScreen';
import { StreamingIndicator } from './StreamingIndicator';
import { useAppStore } from '../../store';

interface MessageListProps {
  messages: Message[];
  isLoading: boolean;
}

export function MessageList({ messages, isLoading }: MessageListProps) {
  const parentRef = useRef<HTMLDivElement>(null);
  const lastMessageCountRef = useRef(messages.length);
  const scrollPositionRef = useRef<{ offset: number; height: number } | null>(null);
  
  const { 
    hasMoreMessages, 
    isLoadingMore, 
    loadMoreMessages 
  } = useAppStore();

  // Virtual list configuration
  const virtualizer = useVirtualizer({
    count: messages.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 100, // 估算每条消息的平均高度
    overscan: 5, // 预渲染上下各 5 个项目
  });

  // 滚动到底部（新消息到达时）
  const scrollToBottom = useCallback(() => {
    if (parentRef.current) {
      parentRef.current.scrollTop = parentRef.current.scrollHeight;
    }
  }, []);

  // 监听新消息，自动滚动到底部
  useEffect(() => {
    if (messages.length > lastMessageCountRef.current) {
      // 新消息到达，滚动到底部
      setTimeout(scrollToBottom, 50);
    }
    lastMessageCountRef.current = messages.length;
  }, [messages.length, scrollToBottom]);

  // 处理滚动事件 - 滚动到顶部时加载更多
  const handleScroll = useCallback((e: React.UIEvent<HTMLDivElement>) => {
    const target = e.target as HTMLDivElement;
    const scrollTop = target.scrollTop;
    
    // 当滚动到顶部附近（小于 100px）时，加载更多消息
    if (scrollTop < 100 && hasMoreMessages && !isLoadingMore && messages.length > 0) {
      // 保存当前滚动位置，用于加载后恢复
      scrollPositionRef.current = {
        offset: target.scrollHeight - target.scrollTop,
        height: target.scrollHeight,
      };
      loadMoreMessages();
    }
  }, [hasMoreMessages, isLoadingMore, loadMoreMessages, messages.length]);

  // 加载更多消息后恢复滚动位置
  useEffect(() => {
    if (!isLoadingMore && scrollPositionRef.current && parentRef.current) {
      const { offset } = scrollPositionRef.current;
      // 恢复滚动位置：新的 scrollHeight - 之前的 offset
      parentRef.current.scrollTop = parentRef.current.scrollHeight - offset;
      scrollPositionRef.current = null;
    }
  }, [isLoadingMore, messages.length]);

  // Empty state
  if (messages.length === 0 && !isLoading) {
    return <WelcomeScreen />;
  }

  const virtualItems = virtualizer.getVirtualItems();

  return (
    <div 
      ref={parentRef}
      className="h-full overflow-auto px-3 py-3"
      onScroll={handleScroll}
    >
      {/* 加载更多指示器 */}
      {isLoadingMore && (
        <div className="flex justify-center py-2 mb-2">
          <Loader2 size={20} className="animate-spin text-nb-text-muted" />
          <span className="ml-2 text-xs text-nb-text-muted">加载历史消息...</span>
        </div>
      )}
      
      {/* 没有更多消息提示 */}
      {!hasMoreMessages && messages.length > 0 && (
        <div className="text-center text-xs text-nb-text-muted py-2 mb-2">
          — 已加载全部消息 —
        </div>
      )}

      {/* 虚拟列表容器 */}
      <div
        style={{
          height: `${virtualizer.getTotalSize()}px`,
          width: '100%',
          position: 'relative',
        }}
      >
        {virtualItems.map((virtualRow) => {
          const message = messages[virtualRow.index];
          return (
            <div
              key={virtualRow.key}
              data-index={virtualRow.index}
              ref={virtualizer.measureElement}
              style={{
                position: 'absolute',
                top: 0,
                left: 0,
                width: '100%',
                transform: `translateY(${virtualRow.start}px)`,
              }}
            >
              <div 
                className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'} mb-3`}
              >
                <div className="max-w-[85%]">
                  {message.role === 'user' 
                    ? <UserMessage message={message} />
                    : <AssistantMessage message={message} />
                  }
                </div>
              </div>
            </div>
          );
        })}
      </div>
      
      {/* Loading indicator when waiting for first response */}
      {isLoading && messages.length > 0 && 
        messages[messages.length - 1].role === 'user' && (
        <div className="flex justify-start mt-3">
          <StreamingIndicator />
        </div>
      )}
    </div>
  );
}
