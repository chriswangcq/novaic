import { useEffect, useRef, useState, useCallback } from 'react';
import { useVirtualizer } from '@tanstack/react-virtual';
import { LogEntry } from '../../types';
import { Trash2, Rocket, CheckCircle, AlertCircle, Terminal, Loader2, Brain, Zap, XCircle, ChevronDown, ChevronRight, Copy, Check } from 'lucide-react';
import { useAppStore } from '../../store';

const LOG_ESTIMATE_SIZE = 72;
const OVERSCAN = 8;

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
      setTimeout(() => setCopied(null), 2000);
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
                <span className="text-purple-400 font-medium">💭 思考内容</span>
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
  const parentRef = useRef<HTMLDivElement>(null);
  const { clearLogs, currentAgentId, logSubagentId, logSubagents, setLogSubagentId } = useAppStore();
  const prevLengthRef = useRef(logs.length);
  
  // 记录展开状态的日志 ID
  const [expandedLogs, setExpandedLogs] = useState<Set<string>>(new Set());
  
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

  const virtualizer = useVirtualizer({
    count: logs.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => LOG_ESTIMATE_SIZE,
    overscan: OVERSCAN,
  });

  // Auto-scroll to bottom when new logs arrive (user is at bottom)
  useEffect(() => {
    if (logs.length <= prevLengthRef.current) {
      prevLengthRef.current = logs.length;
      return;
    }
    prevLengthRef.current = logs.length;
    const el = parentRef.current;
    if (!el) return;
    const threshold = 80;
    const atBottom = el.scrollHeight - el.scrollTop - el.clientHeight < threshold;
    if (atBottom) {
      requestAnimationFrame(() => {
        el.scrollTop = el.scrollHeight;
      });
    }
  }, [logs.length]);

  const getLogIcon = (log: LogEntry, success?: boolean) => {
    // 如果有 kind 字段，优先使用 kind
    if (log.kind === 'think') {
      // 根据 status 显示不同图标
      if (log.status === 'running') {
        return <Loader2 size={14} className="text-purple-400 animate-spin" />;
      }
      return <Brain size={14} className="text-purple-400" />;
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
        return <Brain size={14} className="text-purple-400" />;
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

  const formatLog = (log: LogEntry): { main: string; detail?: string; toolName?: string; status?: string; isRunning?: boolean } => {
    // 新事件模型：根据 kind 和 status 显示
    if (log.kind === 'think') {
      const content = log.result?.content || log.data?.content || (typeof log.data === 'string' ? log.data : '');
      if (log.status === 'running') {
        return { 
          main: '🧠 思考中...', 
          detail: content ? truncateString(content, 80) : undefined,
          isRunning: true 
        };
      }
      // complete 状态
      return { 
        main: '🧠 思考完成',
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
        return 'text-purple-300 italic';
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
      {/* Header */}
      <div className="h-10 px-4 flex items-center gap-2 bg-nb-surface border-b border-nb-border">
        <Terminal size={16} className="text-nb-text-muted" />
        <span className="text-sm font-medium text-nb-text">Execution Log</span>
        
        {isExecuting && (
          <span className="flex items-center gap-1.5 px-2 py-0.5 bg-nb-success/20 text-nb-success rounded text-xs">
            <Loader2 size={12} className="animate-spin" />
            Running
          </span>
        )}

        <div className="flex-1" />

        <button
          onClick={clearLogs}
          className="p-1.5 hover:bg-nb-surface-2 rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          title={currentAgentId ? "Clear logs" : "No agent selected"}
          disabled={!currentAgentId || logs.length === 0}
        >
          <Trash2 size={14} className="text-nb-text-muted" />
        </button>
      </div>

      {/* Subagent Tabs */}
      {logSubagents.length > 0 && (
        <div className="px-4 py-2 flex gap-2 border-b border-nb-border bg-nb-surface overflow-x-auto">
          <button
            className={`px-3 py-1 rounded text-xs font-medium transition-colors whitespace-nowrap ${
              logSubagentId === null 
                ? 'bg-blue-500 text-white' 
                : 'bg-nb-surface-2 text-nb-text-muted hover:bg-nb-surface-2/80'
            }`}
            onClick={() => setLogSubagentId(null)}
          >
            全部
          </button>
          {logSubagents.map(id => (
            <button
              key={id}
              className={`px-3 py-1 rounded text-xs font-medium transition-colors whitespace-nowrap ${
                logSubagentId === id 
                  ? 'bg-blue-500 text-white' 
                  : 'bg-nb-surface-2 text-nb-text-muted hover:bg-nb-surface-2/80'
              }`}
              onClick={() => setLogSubagentId(id)}
            >
              {id}
            </button>
          ))}
        </div>
      )}

      {/* Log content - virtualized for large lists */}
      <div
        ref={parentRef}
        className="flex-1 overflow-y-auto overflow-x-hidden p-4 font-mono text-xs"
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
                  {/* 主要信息行 */}
                  <div className="flex items-start gap-2">
                    <span className="flex-shrink-0 mt-0.5">{getLogIcon(log, success)}</span>
                    <span className="text-nb-text-muted w-14 flex-shrink-0 text-[10px] font-mono">
                      {new Date(log.timestamp).toLocaleTimeString()}
                    </span>
                    <div className="flex-1 min-w-0">
                      {/* 第一行：工具名/类型 + 状态标签 */}
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="font-medium">{formatted.main}</span>
                        {formatted.status && (
                          <span className={`px-1.5 py-0.5 rounded text-[10px] ${
                            formatted.isRunning 
                              ? 'bg-blue-500/20 text-blue-400' 
                              : formatted.status === '失败' 
                                ? 'bg-nb-error/20 text-nb-error'
                                : 'bg-nb-success/20 text-nb-success'
                          }`}>
                            {formatted.status}
                          </span>
                        )}
                        {/* 显示 subagent_id 标签 */}
                        {log.subagent_id && logSubagentId === null && (
                          <span className="px-1.5 py-0.5 bg-purple-500/20 text-purple-400 text-[10px] rounded">
                            {log.subagent_id}
                          </span>
                        )}
                      </div>
                      
                      {/* 第二行：摘要信息 */}
                      {formatted.detail && (
                        <div className="text-[11px] text-nb-text-muted mt-1 break-all leading-relaxed">
                          {formatted.detail}
                        </div>
                      )}
                      
                      {/* 可展开的详情 */}
                      <LogDetail 
                        log={log} 
                        isExpanded={isExpanded}
                        onToggle={() => toggleLogExpand(logKey)}
                      />
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* Progress bar when executing */}
        {isExecuting && (
          <div className="mt-4 h-1 bg-nb-surface-2 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-nb-accent to-purple-500 animate-pulse"
              style={{ width: '60%' }}
            />
          </div>
        )}
      </div>
    </div>
  );
}

