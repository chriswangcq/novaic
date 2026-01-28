import { useState, Component, ReactNode, ErrorInfo } from 'react';
import { Message, AgentEvent } from '../../types';
import { ThinkingBlock } from './ThinkingBlock';
import { ToolCallCard } from './ToolCallCard';
import { Sparkles, Copy, Check, AlertTriangle } from 'lucide-react';

interface AssistantMessageProps {
  message: Message;
}

/**
 * Error Boundary for catching render errors
 */
interface ErrorBoundaryState {
  hasError: boolean;
  error?: Error;
}

class MessageErrorBoundary extends Component<{ children: ReactNode }, ErrorBoundaryState> {
  constructor(props: { children: ReactNode }) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('[AssistantMessage] Render error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex items-start gap-2 px-2.5 py-1.5 rounded bg-red-500/10 border border-red-500/20 text-red-400 text-[12px]">
          <AlertTriangle size={14} className="shrink-0 mt-0.5" />
          <div>
            <div className="font-medium">Render Error</div>
            <div className="text-[11px] opacity-70">{this.state.error?.message || 'Unknown error'}</div>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}

/**
 * 从 event.data 提取文本内容 (with safety checks)
 */
function extractContent(data: unknown): string {
  try {
    if (data === null || data === undefined) return '';
    if (typeof data === 'string') return data;
    if (typeof data === 'number' || typeof data === 'boolean') return String(data);
    if (data && typeof data === 'object') {
      const obj = data as Record<string, unknown>;
      const content = obj.content || obj.data || obj.text || obj.error || obj.message;
      if (content !== undefined && content !== null) {
        return typeof content === 'string' ? content : JSON.stringify(content);
      }
    }
    return '';
  } catch (e) {
    console.error('[extractContent] Error:', e);
    return '';
  }
}

/**
 * 查找 tool_start 对应的 tool_end
 */
function findToolEnd(events: AgentEvent[], startIndex: number, toolName: string): AgentEvent | undefined {
  for (let i = startIndex + 1; i < events.length; i++) {
    const event = events[i];
    if (event.type === 'tool_end') {
      const endTool = (event.data as Record<string, unknown>)?.tool;
      if (endTool === toolName) {
        return event;
      }
    }
  }
  return undefined;
}

export function AssistantMessage({ message }: AssistantMessageProps) {
  const events = message.events || [];
  const isStreaming = message.isStreaming;
  
  // 记录已处理的 tool_end 索引，避免重复渲染
  const processedToolEnds = new Set<number>();

  return (
    <MessageErrorBoundary>
      <div className="group py-2">
        {/* Header: icon + label */}
        <div className="flex items-center gap-1.5 mb-1">
          <Sparkles size={12} className="text-violet-400" />
          <span className="text-[11px] font-medium text-white/40 uppercase tracking-wide">Agent</span>
        </div>
        
        {/* 按事件顺序渲染 */}
        <div className="space-y-2 pl-[18px]">
          {events.map((event, index) => {
            try {
              if (!event || !event.type) return null;
              
              switch (event.type) {
                case 'thinking': {
                  const content = extractContent(event.data);
                  if (!content || content.length < 5) return null;
                  return <ThinkingBlock key={`thinking-${index}`} content={content} />;
                }
                
                case 'tool_start': {
                  const data = (event.data || {}) as Record<string, unknown>;
                  const toolName = String(data?.tool || 'unknown');
                  const toolInput = (data?.input && typeof data.input === 'object' ? data.input : {}) as Record<string, unknown>;
                  const toolId = String(data?.id || `tool-${index}`);
                  
                  // 查找对应的 tool_end
                  const toolEnd = findToolEnd(events, index, toolName);
                  const toolEndIndex = toolEnd ? events.indexOf(toolEnd) : -1;
                  if (toolEndIndex >= 0) {
                    processedToolEnds.add(toolEndIndex);
                  }
                  
                  const endData = (toolEnd?.data || {}) as Record<string, unknown>;
                  const resultData = (endData?.result && typeof endData.result === 'object' ? endData.result : undefined) as Record<string, unknown> | undefined;
                  const isSuccess = resultData?.success === true;
                  const isRunning = !toolEnd;
                  
                  return (
                    <ToolCallCard
                      key={`tool-${index}`}
                      toolCall={{
                        id: toolId,
                        tool: toolName,
                        input: toolInput,
                        status: isRunning ? 'running' : (isSuccess ? 'success' : 'error'),
                        result: resultData ? {
                          success: Boolean(resultData.success),
                          ...resultData,
                        } : undefined,
                        startTime: Date.now(),
                        endTime: toolEnd ? Date.now() : undefined,
                      }}
                    />
                  );
                }
                
                case 'tool_end': {
                  // 已经在 tool_start 中处理，跳过
                  return null;
                }
                
                case 'text':
                case 'final': {
                  const content = extractContent(event.data);
                  if (!content) return null;
                  return (
                    <div key={`text-${index}`} className="text-[13px] text-white/90 leading-relaxed whitespace-pre-wrap">
                      <FormattedText text={content} />
                    </div>
                  );
                }
                
                case 'warning': {
                  const content = extractContent(event.data);
                  return (
                    <div key={`warning-${index}`} className="flex items-start gap-2 px-2.5 py-1.5 rounded bg-yellow-500/10 border border-yellow-500/20 text-yellow-400 text-[12px]">
                      <span className="shrink-0">⚠</span>
                      <span>{content || 'Warning'}</span>
                    </div>
                  );
                }
                
                case 'error': {
                  const content = extractContent(event.data);
                  return (
                    <div key={`error-${index}`} className="flex items-start gap-2 px-2.5 py-1.5 rounded bg-red-500/10 border border-red-500/20 text-red-400 text-[12px]">
                      <span className="shrink-0">✕</span>
                      <span>{content || 'Error'}</span>
                    </div>
                  );
                }
                
                default:
                  return null;
              }
            } catch (e) {
              console.error(`[AssistantMessage] Error rendering event ${index}:`, e, event);
              return (
                <div key={`error-${index}`} className="text-[11px] text-red-400/60">
                  [Render error for event {index}]
                </div>
              );
            }
          })}
          
          {/* 最终响应（如果有且不在 events 中） */}
          {message.content && !events.some(e => e?.type === 'final') && (
            <div className="text-[13px] text-white/90 leading-relaxed whitespace-pre-wrap">
              <FormattedText text={message.content} />
            </div>
          )}
          
          {/* Streaming 指示器 */}
          {isStreaming && events.length === 0 && (
            <div className="flex items-center gap-1 text-white/30 text-[12px]">
              <span className="animate-pulse">●</span>
              <span className="animate-pulse" style={{ animationDelay: '150ms' }}>●</span>
              <span className="animate-pulse" style={{ animationDelay: '300ms' }}>●</span>
            </div>
          )}
        </div>
      </div>
    </MessageErrorBoundary>
  );
}

/**
 * Code block with language label and copy button (Cursor style)
 */
function CodeBlock({ code, language }: { code: string; language: string }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="my-2 rounded-md bg-[#1e1e1e] border border-white/[0.06] overflow-hidden group/code">
      {/* Header with language and copy button */}
      <div className="flex items-center justify-between px-3 py-1.5 bg-white/[0.02] border-b border-white/[0.04]">
        <span className="text-[10px] text-white/30 uppercase tracking-wider font-medium">{language}</span>
        <button
          onClick={handleCopy}
          className="flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] text-white/30 hover:text-white/60 hover:bg-white/[0.04] transition-colors"
        >
          {copied ? (
            <>
              <Check size={10} />
              <span>Copied</span>
            </>
          ) : (
            <>
              <Copy size={10} />
              <span>Copy</span>
            </>
          )}
        </button>
      </div>
      {/* Code content */}
      <pre className="px-3 py-2.5 overflow-x-auto">
        <code className="text-[12px] text-emerald-400/90 font-mono leading-relaxed">
          {code}
        </code>
      </pre>
    </div>
  );
}

