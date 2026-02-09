import { useEffect, useLayoutEffect, useState, useCallback, useRef, useMemo } from 'react';
import { createPortal } from 'react-dom';
import { LogEntry } from '../../types';
import { CheckCircle, Terminal, Loader2, Brain, XCircle, ChevronDown, ChevronRight, Sparkles, Maximize2, X, Copy, Check, Wrench, Image as ImageIcon } from 'lucide-react';
import { useAppStore } from '../../store';
import { useVirtualList } from '../../hooks/useVirtualList';
import { useScrollPagination } from '../../hooks/useScrollPagination';
import { LOG_ESTIMATE_SIZE, LOG_OVERSCAN } from '../../constants/scroll';
import { SmartValue } from './SmartValue';
import { formatTime } from '../../utils/time';

// ==================== LLM Message Types ====================

// OpenAI 多模态 content 格式
type ContentPart = 
  | { type: 'text'; text: string }
  | { type: 'image_url'; image_url: { url: string; detail?: string } };

// LLM 消息格式（完整）
interface LLMMessage {
  role: string;
  content?: string | ContentPart[];
  tool_calls?: Array<{
    id: string;
    type: string;
    function: { name: string; arguments: string };
  }>;
  tool_call_id?: string;  // tool role 消息
  name?: string;          // tool role 消息的工具名
}

// ==================== Helper Functions ====================

/**
 * 解析消息内容，返回用于显示的信息
 * - 处理字符串和数组格式的 content
 * - 处理 tool_calls
 * - 图片数据用占位符替代（避免渲染卡顿）
 */
function parseMessageContent(msg: LLMMessage): {
  displayText: string;
  hasImages: boolean;
  imageCount: number;
  hasToolCalls: boolean;
  toolCallNames: string[];
  rawSize: number;
} {
  let displayText = '';
  let hasImages = false;
  let imageCount = 0;
  let rawSize = 0;
  const hasToolCalls = !!(msg.tool_calls && msg.tool_calls.length > 0);
  const toolCallNames = msg.tool_calls?.map(tc => tc.function?.name) || [];

  // 处理 content
  if (typeof msg.content === 'string') {
    displayText = msg.content;
    rawSize = msg.content.length;
  } else if (Array.isArray(msg.content)) {
    // 多模态 content 数组
    const textParts: string[] = [];
    for (const part of msg.content) {
      if (part.type === 'text') {
        textParts.push(part.text);
        rawSize += part.text.length;
      } else if (part.type === 'image_url') {
        hasImages = true;
        imageCount++;
        const url = part.image_url?.url || '';
        // 计算原始大小（base64 数据）
        if (url.startsWith('data:')) {
          const base64Part = url.split(',')[1] || '';
          rawSize += base64Part.length;
          textParts.push(`[IMAGE ${imageCount}: ${(base64Part.length / 1024).toFixed(1)}KB base64]`);
        } else {
          rawSize += url.length;
          textParts.push(`[IMAGE ${imageCount}: ${url.slice(0, 100)}${url.length > 100 ? '...' : ''}]`);
        }
      }
    }
    displayText = textParts.join('\n\n');
  }

  // 处理 tool_calls
  if (hasToolCalls && !displayText) {
    displayText = `[Tool Calls: ${toolCallNames.join(', ')}]\n\n${JSON.stringify(msg.tool_calls, null, 2)}`;
    rawSize = JSON.stringify(msg.tool_calls).length;
  } else if (hasToolCalls) {
    displayText += `\n\n[Tool Calls: ${toolCallNames.join(', ')}]\n${JSON.stringify(msg.tool_calls, null, 2)}`;
    rawSize += JSON.stringify(msg.tool_calls).length;
  }

  // tool role 消息
  if (msg.role === 'tool' && msg.tool_call_id) {
    const prefix = `[Tool Result for: ${msg.tool_call_id}${msg.name ? ` (${msg.name})` : ''}]\n\n`;
    displayText = prefix + displayText;
  }

  return {
    displayText: displayText || '(empty)',
    hasImages,
    imageCount,
    hasToolCalls,
    toolCallNames,
    rawSize,
  };
}

/**
 * 获取消息的原始 JSON（用于复制）
 * 图片数据截断以避免复制过大内容
 */
