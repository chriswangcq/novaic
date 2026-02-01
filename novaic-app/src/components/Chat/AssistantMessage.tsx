import { Component, ReactNode, ErrorInfo } from 'react';
import { Message, AgentEvent } from '../../types';
import { ThinkingBlock } from './ThinkingBlock';
import { ToolCallCard } from './ToolCallCard';
import { Markdown } from './Markdown';
import { Sparkles, AlertTriangle, ChevronDown } from 'lucide-react';
import { useAppStore } from '../../store';

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
  const expandMessage = useAppStore((state) => state.expandMessage);
  
  // 记录已处理的 tool_end 索引，避免重复渲染
  const processedToolEnds = new Set<number>();
  
  const handleExpand = () => {
    expandMessage(message.id);
  };

  return (
    <MessageErrorBoundary>
      <div className="group py-2">
        {/* Header: icon + label - left aligned */}
        <div className="flex items-center gap-1.5 mb-1">
          <Sparkles size={12} className="text-violet-400" />
          <span className="text-[11px] font-medium text-white/40 uppercase tracking-wide">Agent</span>
        </div>
        
        {/* Content with bubble style */}
        <div className="bg-white/[0.04] border border-white/[0.08] rounded-lg px-3 py-2 space-y-2">
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
                    <div key={`text-${index}`}>
                      <Markdown content={content} />
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
                
                case 'image': {
                  const data = (event.data || {}) as Record<string, unknown>;
                  const imageUrl = String(data?.image_url || data?.image_path || '');
                  const caption = String(data?.caption || '');
                  if (!imageUrl) return null;
                  return (
                    <div key={`image-${index}`} className="space-y-1">
                      <img 
                        src={imageUrl} 
                        alt={caption || 'Image'} 
                        className="max-w-full rounded-lg border border-white/10"
                        style={{ maxHeight: '400px', objectFit: 'contain' }}
                      />
                      {caption && (
                        <p className="text-[11px] text-white/50">{caption}</p>
                      )}
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
            <Markdown content={message.content} />
          )}
          
          {/* Expand button for truncated messages */}
          {message.isTruncated && (
            <button
              onClick={handleExpand}
              className="flex items-center gap-1 text-[11px] text-violet-400 hover:text-violet-300 transition-colors"
            >
              <ChevronDown size={14} />
              <span>查看更多</span>
            </button>
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

