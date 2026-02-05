import { useRef, useEffect, useLayoutEffect, useCallback, useState } from 'react';
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
  const hasInitialScrolled = useRef(false);
  const [isReady, setIsReady] = useState(false);
  
  const { 
    hasMoreMessages, 
    isLoadingMore, 
    loadMoreMessages,
    currentAgentId 
  } = useAppStore();

  // Virtual list configuration
  const virtualizer = useVirtualizer({
    count: messages.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 120, // 估算每条消息的平均高度，稍大一些更安全
    overscan: 8, // 增加预渲染数量，确保边界元素被渲染
  });

  // 切换聊天时重置状态
  useLayoutEffect(() => {
    hasInitialScrolled.current = false;
    setIsReady(false);
  }, [currentAgentId]);

  // 初始化时滚动到底部
  useEffect(() => {
    if (!hasInitialScrolled.current && messages.length > 0) {
      // 使用 virtualizer API 滚动到最后一条消息
      // 需要等待 virtualizer 初始化完成
      const timer = setTimeout(() => {
        virtualizer.scrollToIndex(messages.length - 1, { 
          align: 'end',
          behavior: 'auto' 
        });
        hasInitialScrolled.current = true;
        setIsReady(true);
      }, 0);
      return () => clearTimeout(timer);
    } else if (messages.length === 0) {
      // 没有消息时直接显示（欢迎屏幕）
      setIsReady(true);
    }
  }, [messages.length, currentAgentId, virtualizer]);

  // 监听新消息，自动滚动到底部（已初始化后的新消息）
  useEffect(() => {
    if (hasInitialScrolled.current && messages.length > lastMessageCountRef.current) {
      // 新消息到达，使用 virtualizer API 滚动到底部
      // 延迟一帧确保 DOM 已更新
      requestAnimationFrame(() => {
        virtualizer.scrollToIndex(messages.length - 1, { 
          align: 'end',
          behavior: 'smooth' 
        });
      });
    }
    lastMessageCountRef.current = messages.length;
  }, [messages.length, virtualizer]);

  // 记录加载前的第一条可见消息索引
  const firstVisibleIndexRef = useRef<number | null>(null);
  const prevMessagesLengthRef = useRef(messages.length);

  // 处理滚动事件 - 滚动到顶部时加载更多
  const handleScroll = useCallback((e: React.UIEvent<HTMLDivElement>) => {
    const target = e.target as HTMLDivElement;
    const scrollTop = target.scrollTop;
    
    // 当滚动到顶部附近（小于 100px）时，加载更多消息
    if (scrollTop < 100 && hasMoreMessages && !isLoadingMore && messages.length > 0) {
      // 保存当前第一条可见消息的索引（加载后需要调整）
      const virtualItems = virtualizer.getVirtualItems();
      if (virtualItems.length > 0) {
        firstVisibleIndexRef.current = virtualItems[0].index;
        prevMessagesLengthRef.current = messages.length;
      }
      loadMoreMessages();
    }
  }, [hasMoreMessages, isLoadingMore, loadMoreMessages, messages.length, virtualizer]);

  // 加载更多消息后恢复滚动位置
  useEffect(() => {
    if (!isLoadingMore && firstVisibleIndexRef.current !== null && messages.length > prevMessagesLengthRef.current) {
      // 计算新加载的消息数量
      const newMessagesCount = messages.length - prevMessagesLengthRef.current;
      // 滚动到之前可见的第一条消息（索引需要加上新加载的数量）
      const targetIndex = firstVisibleIndexRef.current + newMessagesCount;
      virtualizer.scrollToIndex(targetIndex, { align: 'start' });
      firstVisibleIndexRef.current = null;
    }
    prevMessagesLengthRef.current = messages.length;
  }, [isLoadingMore, messages.length, virtualizer]);

  // Empty state
  if (messages.length === 0 && !isLoading) {
    return <WelcomeScreen />;
  }

  const virtualItems = virtualizer.getVirtualItems();

  return (
    <div 
      ref={parentRef}
      className={`h-full overflow-auto px-3 py-3 ${isReady ? 'opacity-100' : 'opacity-0'}`}
      style={{ transition: 'none' }} // 不要过渡动画，直接切换
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