function getMessageJson(msg: LLMMessage, truncateImages = true): string {
  if (!truncateImages) {
    return JSON.stringify(msg, null, 2);
  }
  
  // 深拷贝并截断图片数据
  const clone = JSON.parse(JSON.stringify(msg));
  if (Array.isArray(clone.content)) {
    for (const part of clone.content) {
      if (part.type === 'image_url' && part.image_url?.url?.startsWith('data:')) {
        const [prefix] = part.image_url.url.split(',');
        part.image_url.url = `${prefix},[BASE64_DATA_TRUNCATED]`;
      }
    }
  }
  return JSON.stringify(clone, null, 2);
}

// ==================== Tool Result Content ====================

interface ToolResultContentProps {
  content?: string | ContentPart[];
  toolCallId?: string;
  toolName?: string;
}

/**
 * 渲染 tool role 消息的内容
 * - 尝试解析 JSON 并用 SmartValue 渲染（支持树形展开和图片预览）
 * - 如果不是 JSON，则显示纯文本
 */
function ToolResultContent({ content, toolCallId, toolName }: ToolResultContentProps) {
  // 提取文本内容
  let textContent = '';
  if (typeof content === 'string') {
    textContent = content;
  } else if (Array.isArray(content)) {
    // 多模态 content，提取 text 部分
    textContent = content
      .filter((part): part is { type: 'text'; text: string } => part.type === 'text')
      .map(part => part.text)
      .join('\n');
  }

  // 尝试解析 JSON
  let parsedJson: unknown = null;
  let isJson = false;
  
  if (textContent) {
    try {
      parsedJson = JSON.parse(textContent);
      isJson = typeof parsedJson === 'object' && parsedJson !== null;
    } catch {
      // 不是 JSON，保持 isJson = false
    }
  }

  return (
    <div className="space-y-2">
      {/* Tool Call ID 信息 */}
      {(toolCallId || toolName) && (
        <div className="text-[10px] text-purple-400/70 mb-2">
          {toolName && <span className="font-medium">{toolName}</span>}
          {toolCallId && <span className="text-nb-text-muted ml-2">({toolCallId})</span>}
        </div>
      )}
      
      {/* 内容渲染 */}
      {isJson ? (
        // JSON 用 SmartValue 渲染（树形展开 + 图片预览）
        <SmartValue value={parsedJson} copyable={false} />
      ) : (
        // 非 JSON 用纯文本
        <pre className="text-[11px] text-nb-text-muted whitespace-pre-wrap break-words font-mono leading-relaxed">
          {textContent || '(empty)'}
        </pre>
      )}
    </div>
  );
}

// ==================== LLM Input Modal ====================

interface LLMInputModalProps {
  isOpen: boolean;
  onClose: () => void;
  messages: LLMMessage[];
  model?: string;
  tools?: Array<{ type: string; function: { name: string; description: string; parameters: unknown } }>;
  provider?: string;
}

