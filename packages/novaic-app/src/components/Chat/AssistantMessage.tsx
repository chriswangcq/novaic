import { Message, AgentEvent } from '../../types';
import { ThinkingBlock } from './ThinkingBlock';
import { ToolCallCard } from './ToolCallCard';
import { Sparkles } from 'lucide-react';

interface AssistantMessageProps {
  message: Message;
}

/**
 * 从 event.data 提取文本内容
 */
function extractContent(data: unknown): string {
  if (typeof data === 'string') return data;
  if (data && typeof data === 'object') {
    const obj = data as Record<string, unknown>;
    return String(obj.content || obj.data || obj.text || obj.error || '');
  }
  return '';
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
    <div className="group">
      {/* Assistant label */}
      <div className="flex items-center gap-2 mb-2">
        <div className="w-5 h-5 rounded-md bg-gradient-to-br from-violet-500 to-violet-600 flex items-center justify-center">
          <Sparkles size={12} className="text-white" />
        </div>
        <span className="text-xs font-medium text-white/40">Agent</span>
        <span className="text-xs text-white/20">
          {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </span>
      </div>
      
      {/* 按事件顺序渲染 */}
      <div className="space-y-3 pl-7">
        {events.map((event, index) => {
          switch (event.type) {
            case 'thinking': {
              const content = extractContent(event.data);
              if (!content || content.length < 5) return null;
              return <ThinkingBlock key={`thinking-${index}`} content={content} />;
            }
            
            case 'tool_start': {
              const data = event.data as Record<string, unknown>;
              const toolName = String(data?.tool || 'unknown');
              const toolInput = (data?.input || {}) as Record<string, unknown>;
              const toolId = String(data?.id || `tool-${index}`);
              
              // 查找对应的 tool_end
              const toolEnd = findToolEnd(events, index, toolName);
              const toolEndIndex = toolEnd ? events.indexOf(toolEnd) : -1;
              if (toolEndIndex >= 0) {
                processedToolEnds.add(toolEndIndex);
              }
              
              const endData = toolEnd?.data as Record<string, unknown> | undefined;
              const resultData = endData?.result as Record<string, unknown> | undefined;
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
                <div key={`text-${index}`} className="text-[14px] text-white/90 leading-relaxed whitespace-pre-wrap">
                  <FormattedText text={content} />
                </div>
              );
            }
            
            case 'warning': {
              const content = extractContent(event.data);
              return (
                <div key={`warning-${index}`} className="flex items-start gap-2 px-3 py-2 rounded-md bg-yellow-500/10 border border-yellow-500/20 text-yellow-400 text-sm">
                  <span>⚠️</span>
                  <span>{content}</span>
                </div>
              );
            }
            
            case 'error': {
              const content = extractContent(event.data);
              return (
                <div key={`error-${index}`} className="flex items-start gap-2 px-3 py-2 rounded-md bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
                  <span>❌</span>
                  <span>{content}</span>
                </div>
              );
            }
            
            default:
              return null;
          }
        })}
        
        {/* 最终响应（如果有且不在 events 中） */}
        {message.content && !events.some(e => e.type === 'final') && (
          <div className="text-[14px] text-white/90 leading-relaxed whitespace-pre-wrap">
            <FormattedText text={message.content} />
          </div>
        )}
        
        {/* Streaming 指示器 */}
        {isStreaming && events.length === 0 && (
          <div className="flex items-center gap-2 text-white/40 text-sm">
            <span className="inline-flex">
              <span className="animate-pulse">●</span>
              <span className="animate-pulse" style={{ animationDelay: '150ms' }}>●</span>
              <span className="animate-pulse" style={{ animationDelay: '300ms' }}>●</span>
            </span>
          </div>
        )}
      </div>
    </div>
  );
}

/**
 * 简单的文本格式化（处理代码块）
 */
function FormattedText({ text }: { text: string }) {
  const codeBlockRegex = /```(\w+)?\n?([\s\S]*?)```/g;
  const inlineCodeRegex = /`([^`]+)`/g;
  
  const parts: Array<{ type: 'text' | 'code-block' | 'inline-code'; content: string; language?: string }> = [];
  let lastIndex = 0;
  let match;
  
  while ((match = codeBlockRegex.exec(text)) !== null) {
    if (match.index > lastIndex) {
      parts.push({ type: 'text', content: text.slice(lastIndex, match.index) });
    }
    parts.push({ 
      type: 'code-block', 
      content: match[2].trim(), 
      language: match[1] || 'plaintext' 
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
          return (
            <pre key={i} className="my-2 px-3 py-2 rounded-md bg-black/40 border border-white/[0.06] overflow-x-auto">
              <code className="text-[13px] text-emerald-400/90 font-mono">
                {part.content}
              </code>
            </pre>
          );
        }
        
        const textParts = part.content.split(inlineCodeRegex);
        return (
          <span key={i}>
            {textParts.map((t, j) => 
              j % 2 === 1 ? (
                <code key={j} className="px-1.5 py-0.5 rounded bg-white/[0.06] text-[13px] font-mono text-violet-300">
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
