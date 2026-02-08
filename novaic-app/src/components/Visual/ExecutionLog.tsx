import { useEffect, useLayoutEffect, useState, useCallback, useRef } from 'react';
import { LogEntry } from '../../types';
import { Rocket, CheckCircle, AlertCircle, Terminal, Loader2, Brain, Zap, XCircle, ChevronDown, ChevronRight, Copy, Check } from 'lucide-react';
import { useAppStore } from '../../store';
import { useVirtualList } from '../../hooks/useVirtualList';
import { useScrollPagination } from '../../hooks/useScrollPagination';
import { LOG_ESTIMATE_SIZE, LOG_OVERSCAN } from '../../constants/scroll';
import { UI_CONFIG } from '../../config';

interface ExecutionLogProps {
  logs: LogEntry[];
  isExecuting: boolean;
}

// 格式化 JSON 数据用于显示
const formatJsonForDisplay = (data: unknown, indent = 2): string => {
  if (data === null || data === undefined) return '';
  if (typeof data === 'string') return data;
  try {
    return JSON.stringify(data, null, indent);
  } catch {
    return String(data);
  }
};

// 截断字符串
const truncateString = (str: string, maxLength: number): string => {
  if (str.length <= maxLength) return str;
  return str.substring(0, maxLength) + '...';
};

// 详情展示组件
interface LogDetailProps {
  log: LogEntry;
  isExpanded: boolean;
  onToggle: () => void;
}

