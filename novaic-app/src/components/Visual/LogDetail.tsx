import { useState, useCallback } from 'react';
import { LogEntry } from '../../types';
import { ChevronDown, ChevronRight, Copy, Check } from 'lucide-react';
import { 
  formatJsonForDisplay, 
  getInputData, 
  getResultData, 
  getThinkingContent, 
  getErrorInfo 
} from '../../utils/logFormatters';
import { UI_CONFIG } from '../../config';

interface LogDetailProps {
  log: LogEntry;
  isExpanded: boolean;
  onToggle: () => void;
}

export function LogDetail({ log, isExpanded, onToggle }: LogDetailProps) {
  const [copied, setCopied] = useState<string | null>(null);

  const copyToClipboard = useCallback((text: string, label: string) => {
    navigator.clipboard.writeText(text).then(() => {
      setCopied(label);
      setTimeout(() => setCopied(null), UI_CONFIG.COPY_FEEDBACK_DELAY);
    });
  }, []);

  const input = getInputData(log);
  const result = getResultData(log);
  const thinkingContent = getThinkingContent(log);
  const error = getErrorInfo(log);

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
