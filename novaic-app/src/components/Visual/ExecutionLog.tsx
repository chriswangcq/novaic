import { useEffect, useLayoutEffect, useState, useCallback, useRef } from 'react';
import { LogEntry } from '../../types';
import { CheckCircle, Terminal, Loader2, Brain, XCircle, ChevronDown, ChevronRight, Sparkles } from 'lucide-react';
import { useAppStore } from '../../store';
import { useVirtualList } from '../../hooks/useVirtualList';
import { useScrollPagination } from '../../hooks/useScrollPagination';
import { LOG_ESTIMATE_SIZE, LOG_OVERSCAN } from '../../constants/scroll';
import { SmartValue } from './SmartValue';
import { formatTime } from '../../utils/time';

interface ExecutionLogProps {
  logs: LogEntry[];
}

// 截断字符串
const truncateString = (str: string, maxLength: number): string => {
  if (str.length <= maxLength) return str;
  return str.substring(0, maxLength) + '...';
};

// ==================== 日志卡片组件 ====================

interface LogCardProps {
  log: LogEntry;
  isExpanded: boolean;
  onToggle: () => void;
  showSubagent: boolean;
}

function LogCard({ log, isExpanded, onToggle, showSubagent }: LogCardProps) {
  // 提取数据
  const getInputData = (): unknown => {
    if (log.input) return log.input;
    if (log.data?.input) {
      const inputObj = log.data.input as Record<string, unknown>;
      if (inputObj.args) return inputObj.args;
      return inputObj;
    }
    if (log.data?.args) return log.data.args;
    return null;
  };

  const getResultData = (): unknown => {
    if (log.result) return log.result;
    if (log.data?.result) {
      const resultObj = log.data.result as Record<string, unknown>;
      if (resultObj.result !== undefined) return resultObj.result;
      return resultObj;
    }
    return null;
  };

  const getThinkingContent = (): string => {
    if (log.result?.content && typeof log.result.content === 'string') return log.result.content;
    if (log.data?.content && typeof log.data.content === 'string') return log.data.content;
    if (typeof log.data === 'string') return log.data;
    return '';
  };

  const input = getInputData();
  const result = getResultData();
  const thinkingContent = getThinkingContent();
  const toolName = log.data?.tool || log.event_key || '';
  const isThink = log.kind === 'think' || log.type === 'thinking';
  const isTool = log.kind === 'tool' || log.type === 'tool_start' || log.type === 'tool_end';
  const isRunning = log.status === 'running';
  const isFailed = log.status === 'failed' || log.data?.success === false || !!(log.result?.error || log.data?.error);
  
  const hasDetails = Boolean(
    (isThink && thinkingContent) ||
    (isTool && (input || result))
  );

  // 获取摘要
  const getSummary = (): string => {
    if (isThink && thinkingContent) {
      return truncateString(thinkingContent, 100);
    }
    if (isTool && result) {
      const r = result as Record<string, unknown>;
      if (r.error) return `错误: ${truncateString(String(r.error), 60)}`;
      if (r.message) return truncateString(String(r.message), 60);
      if (r.content) return truncateString(String(r.content), 60);
      const keys = Object.keys(r).filter(k => !['success', 'done'].includes(k));
      if (keys.length > 0) {
        const firstVal = r[keys[0]];
        if (typeof firstVal === 'string' && firstVal.length > 100) {
          return `${keys[0]}: [${firstVal.length} 字符]`;
        }
        return `${keys[0]}: ${truncateString(JSON.stringify(firstVal), 50)}`;
      }
    }
    return '';
  };

  const summary = getSummary();

  return (
    <div className={`
      group rounded-lg border transition-all duration-200
      ${isRunning 
        ? 'bg-gradient-to-r from-nb-accent/10 to-transparent border-nb-accent/30' 
        : isFailed 
          ? 'bg-gradient-to-r from-nb-error/10 to-transparent border-nb-error/30'
          : 'bg-nb-surface/50 border-nb-border/50 hover:border-nb-border hover:bg-nb-surface'
      }
    `}>
      {/* 主内容区 */}
      <div 
        className="px-3 py-2.5 cursor-pointer"
        onClick={hasDetails ? onToggle : undefined}
      >
        {/* 第一行：时间 + 类型图标 + 名称 + 状态 */}
        <div className="flex items-center gap-2">
          {/* 时间戳 */}
          <span className="text-[10px] text-nb-text-secondary font-mono tabular-nums">
            {formatTime(log.timestamp, undefined, { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false })}
          </span>
          
          {/* 类型图标 */}
          <div className={`
            w-5 h-5 rounded-md flex items-center justify-center shrink-0
            ${isThink 
              ? 'bg-violet-500/20' 
              : isRunning 
                ? 'bg-nb-accent/20'
                : isFailed 
                  ? 'bg-nb-error/20' 
                  : 'bg-nb-success/20'
            }
          `}>
            {isThink ? (
              isRunning ? <Loader2 size={12} className="text-violet-400 animate-spin" /> 
                       : <Brain size={12} className="text-violet-400" />
            ) : isRunning ? (
              <Loader2 size={12} className="text-nb-text-muted animate-spin" />
            ) : isFailed ? (
              <XCircle size={12} className="text-nb-error" />
            ) : (
              <CheckCircle size={12} className="text-nb-success" />
            )}
          </div>
          
          {/* 名称 */}
          <span className={`
            text-[13px] font-medium truncate
            ${isThink ? 'text-violet-300' : 'text-nb-text'}
          `}>
            {isThink ? '思考' : toolName}
          </span>
          
          {/* Subagent 标签 */}
          {showSubagent && log.subagent_id && (
            <span className="px-1.5 py-0.5 bg-nb-surface-2 text-nb-text-secondary text-[9px] rounded font-mono">
              {log.subagent_id}
            </span>
          )}
          
          {/* 弹性空间 */}
          <div className="flex-1" />
          
          {/* 状态标签 */}
          <span className={`
            px-2 py-0.5 rounded-full text-[10px] font-medium shrink-0
            ${isRunning 
              ? 'bg-nb-accent/20 text-nb-text-muted' 
              : isFailed 
                ? 'bg-nb-error/20 text-nb-error'
                : 'bg-nb-success/20 text-nb-success'
            }
          `}>
            {isRunning ? '运行中' : isFailed ? '失败' : '完成'}
          </span>
          
          {/* 展开箭头 */}
          {hasDetails && (
            <div className={`
              w-5 h-5 rounded flex items-center justify-center
              text-nb-text-secondary group-hover:text-nb-text-muted transition-colors
            `}>
              {isExpanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
            </div>
          )}
        </div>
        
        {/* 第二行：摘要 */}
        {summary && !isExpanded && (
          <div className="mt-1.5 pl-7 text-[11px] text-nb-text-secondary leading-relaxed line-clamp-2">
            {summary}
          </div>
        )}
      </div>
      
      {/* 展开的详情区域 */}
      {isExpanded && hasDetails && (
        <div className="px-3 pb-3 space-y-2">
          <div className="h-px bg-nb-border/30" />
          
          {/* 思考内容 */}
          {isThink && thinkingContent ? (
            <div className="space-y-1.5">
              <div className="flex items-center gap-1.5 text-[10px] text-violet-400/70 font-medium">
                <Sparkles size={10} />
                <span>思考内容</span>
              </div>
              <div className="bg-nb-bg rounded-md p-2.5 border border-nb-border/30">
                <SmartValue value={thinkingContent} copyable />
              </div>
            </div>
          ) : null}
          
          {/* 工具输入 */}
          {isTool && input ? (
            <div className="space-y-1.5">
              <div className="flex items-center gap-1.5 text-[10px] text-nb-text-muted font-medium">
                <span className="w-1 h-1 rounded-full bg-nb-text-muted" />
                <span>输入参数</span>
              </div>
              <div className="bg-nb-bg rounded-md p-2.5 border border-nb-border/30">
                <SmartValue value={input} copyable />
              </div>
            </div>
          ) : null}
          
          {/* 工具输出 */}
          {isTool && result ? (
            <div className="space-y-1.5">
              <div className={`flex items-center gap-1.5 text-[10px] font-medium ${
                isFailed ? 'text-nb-error/70' : 'text-nb-success/70'
              }`}>
                <span className={`w-1 h-1 rounded-full ${isFailed ? 'bg-nb-error' : 'bg-nb-success'}`} />
                <span>{isFailed ? '错误输出' : '执行结果'}</span>
              </div>
              <div className={`bg-nb-bg rounded-md p-2.5 border ${
                isFailed ? 'border-nb-error/20' : 'border-nb-border/30'
              }`}>
                <SmartValue value={result} isError={isFailed} copyable />
              </div>
            </div>
          ) : null}
        </div>
      )}
    </div>
  );
}

// ==================== 主组件 ====================

export function ExecutionLog({ logs }: ExecutionLogProps) {
  const { 
    currentAgentId, 
    logSubagentId, 
    logSubagents, 
    setLogSubagentId,
    hasMoreLogs,
    isLoadingMoreLogs,
    loadMoreLogs,
  } = useAppStore();
  
  const [expandedLogs, setExpandedLogs] = useState<Set<string>>(new Set());
  const [isReady, setIsReady] = useState(false);
  
  const toggleLogExpand = useCallback((logKey: string) => {
    setExpandedLogs(prev => {
      const next = new Set(prev);
      if (next.has(logKey)) {
        next.delete(logKey);
      } else {
        next.add(logKey);
      }
      return next;
    });
  }, []);

  const { parentRef, virtualizer } = useVirtualList({
    count: logs.length,
    estimateSize: LOG_ESTIMATE_SIZE,
    overscan: LOG_OVERSCAN,
  });

  const hasInitialScrolled = useRef(false);
  const prevLogsLengthRef = useRef(0);
  const autoScrollEnabled = useRef(true);
  const isAutoScrolling = useRef(false);

  const isAtBottom = useCallback(() => {
    const scrollElement = parentRef.current;
    if (!scrollElement) return false;
    const { scrollTop, scrollHeight, clientHeight } = scrollElement;
    return scrollHeight - scrollTop - clientHeight < 200;
  }, [parentRef]);

  const handleUserScroll = useCallback(() => {
    if (isAutoScrolling.current) return;
    autoScrollEnabled.current = isAtBottom();
  }, [isAtBottom]);

  const { handleScroll: handlePaginationScroll, firstVisibleIndexRef } = useScrollPagination({
    itemsLength: logs.length,
    virtualizer,
    hasMore: hasMoreLogs,
    isLoading: isLoadingMoreLogs,
    onLoadMore: loadMoreLogs,
    scrollThreshold: 100
  });

  const handleScroll = useCallback((e: React.UIEvent<HTMLDivElement>) => {
    handlePaginationScroll(e);
    handleUserScroll();
  }, [handlePaginationScroll, handleUserScroll]);

  useLayoutEffect(() => {
    hasInitialScrolled.current = false;
    prevLogsLengthRef.current = 0;
    autoScrollEnabled.current = true;
    firstVisibleIndexRef.current = null;
    setIsReady(false);
  }, [currentAgentId, logSubagentId]);
  
  useEffect(() => {
    if (!hasInitialScrolled.current && logs.length > 0) {
      const timer = setTimeout(() => {
        requestAnimationFrame(() => {
          virtualizer.scrollToIndex(logs.length - 1, { align: 'end', behavior: 'auto' });
          hasInitialScrolled.current = true;
          prevLogsLengthRef.current = logs.length;
          setIsReady(true);
        });
      }, 0);
      return () => clearTimeout(timer);
    } else if (logs.length === 0) {
      setIsReady(true);
    }
  }, [logs.length, virtualizer]);

  useEffect(() => {
    if (hasInitialScrolled.current && logs.length > prevLogsLengthRef.current && !isLoadingMoreLogs) {
      if (autoScrollEnabled.current) {
        isAutoScrolling.current = true;
        const targetLength = logs.length;
        requestAnimationFrame(() => {
          requestAnimationFrame(() => {
            requestAnimationFrame(() => {
              virtualizer.scrollToIndex(targetLength - 1, { align: 'end', behavior: 'auto' });
              prevLogsLengthRef.current = targetLength;
              isAutoScrolling.current = false;
              autoScrollEnabled.current = isAtBottom();
            });
          });
        });
      } else {
        prevLogsLengthRef.current = logs.length;
      }
    }
  }, [logs.length, virtualizer, isLoadingMoreLogs, isAtBottom]);

  return (
    <div className="h-full flex flex-col bg-nb-bg">
      {/* Header */}
      <div className="h-10 px-4 flex items-center gap-3 bg-nb-surface border-b border-nb-border">
        <div className="flex items-center gap-2">
          <Terminal size={14} className="text-nb-text-secondary" />
          <span className="text-xs font-medium text-nb-text-muted">Execution Log</span>
        </div>

        {/* Subagent tabs */}
        {logSubagents.length > 0 && (
          <>
            <div className="w-px h-4 bg-nb-border" />
            <div className="flex items-center gap-1">
              <button
                className={`px-2.5 py-1 rounded-md text-[11px] font-medium transition-all ${
                  logSubagentId === null 
                    ? 'bg-white/10 text-nb-text' 
                    : 'text-nb-text-secondary hover:text-nb-text-muted hover:bg-nb-hover'
                }`}
                onClick={() => setLogSubagentId(null)}
              >
                全部
              </button>
              {logSubagents.map(id => (
                <button
                  key={id}
                  className={`px-2.5 py-1 rounded-md text-[11px] font-medium transition-all ${
                    logSubagentId === id 
                      ? 'bg-white/10 text-nb-text' 
                      : 'text-nb-text-secondary hover:text-nb-text-muted hover:bg-nb-hover'
                  }`}
                  onClick={() => setLogSubagentId(id)}
                >
                  {id}
                </button>
              ))}
            </div>
          </>
        )}
      </div>

      {/* Log content */}
      <div
        ref={parentRef}
        className={`flex-1 overflow-y-auto overflow-x-hidden p-3 ${isReady ? 'opacity-100' : 'opacity-0'}`}
        style={{ transition: 'none' }}
        onScroll={handleScroll}
      >
        {logs.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center">
            <div className="w-12 h-12 rounded-xl bg-nb-surface flex items-center justify-center mb-3 border border-nb-border">
              <Terminal size={24} className="text-nb-text-secondary" />
            </div>
            {currentAgentId ? (
              <>
                <p className="text-nb-text-muted text-sm">暂无执行日志</p>
                <p className="text-nb-text-secondary text-xs mt-1">发送消息后将在这里显示执行过程</p>
              </>
            ) : (
              <>
                <p className="text-nb-text-muted text-sm">请先选择 Agent</p>
                <p className="text-nb-text-secondary text-xs mt-1">选择或创建一个 Agent 开始使用</p>
              </>
            )}
          </div>
        ) : (
          <>
            {/* 加载更多指示器 */}
            {isLoadingMoreLogs && (
              <div className="flex items-center justify-center gap-2 py-3 mb-2">
                <Loader2 size={14} className="animate-spin text-nb-text-secondary" />
                <span className="text-[11px] text-nb-text-secondary">加载历史日志...</span>
              </div>
            )}
            
            {/* 已加载全部 */}
            {!hasMoreLogs && logs.length > 0 && (
              <div className="text-center text-[11px] text-nb-text-secondary py-2 mb-2">
                — 已加载全部日志 —
              </div>
            )}

            {/* 虚拟列表 */}
            <div
              style={{
                height: `${virtualizer.getTotalSize()}px`,
                position: 'relative',
                width: '100%',
              }}
            >
              {virtualizer.getVirtualItems().map((virtualRow) => {
                const log = logs[virtualRow.index];
                const logKey = log.id?.toString() || `${virtualRow.index}-${log.timestamp}`;
                const isExpanded = expandedLogs.has(logKey);
                
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
                    className="pb-2"
                  >
                    <LogCard
                      log={log}
                      isExpanded={isExpanded}
                      onToggle={() => toggleLogExpand(logKey)}
                      showSubagent={logSubagentId === null}
                    />
                  </div>
                );
              })}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