/**
 * 文本格式化（处理代码块）- Cursor style
 */
function FormattedText({ text }: { text: string }) {
  const codeBlockRegex = /```(\w+)?\n?([\s\S]*?)```/g;
  const inlineCodeRegex = /`([^`]+)`/g;
  
  const parts: Array<{ type: 'text' | 'code-block'; content: string; language?: string }> = [];
  let lastIndex = 0;
  let match;
  
  while ((match = codeBlockRegex.exec(text)) !== null) {
    if (match.index > lastIndex) {
      parts.push({ type: 'text', content: text.slice(lastIndex, match.index) });
    }
    parts.push({ 
      type: 'code-block', 
      content: match[2].trim(), 
      language: match[1] || 'text' 
    });
    lastIndex = match.index + match[0].length;
  }
  
  if (lastIndex < text.length) {
    parts.push({ type: 'text', content: text.slice(lastIndex) });
  }
  
  return (
    <>
      {parts.map((part, i) => {
        if (part.type === 'code-block') {
          return <CodeBlock key={i} code={part.content} language={part.language || 'text'} />;
        }
        
        // Process inline code
        const textParts = part.content.split(inlineCodeRegex);
        return (
          <span key={i}>
            {textParts.map((t, j) => 
              j % 2 === 1 ? (
                <code key={j} className="px-1 py-0.5 rounded bg-white/[0.06] text-[12px] font-mono text-violet-300">
                  {t}
                </code>
              ) : t
            )}
          </span>
        );
      })}
    </>
  );
}
