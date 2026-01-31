import { useEffect, useRef } from 'react';
import { LogEntry } from '../../types';
import { Trash2, Rocket, CheckCircle, AlertCircle, Terminal, Loader2, Brain, Zap, XCircle } from 'lucide-react';
import { useAppStore } from '../../store';

interface ExecutionLogProps {
  logs: LogEntry[];
  isExecuting: boolean;
}

export function ExecutionLog({ logs, isExecuting }: ExecutionLogProps) {
  const logEndRef = useRef<HTMLDivElement>(null);
  const { clearLogs } = useAppStore();

  // Auto-scroll to bottom
  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);

  const getLogIcon = (type: string, success?: boolean) => {
    switch (type) {
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

  const formatLog = (log: LogEntry): { main: string; detail?: string } => {
    switch (log.type) {
      case 'tool_start': {
        const toolName = log.data.tool || 'unknown';
        const args = log.data.args || log.data.input;
        let detail = '';
        
        // Format input parameters
        if (args && typeof args === 'object') {
          const argsObj = args as Record<string, unknown>;
          const keys = Object.keys(argsObj);
          if (keys.length > 0) {
            const params = keys.slice(0, 3).map(k => {
              const v = argsObj[k];
              const val = typeof v === 'string' 
                ? (v.length > 50 ? v.substring(0, 50) + '...' : v)
                : JSON.stringify(v).substring(0, 50);
              return `${k}: ${val}`;
            }).join(' | ');
            detail = params + (keys.length > 3 ? ` (+${keys.length - 3})` : '');
          }
        }
        
        return { main: `⚡ ${toolName}`, detail };
      }
      case 'tool_end': {
        const toolName = log.data.tool || 'unknown';
        const success = log.data.success;
        const result = log.data.result;
        let detail = '';
        
        // Format result summary
        if (result && typeof result === 'object') {
          if (result.error) {
            detail = `❌ ${String(result.error).substring(0, 80)}`;
          } else if (result.message) {
            detail = `💬 ${String(result.message).substring(0, 80)}`;
          } else if (result.url) {
            detail = `🔗 ${result.url}`;
          } else if (result.output) {
            detail = String(result.output).substring(0, 80);
          } else if (result.content) {
            detail = String(result.content).substring(0, 80);
          } else {
            const keys = Object.keys(result).filter(k => k !== 'success' && k !== 'done');
            if (keys.length > 0) {
              detail = keys.slice(0, 3).map(k => `${k}: ${JSON.stringify(result[k]).substring(0, 30)}`).join(' | ');
            }
          }
        }
        
        const icon = success !== false ? '✓' : '✗';
        return { 
          main: `${icon} ${toolName}`, 
          detail: detail || (success !== false ? 'completed' : 'failed')
        };
      }
      case 'thinking': {
        const content = typeof log.data === 'string' ? log.data : (log.data?.content || '');
        if (!content) return { main: '...' };
        // Show reasoning content (truncated)
        const truncated = content.length > 150 ? content.substring(0, 150) + '...' : content;
        return { main: truncated };
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
          className="p-1.5 hover:bg-nb-surface-2 rounded transition-colors"
          title="Clear logs"
        >
          <Trash2 size={14} className="text-nb-text-muted" />
        </button>
      </div>

      {/* Log content */}
      <div className="flex-1 overflow-y-auto p-4 font-mono text-xs">
        {logs.length === 0 ? (
          <div className="text-nb-text-muted text-center py-8">
            <Terminal size={32} className="mx-auto mb-2 opacity-50" />
            <p>No execution logs yet</p>
            <p className="text-xs mt-1 opacity-50">
              Logs will appear here when you send a message
            </p>
          </div>
        ) : (
          <div className="space-y-1">
            {logs.map((log, index) => {
              const formatted = formatLog(log);
              const success = log.type === 'tool_end' ? log.data?.success : undefined;
              return (
                <div
                  key={index}
                  className={`flex items-start gap-2 py-1.5 ${getLogClass(log.type)}`}
                >
                  <span className="flex-shrink-0 mt-0.5">{getLogIcon(log.type, success)}</span>
                  <span className="text-nb-text-muted w-16 flex-shrink-0 text-[10px]">
                    {new Date(log.timestamp).toLocaleTimeString()}
                  </span>
                  <div className="flex-1 min-w-0">
                    <div className="break-all whitespace-pre-wrap leading-relaxed">
                      {formatted.main}
                    </div>
                    {formatted.detail && (
                      <div className="text-[11px] text-nb-text-muted mt-1 break-all opacity-80">
                        {formatted.detail}
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
            <div ref={logEndRef} />
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

