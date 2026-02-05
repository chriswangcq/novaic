import { useRef, useEffect, useLayoutEffect, useCallback, useState } from 'react';
import { Loader2 } from 'lucide-react';
import { Message } from '../../types';
import { UserMessage } from './UserMessage';
import { AssistantMessage } from './AssistantMessage';
import { WelcomeScreen } from './WelcomeScreen';
import { StreamingIndicator } from './StreamingIndicator';
import { useAppStore } from '../../store';
import { useVirtualList } from '../../hooks/useVirtualList';
import { useScrollPagination } from '../../hooks/useScrollPagination';
import { MESSAGE_ESTIMATE_SIZE, MESSAGE_OVERSCAN } from '../../constants/scroll';

interface MessageListProps {
  messages: Message[];
  isLoading: boolean;
  onUnreadCountChange?: (count: number) => void;
  scrollToBottomRef?: React.MutableRefObject<(() => void) | null>;
  clearUnreadRef?: React.MutableRefObject<(() => void) | null>;
}

export function MessageList({ messages, isLoading, onUnreadCountChange, scrollToBottomRef, clearUnreadRef }: MessageListProps) {
  const lastMessageCountRef = useRef(messages.length);
  const lastMessageIdRef = useRef<string | null>(null); // 记录最后一条消息的 ID
  const prevIsLoadingMoreRef = useRef(false); // 记录上一次的 isLoadingMore 状态
  const [isReady, setIsReady] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);
  const hasInitialScrolled = useRef(false);
  
  const { 
    hasMoreMessages, 
    isLoadingMore, 
    loadMoreMessages,
    currentAgentId 
  } = useAppStore();

  // 使用虚拟列表 hook
  const { parentRef, virtualizer } = useVirtualList({
    count: messages.length,
    estimateSize: MESSAGE_ESTIMATE_SIZE,
    overscan: MESSAGE_OVERSCAN,
  });

  // 使用分页滚动 hook
  const { handleScroll: handlePaginationScroll } = useScrollPagination({
    itemsLength: messages.length,
    virtualizer,
    hasMore: hasMoreMessages,
    isLoading: isLoadingMore,
    onLoadMore: loadMoreMessages,
    scrollThreshold: 100
  });

  // 判断最新消息的可见高度
  const getLastMessageVisibleHeight = useCallback(() => {
    if (messages.length === 0) return 0;
    
    const virtualItems = virtualizer.getVirtualItems();
    if (virtualItems.length === 0) return 0;
    
    const lastVirtualItem = virtualItems[virtualItems.length - 1];
    if (lastVirtualItem.index !== messages.length - 1) return 0; // 最新消息不在可见区域
    
    const scrollElement = parentRef.current;
    if (!scrollElement) return 0;
    
    const { scrollTop, clientHeight } = scrollElement;
    const itemEnd = lastVirtualItem.start + lastVirtualItem.size;
    const itemStart = lastVirtualItem.start;
    const viewportBottom = scrollTop + clientHeight;
    
    // 计算可见高度
    const visibleHeight = Math.max(0, Math.min(itemEnd, viewportBottom) - Math.max(itemStart, scrollTop));
    return visibleHeight;
  }, [messages.length, virtualizer, parentRef]);

  // 判断是否应该清除未读（最新消息露出 > 30px）
  const shouldClearUnread = useCallback(() => {
    const visibleHeight = getLastMessageVisibleHeight();
    return visibleHeight > 30;
  }, [getLastMessageVisibleHeight]);

  // 滚动到底部
  const scrollToBottom = useCallback((behavior: 'auto' | 'smooth' = 'smooth') => {
    requestAnimationFrame(() => {
      // 在回调执行时获取最新的消息数量，避免闭包陷阱
      if (messages.length > 0) {
        virtualizer.scrollToIndex(messages.length - 1, { 
          align: 'end',
          behavior 
        });
      }
    });
  }, [virtualizer, messages.length]);

  // 清除未读计数的函数
  const clearUnread = useCallback(() => {
    setUnreadCount(0);
  }, []);

  // 暴露函数给父组件
  useEffect(() => {
    if (scrollToBottomRef) {
      scrollToBottomRef.current = () => scrollToBottom('smooth');
    }
    if (clearUnreadRef) {
      clearUnreadRef.current = clearUnread;
    }
  }, [scrollToBottom, scrollToBottomRef, clearUnread, clearUnreadRef]);

  // 同步 unreadCount 到父组件
  useEffect(() => {
    onUnreadCountChange?.(unreadCount);
  }, [unreadCount, onUnreadCountChange]);

  // 切换聊天时重置状态
  useLayoutEffect(() => {
    hasInitialScrolled.current = false;
    setIsReady(false);
    setUnreadCount(0);
    lastMessageIdRef.current = null; // 重置消息 ID
    prevIsLoadingMoreRef.current = false; // 重置加载状态
  }, [currentAgentId]);

  // 初始滚动到底部
  useEffect(() => {
    if (!hasInitialScrolled.current && messages.length > 0) {
      const timer = setTimeout(() => {
        scrollToBottom('auto');
        hasInitialScrolled.current = true;
        setIsReady(true);
      }, 0);
      return () => clearTimeout(timer);
    } else if (messages.length === 0) {
      setIsReady(true);
    }
  }, [messages.length, scrollToBottom]);

  // 监听 isLoading 状态，StreamingIndicator 出现时重新滚动到底部
  useEffect(() => {
    if (isLoading && hasInitialScrolled.current && messages.length > 0) {
      const latestMessage = messages[messages.length - 1];
      if (latestMessage.role === 'user') {
        // 检查用户是否在底部
        requestAnimationFrame(() => {
          if (shouldClearUnread()) {
            // 用户还在底部 → 滚动（保持在底部）
            scrollToBottom('smooth');
          }
          // 用户不在底部 → 不滚动（尊重用户意图）
        });
      }
    }
  }, [isLoading, messages.length, scrollToBottom, shouldClearUnread]);

  // 监听新消息，智能滚动逻辑
  useEffect(() => {
    let rafId: number | null = null;
    
    if (hasInitialScrolled.current && messages.length > 0) {
      const latestMessage = messages[messages.length - 1];
      const prevMessageId = lastMessageIdRef.current;
      
      // 检测是否刚完成历史消息加载（在更新前检查）
      const justFinishedLoadingMore = prevIsLoadingMoreRef.current && !isLoadingMore;
      
      // 只有当最后一条消息的 ID 变化，且不是正在加载更多，且不是刚完成加载历史消息时，才认为是新消息
      if (latestMessage.id !== prevMessageId && !isLoadingMore && !justFinishedLoadingMore) {
        const isUserMessage = latestMessage.role === 'user';
        
        if (isUserMessage) {
          // 用户消息：必定滚动
          scrollToBottom('smooth');
          setUnreadCount(0);
        } else {
          // Agent 消息：需要延迟检查，等虚拟列表更新后再判断
          rafId = requestAnimationFrame(() => {
            // 延迟一帧，确保虚拟列表已更新
            if (shouldClearUnread()) {
              // 最新消息可见（露出 > 30px）：自动滚动
              scrollToBottom('smooth');
              setUnreadCount(0);
            } else {
              // 最新消息不可见：增加未读计数
              setUnreadCount(prev => prev + 1);
            }
          });
        }
      }
      
      // 更新最后一条消息的 ID（在处理完新消息后）
      lastMessageIdRef.current = latestMessage.id;
      
      // 更新 isLoadingMore 状态（在检查完之后）
      prevIsLoadingMoreRef.current = isLoadingMore;
    }
    
    // 更新消息数量 ref
    lastMessageCountRef.current = messages.length;
    
    // 清理函数
    return () => {
      if (rafId !== null) {
        cancelAnimationFrame(rafId);
      }
    };
  }, [messages, messages.length, isLoadingMore, scrollToBottom, shouldClearUnread]);

  // 合并滚动处理：分页和清除未读计数
  const handleScroll = useCallback((e: React.UIEvent<HTMLDivElement>) => {
    // 分页逻辑
    handlePaginationScroll(e);
    
    // 清除未读计数逻辑（最新消息可见时）
    if (unreadCount > 0 && shouldClearUnread()) {
      setUnreadCount(0);
    }
  }, [handlePaginationScroll, unreadCount, shouldClearUnread]);

  // Empty state
  if (messages.length === 0 && !isLoading) {
    return <WelcomeScreen />;
  }

  const virtualItems = virtualizer.getVirtualItems();

  return (
    <div 
      ref={parentRef}
      className={`h-full overflow-auto px-3 py-3 relative ${isReady ? 'opacity-100' : 'opacity-0'}`}
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
