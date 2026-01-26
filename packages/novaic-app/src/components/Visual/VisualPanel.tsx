import { useState } from 'react';
import { VNCView } from './VNCView';
import { ExecutionLog } from './ExecutionLog';
import { useAppStore } from '../../store';
import { Monitor, Terminal, Maximize2, Minimize2 } from 'lucide-react';

export function VisualPanel() {
  const { logs, isExecuting } = useAppStore();
  const [isLogExpanded, setIsLogExpanded] = useState(false);
  const [activeTab, setActiveTab] = useState<'vnc' | 'logs'>('vnc');

  return (
    <div className="flex flex-col h-full">
      {/* Tabs */}
      <div className="h-12 px-4 flex items-center border-b border-nb-border gap-4">
        <button
          onClick={() => setActiveTab('vnc')}
          className={`flex items-center gap-2 px-3 py-1.5 rounded-lg transition-colors ${
            activeTab === 'vnc'
              ? 'bg-nb-surface-2 text-nb-text'
              : 'text-nb-text-muted hover:text-nb-text'
          }`}
        >
          <Monitor size={16} />
          <span className="text-sm font-medium">Desktop</span>
        </button>
        <button
          onClick={() => setActiveTab('logs')}
          className={`flex items-center gap-2 px-3 py-1.5 rounded-lg transition-colors ${
            activeTab === 'logs'
              ? 'bg-nb-surface-2 text-nb-text'
              : 'text-nb-text-muted hover:text-nb-text'
          }`}
        >
          <Terminal size={16} />
          <span className="text-sm font-medium">Logs</span>
          {isExecuting && (
            <span className="w-2 h-2 rounded-full bg-nb-success animate-pulse" />
          )}
        </button>
        
        <div className="flex-1" />
        
        {/* Toggle log expansion */}
        <button
          onClick={() => setIsLogExpanded(!isLogExpanded)}
          className="p-2 hover:bg-nb-surface-2 rounded-lg transition-colors"
          title={isLogExpanded ? 'Collapse logs' : 'Expand logs'}
        >
          {isLogExpanded ? (
            <Minimize2 size={16} className="text-nb-text-muted" />
          ) : (
            <Maximize2 size={16} className="text-nb-text-muted" />
          )}
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* VNC Section */}
        <div
          className={`transition-all duration-300 ${
            activeTab === 'vnc'
              ? isLogExpanded
                ? 'h-1/2'
                : 'flex-1'
              : 'h-0 overflow-hidden'
          }`}
        >
          <VNCView />
        </div>

        {/* Logs Section */}
        <div
          className={`border-t border-nb-border transition-all duration-300 ${
            activeTab === 'logs' || isLogExpanded
              ? isLogExpanded
                ? 'h-1/2'
                : 'flex-1'
              : 'h-0 overflow-hidden'
          }`}
        >
          <ExecutionLog logs={logs} isExecuting={isExecuting} />
        </div>
      </div>
    </div>
  );
}

