import { useEffect, useRef } from 'react';
import { LogEntry } from '../../types';
import { Trash2, Rocket, CheckCircle, AlertCircle, Terminal, Loader2 } from 'lucide-react';
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

  const getLogIcon = (type: string) => {
    switch (type) {
      case 'tool_start':
        return <Rocket size={14} className="text-nb-accent" />;
      case 'tool_end':
        return <CheckCircle size={14} className="text-nb-success" />;
      case 'error':
        return <AlertCircle size={14} className="text-nb-error" />;
      case 'stdout':
      case 'stderr':
        return <Terminal size={14} className="text-nb-text-muted" />;
      default:
        return <Terminal size={14} className="text-nb-text-muted" />;
    }
  };

  const formatLog = (log: LogEntry): string => {
    switch (log.type) {
      case 'tool_start':
        return `Starting: ${log.data.tool || 'unknown'}`;
      case 'tool_end':
        return `Completed: ${log.data.tool || 'unknown'}`;
      case 'status':
        return log.data.message || '';
      case 'stdout':
      case 'stderr':
        return log.data.output || '';
      case 'progress':
        return `Progress: ${log.data.progress}%`;
      case 'text':
        return log.data.content || String(log.data);
      case 'final':
        // Display the final response content from agent
        return String(log.data || '');
      case 'error':
        return `Error: ${log.data.error || 'Unknown error'}`;
      default:
        return JSON.stringify(log.data);
    }
  };

  const getLogClass = (type: string): string => {
    switch (type) {
      case 'tool_start':
        return 'text-nb-accent';
      case 'tool_end':
        return 'text-nb-success';
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
            {logs.map((log, index) => (
              <div
                key={index}
                className={`flex items-start gap-2 py-1 ${getLogClass(log.type)}`}
              >
                <span className="flex-shrink-0 mt-0.5">{getLogIcon(log.type)}</span>
                <span className="text-nb-text-muted w-16 flex-shrink-0">
                  {new Date(log.timestamp).toLocaleTimeString()}
                </span>
                <span className="break-all whitespace-pre-wrap">
                  {formatLog(log)}
                </span>
              </div>
            ))}
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

