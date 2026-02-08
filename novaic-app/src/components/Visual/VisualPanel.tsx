import { useState, useCallback, useRef, useEffect } from 'react';
import { VNCView } from './VNCView';
import { ExecutionLog } from './ExecutionLog';
import { useAppStore } from '../../store';
import { GripHorizontal, Maximize2 } from 'lucide-react';

// Layout persistence key
const VM_HEIGHT_STORAGE_KEY = 'novaic-vm-height-ratio';
const DEFAULT_VM_HEIGHT_RATIO = 0.65; // 65% for VM, 35% for logs
const MIN_VM_HEIGHT_RATIO = 0.3;
const MAX_VM_HEIGHT_RATIO = 0.85;

function loadVmHeightRatio(): number {
  try {
    const saved = localStorage.getItem(VM_HEIGHT_STORAGE_KEY);
    if (saved) {
      const ratio = parseFloat(saved);
      if (!isNaN(ratio) && ratio >= MIN_VM_HEIGHT_RATIO && ratio <= MAX_VM_HEIGHT_RATIO) {
        return ratio;
      }
    }
  } catch (e) {
    console.warn('[VisualPanel] Failed to load VM height ratio:', e);
  }
  return DEFAULT_VM_HEIGHT_RATIO;
}

function saveVmHeightRatio(ratio: number): void {
  try {
    localStorage.setItem(VM_HEIGHT_STORAGE_KEY, ratio.toString());
  } catch (e) {
    console.warn('[VisualPanel] Failed to save VM height ratio:', e);
  }
}

interface VisualPanelProps {
  isThumbnail?: boolean;
}

export function VisualPanel({ isThumbnail = false }: VisualPanelProps) {
  const { setLayoutMode, logs } = useAppStore();
  const [vmHeightRatio, setVmHeightRatio] = useState(loadVmHeightRatio);
  const [isResizing, setIsResizing] = useState(false);
  const [isLogsCollapsed, setIsLogsCollapsed] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  // Handle vertical resize
  const handleResizeStart = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    setIsResizing(true);
  }, []);

  useEffect(() => {
    if (!isResizing) return;

    const handleMouseMove = (e: MouseEvent) => {
      if (!containerRef.current) return;
      
      const rect = containerRef.current.getBoundingClientRect();
      const newRatio = (e.clientY - rect.top) / rect.height;
      const clampedRatio = Math.max(MIN_VM_HEIGHT_RATIO, Math.min(MAX_VM_HEIGHT_RATIO, newRatio));
      
      setVmHeightRatio(clampedRatio);
    };

    const handleMouseUp = () => {
      setIsResizing(false);
      saveVmHeightRatio(vmHeightRatio);
    };

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isResizing, vmHeightRatio]);

  // Double-click to reset
  const handleResetHeight = useCallback(() => {
    setVmHeightRatio(DEFAULT_VM_HEIGHT_RATIO);
    saveVmHeightRatio(DEFAULT_VM_HEIGHT_RATIO);
  }, []);

  // Toggle logs collapse
  const toggleLogsCollapse = useCallback(() => {
    setIsLogsCollapsed(prev => !prev);
  }, []);

  // Thumbnail mode: just show VNC, click to expand
  if (isThumbnail) {
    return (
      <div 
        className="h-full w-full cursor-pointer"
        onClick={() => setLayoutMode('normal')}
      >
        <VNCView isThumbnail />
      </div>
    );
  }

  // Full mode or normal mode: VM on top, logs on bottom
  return (
    <div ref={containerRef} className="flex flex-col h-full">
      {/* VM View */}
      <div 
        className="flex-shrink-0 overflow-hidden"
        style={{ height: isLogsCollapsed ? 'calc(100% - 32px)' : `${vmHeightRatio * 100}%` }}
      >
        <VNCView />
      </div>

      {/* Horizontal Resizer */}
      <div
        className={`
          h-2 flex items-center justify-center cursor-row-resize 
          bg-nb-surface border-y border-nb-border
          hover:bg-nb-surface-2 transition-colors
          ${isResizing ? 'bg-nb-accent/20' : ''}
          ${isLogsCollapsed ? 'hidden' : ''}
        `}
        onMouseDown={handleResizeStart}
        onDoubleClick={handleResetHeight}
      >
        <GripHorizontal size={14} className="text-nb-text-muted" />
      </div>

      {/* Logs Panel */}
      <div 
        className={`
          flex-1 min-h-0 overflow-hidden flex flex-col
          ${isLogsCollapsed ? 'flex-shrink-0' : ''}
        `}
        style={{ height: isLogsCollapsed ? '32px' : undefined }}
      >
        {isLogsCollapsed ? (
          // Collapsed header
          <div 
            className="h-8 px-3 flex items-center gap-2 bg-nb-surface border-t border-nb-border cursor-pointer hover:bg-nb-surface-2"
            onClick={toggleLogsCollapse}
          >
            <span className="text-xs font-medium text-nb-text">Execution Log</span>
            {logs.length > 0 && (
              <span className="px-1.5 py-0.5 bg-nb-accent/20 text-nb-accent rounded text-[10px]">
                {logs.length}
              </span>
            )}
            <div className="flex-1" />
            <Maximize2 size={12} className="text-nb-text-muted" />
          </div>
        ) : (
          // Expanded logs
          <div className="flex-1 flex flex-col min-h-0">
            <ExecutionLog logs={logs} />
          </div>
        )}
      </div>
    </div>
  );
}