function LLMInputModal({ isOpen, onClose, messages, model, tools, provider }: LLMInputModalProps) {
  const [copied, setCopied] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'messages' | 'tools'>('messages');

  // 预解析所有消息（只在 messages 变化时重新计算）
  const parsedMessages = useMemo(() => {
    return messages.map(msg => ({
      original: msg,
      parsed: parseMessageContent(msg),
    }));
  }, [messages]);

  // 统计信息
  const stats = useMemo(() => {
    let totalImages = 0;
    let totalSize = 0;
    for (const { parsed } of parsedMessages) {
      totalImages += parsed.imageCount;
      totalSize += parsed.rawSize;
    }
    return { totalImages, totalSize };
  }, [parsedMessages]);

  const copyToClipboard = async (text: string, key: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(key);
      setTimeout(() => setCopied(null), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  const copyFullRequest = () => {
    // 复制完整请求（截断图片数据）
    const request = {
      model,
      provider,
      messages: messages.map(msg => JSON.parse(getMessageJson(msg, true))),
      tools,
    };
    copyToClipboard(JSON.stringify(request, null, 2), 'request');
  };

  if (!isOpen) return null;

  const modalContent = (
    <div className="fixed inset-0 z-[9999] flex items-center justify-center">
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-black/70 backdrop-blur-sm"
        onClick={onClose}
      />
      
      {/* Modal */}
      <div className="relative w-[95vw] max-w-5xl h-[90vh] bg-nb-surface rounded-xl border border-nb-border shadow-2xl flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-nb-border shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-blue-500/20 flex items-center justify-center">
              <Terminal size={16} className="text-blue-400" />
            </div>
            <div>
              <h3 className="text-sm font-medium text-nb-text">LLM 调用完整入参</h3>
              <div className="flex items-center gap-2 mt-0.5 flex-wrap">
                {provider && (
                  <span className="text-[10px] text-nb-text-secondary bg-nb-surface-2 px-1.5 py-0.5 rounded">
                    {provider}
                  </span>
                )}
                {model && (
                  <span className="text-[10px] text-nb-text-secondary bg-nb-surface-2 px-1.5 py-0.5 rounded">
                    {model}
                  </span>
                )}
                <span className="text-[10px] text-nb-text-secondary">
                  {messages.length} 条消息
                </span>
                {tools && tools.length > 0 && (
                  <span className="text-[10px] text-nb-text-secondary">
                    · {tools.length} 个工具
                  </span>
                )}
                {stats.totalImages > 0 && (
                  <span className="text-[10px] text-cyan-400 flex items-center gap-1">
                    <ImageIcon size={10} />
                    {stats.totalImages} 张图片
                  </span>
                )}
                <span className="text-[10px] text-nb-text-muted">
                  ~{(stats.totalSize / 1024).toFixed(1)}KB
                </span>
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={copyFullRequest}
              className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-md text-[11px] text-nb-text-muted hover:text-nb-text hover:bg-nb-hover transition-colors"
              title="复制完整请求 JSON（图片数据已截断）"
            >
              {copied === 'request' ? <Check size={12} className="text-nb-success" /> : <Copy size={12} />}
              复制请求
            </button>
            <button
              onClick={onClose}
              className="w-8 h-8 rounded-lg flex items-center justify-center text-nb-text-secondary hover:text-nb-text hover:bg-nb-hover transition-colors"
            >
              <X size={16} />
            </button>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex items-center gap-1 px-4 py-2 border-b border-nb-border shrink-0">
          <button
            onClick={() => setActiveTab('messages')}
            className={`px-3 py-1.5 rounded-md text-[11px] font-medium transition-colors ${
              activeTab === 'messages' 
                ? 'bg-blue-500/20 text-blue-400' 
                : 'text-nb-text-secondary hover:text-nb-text hover:bg-nb-hover'
            }`}
          >
            <span className="flex items-center gap-1.5">
              <Terminal size={12} />
              Messages ({messages.length})
            </span>
          </button>
          {tools && tools.length > 0 && (
            <button
              onClick={() => setActiveTab('tools')}
              className={`px-3 py-1.5 rounded-md text-[11px] font-medium transition-colors ${
                activeTab === 'tools' 
                  ? 'bg-orange-500/20 text-orange-400' 
                  : 'text-nb-text-secondary hover:text-nb-text hover:bg-nb-hover'
              }`}
            >
              <span className="flex items-center gap-1.5">
                <Wrench size={12} />
                Tools ({tools.length})
              </span>
            </button>
          )}
        </div>
        
        {/* Content */}
        <div className="flex-1 overflow-y-auto p-4 space-y-3">
          {activeTab === 'messages' && parsedMessages.map(({ original, parsed }, idx) => (
            <div 
              key={idx} 
              className={`rounded-lg border ${
                original.role === 'system' ? 'bg-amber-500/5 border-amber-500/20' : 
                original.role === 'user' ? 'bg-blue-500/5 border-blue-500/20' : 
                original.role === 'assistant' ? 'bg-green-500/5 border-green-500/20' :
                original.role === 'tool' ? 'bg-purple-500/5 border-purple-500/20' : 
                'bg-nb-surface-2 border-nb-border/30'
              }`}
            >
              <div className={`flex items-center justify-between px-3 py-2 border-b ${
                original.role === 'system' ? 'border-amber-500/20' : 
                original.role === 'user' ? 'border-blue-500/20' : 
                original.role === 'assistant' ? 'border-green-500/20' :
                original.role === 'tool' ? 'border-purple-500/20' : 
                'border-nb-border/30'
              }`}>
                <div className="flex items-center gap-2 flex-wrap">
                  <span className={`text-[10px] font-semibold ${
                    original.role === 'system' ? 'text-amber-400' : 
                    original.role === 'user' ? 'text-blue-400' : 
                    original.role === 'assistant' ? 'text-green-400' :
                    original.role === 'tool' ? 'text-purple-400' : 
                    'text-nb-text-secondary'
                  }`}>
                    {original.role.toUpperCase()}
                  </span>
                  {parsed.hasToolCalls && (
                    <span className="text-[9px] text-orange-400 bg-orange-500/10 px-1.5 py-0.5 rounded">
                      +tool_calls
                    </span>
                  )}
                  {parsed.hasImages && (
                    <span className="text-[9px] text-cyan-400 bg-cyan-500/10 px-1.5 py-0.5 rounded flex items-center gap-1">
                      <ImageIcon size={9} />
                      {parsed.imageCount}
                    </span>
                  )}
                  <span className="text-[10px] text-nb-text-secondary">
                    #{idx + 1} · {(parsed.rawSize / 1024).toFixed(1)}KB
                  </span>
                </div>
                <button
                  onClick={() => copyToClipboard(getMessageJson(original, false), `msg-${idx}`)}
                  className="text-nb-text-secondary hover:text-nb-text transition-colors"
                  title="复制原始 JSON"
                >
                  {copied === `msg-${idx}` ? <Check size={12} className="text-nb-success" /> : <Copy size={12} />}
                </button>
              </div>
              <div className="p-3 max-h-[400px] overflow-y-auto">
                {/* tool role 消息尝试用 SmartValue 渲染（支持 JSON 树形展开和图片预览） */}
                {original.role === 'tool' ? (
                  <ToolResultContent content={original.content} toolCallId={original.tool_call_id} toolName={original.name} />
                ) : (
                  <pre className="text-[11px] text-nb-text-muted whitespace-pre-wrap break-words font-mono leading-relaxed">
                    {parsed.displayText}
                  </pre>
                )}
              </div>
            </div>
          ))}

          {activeTab === 'tools' && tools && tools.map((tool, idx) => (
            <div key={idx} className="rounded-lg border bg-orange-500/5 border-orange-500/20">
              <div className="flex items-center justify-between px-3 py-2 border-b border-orange-500/20">
                <div className="flex items-center gap-2">
                  <Wrench size={12} className="text-orange-400" />
                  <span className="text-[11px] font-semibold text-orange-400">
                    {tool.function?.name || 'unknown'}
                  </span>
                </div>
                <button
                  onClick={() => copyToClipboard(JSON.stringify(tool, null, 2), `tool-${idx}`)}
                  className="text-nb-text-secondary hover:text-nb-text transition-colors"
                >
                  {copied === `tool-${idx}` ? <Check size={12} className="text-nb-success" /> : <Copy size={12} />}
                </button>
              </div>
              <div className="p-3 space-y-2">
                {tool.function?.description && (
                  <p className="text-[11px] text-nb-text-muted">{tool.function.description}</p>
                )}
                {tool.function?.parameters ? (
                  <details className="group">
                    <summary className="text-[10px] text-nb-text-secondary cursor-pointer hover:text-nb-text">
                      Parameters Schema
                    </summary>
                    <pre className="mt-2 text-[10px] text-nb-text-secondary font-mono bg-nb-bg p-2 rounded overflow-x-auto max-h-[300px] overflow-y-auto">
                      {JSON.stringify(tool.function.parameters, null, 2)}
                    </pre>
                  </details>
                ) : null}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );

  // 使用 Portal 渲染到 body，确保在最上层
  return createPortal(modalContent, document.body);
}

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
  const [showLLMModal, setShowLLMModal] = useState(false);

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

  // 获取 LLM 输入（完整入参：messages, model, tools, provider）
  // messages 中的 content 可能是 string 或 ContentPart[]（多模态）
  interface LLMInputData {
    messages?: LLMMessage[];
    model?: string;
    tools?: Array<{ type: string; function: { name: string; description: string; parameters: unknown } }>;
    provider?: string;
  }
  const getLLMInput = (): LLMInputData | null => {
    if (log.input?.messages) return log.input as LLMInputData;
    if (log.data?.input?.messages) return log.data.input as LLMInputData;
    return null;
  };

  const input = getInputData();
  const result = getResultData();
  const thinkingContent = getThinkingContent();
  const llmInput = getLLMInput();
  const toolName = log.data?.tool || log.event_key || '';
  const isThink = log.kind === 'think' || log.type === 'thinking';
  const isTool = log.kind === 'tool' || log.type === 'tool_start' || log.type === 'tool_end';
  const isRunning = log.status === 'running';
  const isFailed = log.status === 'failed' || log.data?.success === false || !!(log.result?.error || log.data?.error);
  
  const hasDetails = Boolean(
    (isThink && (thinkingContent || llmInput)) ||
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
          
          {/* LLM 输入（messages） */}
          {isThink && llmInput?.messages ? (
            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-1.5 text-[10px] text-blue-400/70 font-medium">
                  <Terminal size={10} />
                  <span>LLM 输入</span>
                  {llmInput.provider && (
                    <span className="px-1.5 py-0.5 bg-nb-surface-2 text-nb-text-secondary text-[9px] rounded">
                      {llmInput.provider}
                    </span>
                  )}
                  {llmInput.model && (
                    <span className="px-1.5 py-0.5 bg-nb-surface-2 text-nb-text-secondary text-[9px] rounded">
                      {llmInput.model}
                    </span>
                  )}
                  <span className="text-nb-text-secondary text-[9px]">
                    {llmInput.messages.length} 条消息
                  </span>
                  {llmInput.tools && llmInput.tools.length > 0 && (
                    <span className="text-nb-text-secondary text-[9px]">
                      · {llmInput.tools.length} 个工具
                    </span>
                  )}
                </div>
                <button
                  onClick={(e) => { e.stopPropagation(); setShowLLMModal(true); }}
                  className="flex items-center gap-1 px-2 py-1 rounded text-[10px] text-nb-text-secondary hover:text-nb-text hover:bg-nb-hover transition-colors"
                >
                  <Maximize2 size={10} />
                  <span>展开查看</span>
                </button>
              </div>
              <div className="bg-nb-bg rounded-md border border-nb-border/30 max-h-[200px] overflow-y-auto">
                {llmInput.messages.slice(0, 5).map((msg, idx) => {
                  // 使用 parseMessageContent 处理多模态内容
                  const parsed = parseMessageContent(msg);
                  return (
                    <div key={idx} className={`p-2 border-b border-nb-border/20 last:border-b-0 ${
                      msg.role === 'system' ? 'bg-amber-500/5' : 
                      msg.role === 'user' ? 'bg-blue-500/5' : 
                      msg.role === 'assistant' ? 'bg-green-500/5' : 
                      msg.role === 'tool' ? 'bg-purple-500/5' : ''
                    }`}>
                      <div className={`text-[9px] font-medium mb-1 flex items-center gap-1.5 ${
                        msg.role === 'system' ? 'text-amber-400/70' : 
                        msg.role === 'user' ? 'text-blue-400/70' : 
                        msg.role === 'assistant' ? 'text-green-400/70' : 
                        msg.role === 'tool' ? 'text-purple-400/70' : 'text-nb-text-secondary'
                      }`}>
                        <span>{msg.role.toUpperCase()}</span>
                        {parsed.hasToolCalls && <span className="text-orange-400">[+tools]</span>}
                        {parsed.hasImages && <span className="text-cyan-400">[+{parsed.imageCount}img]</span>}
                        <span className="text-nb-text-muted">· {(parsed.rawSize / 1024).toFixed(1)}KB</span>
                      </div>
                      <div className="text-[11px] text-nb-text-muted whitespace-pre-wrap break-words line-clamp-3">
                        {parsed.displayText.length > 300 ? parsed.displayText.slice(0, 300) + '...' : parsed.displayText}
                      </div>
                    </div>
                  );
                })}
                {llmInput.messages.length > 5 && (
                  <div className="p-2 text-center text-[10px] text-nb-text-secondary">
                    还有 {llmInput.messages.length - 5} 条消息，点击"展开查看"查看全部
                  </div>
                )}
              </div>
            </div>
          ) : null}
          
          {/* LLM Input Modal - 使用 Portal 渲染到 body 最上层 */}
          {isThink && llmInput?.messages && (
            <LLMInputModal
              isOpen={showLLMModal}
              onClose={() => setShowLLMModal(false)}
              messages={llmInput.messages}
              model={llmInput.model}
              tools={llmInput.tools}
              provider={llmInput.provider}
            />
          )}

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