function LogDetail({ log, isExpanded, onToggle }: LogDetailProps) {
  const [copied, setCopied] = useState<string | null>(null);

  const copyToClipboard = useCallback((text: string, label: string) => {
    navigator.clipboard.writeText(text).then(() => {
      setCopied(label);
      setTimeout(() => setCopied(null), UI_CONFIG.COPY_FEEDBACK_DELAY);
    });
  }, []);

  // 提取 input 数据
  const getInputData = (): unknown => {
    if (log.input) return log.input;
    if (log.data?.input) return log.data.input;
    if (log.data?.args) return log.data.args;
    return null;
  };

  // 提取 result 数据
  const getResultData = (): unknown => {
    if (log.result) return log.result;
    if (log.data?.result) return log.data.result;
    return null;
  };

  // 提取思考内容
  const getThinkingContent = (): string => {
    if (log.result?.content && typeof log.result.content === 'string') return log.result.content;
    if (log.data?.content && typeof log.data.content === 'string') return log.data.content;
    if (typeof log.data === 'string') return log.data;
    return '';
  };

  // 提取错误信息
  const getErrorInfo = (): string | null => {
    if (log.result?.error && typeof log.result.error === 'string') return log.result.error;
    if (log.data?.error && typeof log.data.error === 'string') return log.data.error;
    if (log.data?.result && typeof log.data.result === 'object' && log.data.result !== null) {
      const resultObj = log.data.result as Record<string, unknown>;
      if (resultObj.error && typeof resultObj.error === 'string') {
        return resultObj.error;
      }
    }
    return null;
  };

  const input = getInputData();
  const result = getResultData();
  const thinkingContent = getThinkingContent();
  const error = getErrorInfo();

  // 判断是否有详情可展示
  const hasDetails = Boolean(
    (log.kind === 'think' && thinkingContent) ||
    (log.kind === 'tool' && (input || result)) ||
    (log.type === 'tool_start' && input) ||
    (log.type === 'tool_end' && result) ||
    error
  );

  if (!hasDetails) return null;

  return (
    <div className="mt-1">
      <button
        onClick={onToggle}
        className="flex items-center gap-1 text-[10px] text-nb-text-muted hover:text-nb-text transition-colors"
      >
        {isExpanded ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
        <span>{isExpanded ? '收起详情' : '展开详情'}</span>
      </button>

      {isExpanded && (
        <div className="mt-2 p-2 bg-nb-surface-2 rounded border border-nb-border text-[11px] space-y-2">
          {/* Think 类型显示思考内容 */}
          {log.kind === 'think' && !!thinkingContent && (
            <div>
              <div className="flex items-center justify-between mb-1">
                <span className="text-white/70 font-medium">💭 思考内容</span>
                <button
                  onClick={() => copyToClipboard(thinkingContent, 'thinking')}
                  className="p-1 hover:bg-nb-surface rounded"
                  title="复制"
                >
                  {copied === 'thinking' ? <Check size={12} className="text-nb-success" /> : <Copy size={12} />}
                </button>
              </div>
              <pre className="whitespace-pre-wrap text-nb-text-muted bg-nb-surface p-2 rounded max-h-40 overflow-auto">
                {thinkingContent}
              </pre>
            </div>
          )}

          {/* Tool 类型显示输入参数 */}
          {(log.kind === 'tool' || log.type === 'tool_start' || log.type === 'tool_end') && !!input && (
            <div>
              <div className="flex items-center justify-between mb-1">
                <span className="text-nb-accent font-medium">📥 输入参数</span>
                <button
                  onClick={() => copyToClipboard(formatJsonForDisplay(input), 'input')}
                  className="p-1 hover:bg-nb-surface rounded"
                  title="复制"
                >
                  {copied === 'input' ? <Check size={12} className="text-nb-success" /> : <Copy size={12} />}
                </button>
              </div>
              <pre className="whitespace-pre-wrap text-nb-text-muted bg-nb-surface p-2 rounded max-h-40 overflow-auto font-mono">
                {formatJsonForDisplay(input)}
              </pre>
            </div>
          )}

          {/* Tool 类型显示执行结果 */}
          {(log.kind === 'tool' || log.type === 'tool_end') && !!result && (
            <div>
              <div className="flex items-center justify-between mb-1">
                <span className={error ? 'text-nb-error font-medium' : 'text-nb-success font-medium'}>
                  {error ? '❌ 执行结果（错误）' : '📤 执行结果'}
                </span>
                <button
                  onClick={() => copyToClipboard(formatJsonForDisplay(result), 'result')}
                  className="p-1 hover:bg-nb-surface rounded"
                  title="复制"
                >
                  {copied === 'result' ? <Check size={12} className="text-nb-success" /> : <Copy size={12} />}
                </button>
              </div>
              <pre className={`whitespace-pre-wrap bg-nb-surface p-2 rounded max-h-40 overflow-auto font-mono ${error ? 'text-nb-error' : 'text-nb-text-muted'}`}>
                {formatJsonForDisplay(result)}
              </pre>
            </div>
          )}

          {/* 单独显示错误（如果有且未在 result 中显示） */}
          {!!error && !result && (
            <div>
              <span className="text-nb-error font-medium">❌ 错误信息</span>
              <pre className="whitespace-pre-wrap text-nb-error bg-nb-surface p-2 rounded mt-1">
                {error}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export function ExecutionLog({ logs, isExecuting }: ExecutionLogProps) {
  const { 
    currentAgentId, 
    logSubagentId, 
    logSubagents, 
    setLogSubagentId,
    hasMoreLogs,
    isLoadingMoreLogs,
    loadMoreLogs,
  } = useAppStore();
  
  // 记录展开状态的日志 ID
  const [expandedLogs, setExpandedLogs] = useState<Set<string>>(new Set());
  // 控制内容显示时机，避免用户看到滚动过程
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

  // 虚拟列表
  const { parentRef, virtualizer } = useVirtualList({
    count: logs.length,
    estimateSize: LOG_ESTIMATE_SIZE,
    overscan: LOG_OVERSCAN,
  });

  // 手动实现自动滚动逻辑
  const hasInitialScrolled = useRef(false);
  const prevLogsLengthRef = useRef(0); // 初始化为 0，用于检测"从无到有"
  const autoScrollEnabled = useRef(true); // 是否启用自动滚动
  const isAutoScrolling = useRef(false); // 是否正在执行自动滚动
  const isMounted = useRef(false); // 是否已经挂载

  // 判断是否在底部（使用更宽松的条件）
  const isAtBottom = useCallback(() => {
    const scrollElement = parentRef.current;
    if (!scrollElement) return false;
    
    const { scrollTop, scrollHeight, clientHeight } = scrollElement;
    const scrollBottom = scrollHeight - scrollTop - clientHeight;
    
    // 距离底部小于 200px 认为在底部（更宽松）
    return scrollBottom < 200;
  }, [parentRef]);

  // 监听用户滚动，更新自动滚动状态
  const handleUserScroll = useCallback(() => {
    // 如果正在自动滚动中，不更新状态（避免误判）
    if (isAutoScrolling.current) {
      return;
    }
    
    const atBottom = isAtBottom();
    if (atBottom !== autoScrollEnabled.current) {
      autoScrollEnabled.current = atBottom;
    }
  }, [isAtBottom]);

  // 分页加载
  const { handleScroll: handlePaginationScroll, firstVisibleIndexRef } = useScrollPagination({
    itemsLength: logs.length,
    virtualizer,
    hasMore: hasMoreLogs,
    isLoading: isLoadingMoreLogs,
    onLoadMore: loadMoreLogs,
    scrollThreshold: 100
  });

  // 组合滚动处理：分页 + 自动滚动状态更新
  const handleScroll = useCallback((e: React.UIEvent<HTMLDivElement>) => {
    handlePaginationScroll(e);
    handleUserScroll();
  }, [handlePaginationScroll, handleUserScroll]);

  // 组件挂载时的初始化
  useEffect(() => {
    isMounted.current = true;
    // 不管有没有日志，都让 line 280-295 的逻辑处理滚动
  }, []);


  // 切换 Agent 或 subagent tag 时重置并滚动
  useLayoutEffect(() => {
    // 重置所有状态
    hasInitialScrolled.current = false;
    prevLogsLengthRef.current = 0;
    autoScrollEnabled.current = true;
    firstVisibleIndexRef.current = null;
    setIsReady(false); // 先隐藏内容，等滚动完成后再显示
  }, [currentAgentId, logSubagentId]);
  
  // 初始滚动到底部（切换 agent 或首次加载数据时）
  useEffect(() => {
    if (!hasInitialScrolled.current && logs.length > 0) {
      const timer = setTimeout(() => {
        // 使用 requestAnimationFrame 确保虚拟列表已更新
        requestAnimationFrame(() => {
          virtualizer.scrollToIndex(logs.length - 1, { 
            align: 'end',
            behavior: 'auto'
          });
          hasInitialScrolled.current = true;
          prevLogsLengthRef.current = logs.length;
          setIsReady(true); // 滚动完成后再显示内容
        });
      }, 0);
      return () => clearTimeout(timer);
    } else if (logs.length === 0) {
      setIsReady(true); // 没有日志时直接显示
    }
  }, [logs.length, virtualizer]);

  // 新日志自动滚动（只在自动滚动启用时）
  useEffect(() => {
    // 只处理新日志到达的情况
    if (hasInitialScrolled.current && logs.length > prevLogsLengthRef.current && !isLoadingMoreLogs) {
      // 如果启用了自动滚动，就滚动到底部
      if (autoScrollEnabled.current) {
        isAutoScrolling.current = true;
        
        // 保存当前长度，避免在异步回调中闭包陷阱
        const targetLength = logs.length;
        
        // 使用三个 requestAnimationFrame 确保虚拟列表完全更新和测量完成后再滚动
        // 虚拟列表的 measureElement 需要时间测量新 item 的实际高度
        requestAnimationFrame(() => {
          requestAnimationFrame(() => {
            requestAnimationFrame(() => {
              // 直接滚动到底部，使用 auto 无动画
              virtualizer.scrollToIndex(targetLength - 1, { 
                align: 'end',
                behavior: 'auto'
              });
              
              // 更新 prevLogsLengthRef 在滚动执行后
              prevLogsLengthRef.current = targetLength;
              
              // 立即重置标志（auto 滚动是瞬时的，不需要延迟）
              isAutoScrolling.current = false;
              // 重新检查一次底部状态
              autoScrollEnabled.current = isAtBottom();
            });
          });
        });
      } else {
        // 如果没有启用自动滚动，也要更新 prevLogsLengthRef
        prevLogsLengthRef.current = logs.length;
      }
    }
    // 注意：不在 else 分支更新 prevLogsLengthRef，避免误更新
  }, [logs.length, virtualizer, isLoadingMoreLogs, isAtBottom]);

  const getLogIcon = (log: LogEntry, success?: boolean) => {
    // 如果有 kind 字段，优先使用 kind
    if (log.kind === 'think') {
      const error = log.result?.error || log.data?.error;
      // 根据 status 显示不同图标
      if (log.status === 'running') {
        return <Loader2 size={14} className="text-white/60 animate-spin" />;
      }
      if (log.status === 'failed' || error) {
        return <XCircle size={14} className="text-nb-error" />;
      }
      return <Brain size={14} className="text-white/60" />;
    }
    if (log.kind === 'tool') {
      // 根据 status 显示不同图标
      if (log.status === 'running') {
        return <Loader2 size={14} className="text-nb-accent animate-spin" />;
      }
      return success !== false 
        ? <CheckCircle size={14} className="text-nb-success" />
        : <XCircle size={14} className="text-nb-error" />;
    }

    // 兼容旧的 type 字段
    switch (log.type) {
      case 'tool_start':
        return <Rocket size={14} className="text-nb-accent" />;
      case 'tool_end':
        return success !== false 
          ? <CheckCircle size={14} className="text-nb-success" />
          : <XCircle size={14} className="text-nb-error" />;
      case 'thinking':
        return <Brain size={14} className="text-white/60" />;
      case 'status':
        return <Zap size={14} className="text-yellow-400" />;
      case 'error':
        return <AlertCircle size={14} className="text-nb-error" />;
      case 'stdout':
      case 'stderr':
        return <Terminal size={14} className="text-nb-text-muted" />;
      default:
        return <Terminal size={14} className="text-nb-text-muted" />;
    }
  };

  // 获取参数摘要（用于默认显示）
  const getParamsSummary = (input: unknown): string => {
    if (!input || typeof input !== 'object') return '';
    const inputObj = input as Record<string, unknown>;
    const keys = Object.keys(inputObj);
    if (keys.length === 0) return '';
    
    const params = keys.slice(0, 2).map(k => {
      const v = inputObj[k];
      let val: string;
      if (typeof v === 'string') {
        val = v.length > 30 ? v.substring(0, 30) + '...' : v;
      } else if (typeof v === 'number' || typeof v === 'boolean') {
        val = String(v);
      } else {
        val = JSON.stringify(v).substring(0, 30);
      }
      return `${k}=${val}`;
    }).join(', ');
    
    return params + (keys.length > 2 ? ` (+${keys.length - 2})` : '');
  };

  // 获取结果摘要
  const getResultSummary = (result: unknown, success?: boolean): string => {
    if (!result) return success !== false ? '完成' : '失败';
    
    if (typeof result === 'object') {
      const resultObj = result as Record<string, unknown>;
      if (resultObj.error) {
        return `错误: ${truncateString(String(resultObj.error), 50)}`;
      }
      if (resultObj.message) {
        return truncateString(String(resultObj.message), 50);
      }
      if (resultObj.url) {
        return `🔗 ${resultObj.url}`;
      }
      if (resultObj.output) {
        return truncateString(String(resultObj.output), 50);
      }
      if (resultObj.content) {
        return truncateString(String(resultObj.content), 50);
      }
      // 显示主要字段
      const keys = Object.keys(resultObj).filter(k => k !== 'success' && k !== 'done');
      if (keys.length > 0) {
        const firstKey = keys[0];
        const val = resultObj[firstKey];
        return `${firstKey}: ${truncateString(JSON.stringify(val), 40)}`;
      }
    }
    
    return success !== false ? '完成' : '失败';
  };

  const formatLog = (log: LogEntry): { main: string; detail?: string; toolName?: string; status?: string; isRunning?: boolean; isFailed?: boolean } => {
    // 新事件模型：根据 kind 和 status 显示
    if (log.kind === 'think') {
      const content = log.result?.content || log.data?.content || (typeof log.data === 'string' ? log.data : '');
      const error = log.result?.error || log.data?.error;
      
      if (log.status === 'running') {
        return { 
          main: '🧠 思考中...', 
          detail: content ? truncateString(content, 80) : undefined,
          isRunning: true 
        };
      }
      
      // failed 状态
      if (log.status === 'failed' || error) {
        return { 
          main: '🧠 思考失败',
          status: '失败',
          detail: error ? truncateString(String(error), 80) : undefined,
          isFailed: true
        };
      }
      
      // complete 状态
      return { 
        main: '🧠 思考完成',
        status: '完成',
        detail: content ? truncateString(content, 80) : undefined
      };
    }
    
    if (log.kind === 'tool') {
      const toolName = log.data?.tool || log.event_key || 'unknown';
      const input = log.input || log.data?.input;
      const result = log.result || log.data?.result;
      const success = log.data?.success ?? (result && !(result as Record<string, unknown>).error);
      
      if (log.status === 'running') {
        const paramsSummary = getParamsSummary(input);
        return { 
          main: `⚡ ${toolName}`, 
          toolName,
          status: '执行中',
          detail: paramsSummary || undefined,
          isRunning: true 
        };
      }
      
      // complete 状态
      const resultSummary = getResultSummary(result, success);
      const icon = success !== false ? '✓' : '✗';
      return { 
        main: `${icon} ${toolName}`, 
        toolName,
        status: success !== false ? '完成' : '失败',
        detail: resultSummary
      };
    }

    // 兼容旧的 type 字段
    switch (log.type) {
      case 'tool_start': {
        const toolName = log.data?.tool || 'unknown';
        const args = log.data?.args || log.data?.input;
        const paramsSummary = getParamsSummary(args);
        return { 
          main: `⚡ ${toolName}`, 
          toolName,
          status: '开始',
          detail: paramsSummary || undefined
        };
      }
      case 'tool_end': {
        const toolName = log.data?.tool || 'unknown';
        const success = log.data?.success;
        const result = log.data?.result;
        const resultSummary = getResultSummary(result, success);
        const icon = success !== false ? '✓' : '✗';
        return { 
          main: `${icon} ${toolName}`, 
          toolName,
          status: success !== false ? '完成' : '失败',
          detail: resultSummary
        };
      }
      case 'thinking': {
        const content = typeof log.data === 'string' ? log.data : (log.data?.content || '');
        return { 
          main: '🧠 思考',
          detail: content ? truncateString(content, 80) : undefined
        };
      }
      case 'status':
        return { main: log.data?.message || (typeof log.data === 'string' ? log.data : JSON.stringify(log.data)) };
      case 'stdout':
      case 'stderr':
        return { main: log.data?.output || (typeof log.data === 'string' ? log.data : '') };
      case 'progress':
        return { main: `Progress: ${log.data?.progress || 0}%` };
      case 'text':
        return { main: log.data?.content || (typeof log.data === 'string' ? log.data : JSON.stringify(log.data)) };
      case 'final':
        return { main: typeof log.data === 'string' ? log.data : (log.data?.content || JSON.stringify(log.data || '')) };
      case 'error':
        return { main: `❌ ${log.data?.error || log.data?.tool || ''}: ${typeof log.data === 'string' ? log.data : (log.data?.error || 'Unknown error')}` };
      case 'warning':
        return { main: typeof log.data === 'string' ? log.data : JSON.stringify(log.data) };
      default:
        return { main: typeof log.data === 'string' ? log.data : JSON.stringify(log.data).substring(0, 100) };
    }
  };

  const getLogClass = (type: string): string => {
    switch (type) {
      case 'tool_start':
        return 'text-nb-accent';
      case 'tool_end':
        return 'text-nb-success';
      case 'thinking':
        return 'text-white/60 italic';
      case 'status':
        return 'text-yellow-300';
      case 'error':
      case 'stderr':
        return 'text-nb-error';
      default:
        return 'text-nb-text';
    }
  };

  return (
    <div className="h-full flex flex-col bg-nb-bg">
      {/* Header - 合并标题和 subagent tabs */}
      <div className="h-8 px-3 flex items-center gap-2 bg-nb-surface border-b border-nb-border overflow-x-auto">
        <Terminal size={13} className="text-nb-text-muted shrink-0" />
        <span className="text-xs font-medium text-nb-text shrink-0">Execution Log</span>
        
        {isExecuting && (
          <span className="flex items-center gap-1 px-1.5 py-0.5 bg-nb-success/20 text-nb-success rounded text-[10px] shrink-0">
            <Loader2 size={10} className="animate-spin" />
            Running
          </span>
        )}

        {/* Subagent tabs inline */}
        {logSubagents.length > 0 && (
          <>
            <div className="w-px h-3.5 bg-nb-border mx-1 shrink-0" />
            <button
              className={`px-2 py-0.5 rounded text-[10px] font-medium transition-colors whitespace-nowrap shrink-0 ${
                logSubagentId === null 
                  ? 'bg-white/15 text-white' 
                  : 'bg-nb-surface-2 text-nb-text-muted hover:bg-nb-surface-2/80'
              }`}
              onClick={() => setLogSubagentId(null)}
            >
              全部
            </button>
            {logSubagents.map(id => (
              <button
                key={id}
                className={`px-2 py-0.5 rounded text-[10px] font-medium transition-colors whitespace-nowrap shrink-0 ${
                  logSubagentId === id 
                    ? 'bg-white/15 text-white' 
                    : 'bg-nb-surface-2 text-nb-text-muted hover:bg-nb-surface-2/80'
                }`}
                onClick={() => setLogSubagentId(id)}
              >
                {id}
              </button>
            ))}
          </>
        )}
      </div>

      {/* Log content - virtualized for large lists */}
      <div
        ref={parentRef}
        className={`flex-1 overflow-y-auto overflow-x-hidden p-4 font-mono text-xs ${isReady ? 'opacity-100' : 'opacity-0'}`}
        style={{ transition: 'none' }} // 不要过渡动画，直接切换
        onScroll={handleScroll}
      >
        {logs.length === 0 ? (
          <div className="text-nb-text-muted text-center py-8">
            <Terminal size={32} className="mx-auto mb-2 opacity-50" />
            {currentAgentId ? (
              <>
                <p>No execution logs yet</p>
                <p className="text-xs mt-1 opacity-50">
                  Logs will appear here when you send a message
                </p>
              </>
            ) : (
              <>
                <p>No agent selected</p>
                <p className="text-xs mt-1 opacity-50">
                  Select or create an agent to see execution logs
                </p>
              </>
            )}
          </div>
        ) : (
          <>
            {/* 加载更多指示器 */}
            {isLoadingMoreLogs && (
              <div className="flex justify-center py-2 mb-2">
                <Loader2 size={20} className="animate-spin text-nb-text-muted" />
                <span className="ml-2 text-xs text-nb-text-muted">加载历史日志...</span>
              </div>
            )}
            
            {/* 没有更多日志提示 */}
            {!hasMoreLogs && logs.length > 0 && (
              <div className="text-center text-xs text-nb-text-muted py-2 mb-2">
                — 已加载全部日志 —
              </div>
            )}

            <div
              style={{
                height: `${virtualizer.getTotalSize()}px`,
                position: 'relative',
                width: '100%',
              }}
            >
            {virtualizer.getVirtualItems().map((virtualRow) => {
              const log = logs[virtualRow.index];
              const formatted = formatLog(log);
              const success = log.type === 'tool_end' ? log.data?.success : (log.kind === 'tool' && log.status === 'complete' ? log.data?.success : undefined);
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
                  className={`py-2 px-1 ${getLogClass(log.type)} hover:bg-nb-surface-2/50 rounded transition-colors`}
                >
                  {/* 新布局：第一行放时间戳 + 名字 + 状态 */}
                  <div className="space-y-1.5">
                    {/* 第一行：时间戳 + 图标 + 名字（左）+ 状态标签（右）*/}
                    <div className="flex items-center justify-between gap-2">
                      <div className="flex items-center gap-2 flex-shrink-0">
                        <span className="text-nb-text-muted text-[10px] font-mono">
                          {new Date(log.timestamp).toLocaleTimeString()}
                        </span>
                        <span className="flex-shrink-0">{getLogIcon(log, success)}</span>
                        <span className="font-medium">{formatted.main}</span>
                        {/* 显示 subagent_id 标签 */}
                        {log.subagent_id && logSubagentId === null && (
                          <span className="px-1.5 py-0.5 bg-white/10 text-white/60 text-[10px] rounded">
                            {log.subagent_id}
                          </span>
                        )}
                      </div>
                      {/* 状态标签放在右边 */}
                      {formatted.status && (
                        <span className={`px-2 py-0.5 rounded text-[10px] flex-shrink-0 ${
                          formatted.isRunning 
                            ? 'bg-white/10 text-white/70' 
                            : formatted.isFailed || formatted.status === '失败' 
                              ? 'bg-nb-error/20 text-nb-error'
                              : 'bg-nb-success/20 text-nb-success'
                        }`}>
                          {formatted.status}
                        </span>
                      )}
                    </div>
                    
                    {/* 第二行：摘要信息（全宽，不锁紧）*/}
                    {formatted.detail && (
                      <div className="text-[11px] text-nb-text-muted break-all leading-relaxed pl-0">
                        {formatted.detail}
                      </div>
                    )}
                    
                    {/* 可展开的详情（全宽）*/}
                    <LogDetail 
                      log={log} 
                      isExpanded={isExpanded}
                      onToggle={() => toggleLogExpand(logKey)}
                    />
                  </div>
                </div>
              );
            })}
            </div>
          </>
        )}

        {/* Progress bar when executing */}
        {isExecuting && (
          <div className="mt-4 h-1 bg-nb-surface-2 rounded-full overflow-hidden">
            <div
              className="h-full bg-white/20 animate-pulse"
              style={{ width: '60%' }}
            />
          </div>
        )}
      </div>
    </div>
  );
}

