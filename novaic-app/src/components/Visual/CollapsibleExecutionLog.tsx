import { useState, useMemo, useRef, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { Terminal, ChevronUp, Loader2, CheckCircle, XCircle, Brain, X, GripHorizontal } from 'lucide-react';
import { useAppStore } from '../../store';
import { ExecutionLog } from './ExecutionLog';
import { LogEntry } from '../../types';

interface CollapsibleExecutionLogProps {
  className?: string;
}

// 拖拽 Hook
function useDraggable(initialPosition: { x: number; y: number }) {
  const [position, setPosition] = useState(initialPosition);
  const [isDragging, setIsDragging] = useState(false);
  const dragRef = useRef<HTMLDivElement>(null);
  const offsetRef = useRef({ x: 0, y: 0 });

  useEffect(() => {
    if (!isDragging) return;

    const handleMouseMove = (e: MouseEvent) => {
      setPosition({
        x: e.clientX - offsetRef.current.x,
        y: e.clientY - offsetRef.current.y,
      });
    };

    const handleMouseUp = () => {
      setIsDragging(false);
    };

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isDragging]);

  const handleMouseDown = (e: React.MouseEvent) => {
    if (dragRef.current) {
      const rect = dragRef.current.getBoundingClientRect();
      offsetRef.current = {
        x: e.clientX - rect.left,
        y: e.clientY - rect.top,
      };
      setIsDragging(true);
    }
  };

  return { position, isDragging, dragRef, handleMouseDown, setPosition };
}

// 获取日志的简短描述
function getLogSummary(log: LogEntry): string {
  const isThink = log.kind === 'think' || log.type === 'thinking';
  const toolName = log.data?.tool || log.event_key || '';
  
  if (isThink) {
    // 思考类型，尝试获取内容摘要
    const content = log.result?.content || log.data?.content || '';
    if (typeof content === 'string' && content.length > 0) {
      return content.length > 50 ? content.slice(0, 50) + '...' : content;
    }
    return '思考中...';
  }
  
  // 工具类型
  return toolName || '执行中...';
}

// 获取日志状态
function getLogStatus(log: LogEntry): 'running' | 'success' | 'failed' {
  if (log.status === 'running') return 'running';
  if (log.status === 'failed' || log.data?.success === false || log.result?.error || log.data?.error) {
    return 'failed';
  }
  return 'success';
}

// 单条日志预览项
function LogPreviewItem({ log }: { log: LogEntry }) {
  const isThink = log.kind === 'think' || log.type === 'thinking';
  const status = getLogStatus(log);
  const summary = getLogSummary(log);
  
  return (
    <div className="flex items-center gap-2 min-w-0">
      {/* 状态图标 */}
      <div className={`
        w-4 h-4 rounded flex items-center justify-center shrink-0
        ${isThink 
          ? 'bg-violet-500/20' 
          : status === 'running' 
            ? 'bg-nb-accent/20'
            : status === 'failed' 
              ? 'bg-nb-error/20' 
              : 'bg-nb-success/20'
        }
      `}>
        {isThink ? (
          status === 'running' 
            ? <Loader2 size={10} className="text-violet-400 animate-spin" /> 
            : <Brain size={10} className="text-violet-400" />
        ) : status === 'running' ? (
          <Loader2 size={10} className="text-nb-text-muted animate-spin" />
        ) : status === 'failed' ? (
          <XCircle size={10} className="text-nb-error" />
        ) : (
          <CheckCircle size={10} className="text-nb-success" />
        )}
      </div>
      
      {/* 摘要文本 */}
      <span className={`
        text-[11px] truncate
        ${isThink ? 'text-violet-300' : 'text-nb-text-muted'}
      `}>
        {summary}
      </span>
    </div>
  );
}

// 全屏日志模态框
function FullLogModal({ isOpen, onClose }: { isOpen: boolean; onClose: () => void }) {
  const { logs } = useAppStore();
  
  if (!isOpen) return null;
  
  const modalContent = (
    <div className="fixed inset-0 z-[9999] flex items-center justify-center">
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-black/70 backdrop-blur-sm"
        onClick={onClose}
      />
      
      {/* Modal */}
      <div className="relative w-[90vw] max-w-4xl h-[85vh] bg-nb-surface rounded-xl border border-nb-border shadow-2xl flex flex-col overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-nb-border shrink-0">
          <div className="flex items-center gap-2">
            <Terminal size={16} className="text-nb-text-secondary" />
            <span className="text-sm font-medium text-nb-text">Execution Log</span>
            <span className="px-2 py-0.5 bg-nb-surface-2 text-nb-text-secondary text-[10px] rounded">
              {logs.length} 条记录
            </span>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 rounded-lg flex items-center justify-center text-nb-text-secondary hover:text-nb-text hover:bg-nb-hover transition-colors"
          >
            <X size={16} />
          </button>
        </div>
        
        {/* Content */}
        <div className="flex-1 min-h-0 overflow-hidden">
          <ExecutionLog logs={logs} />
        </div>
      </div>
    </div>
  );
  
  return createPortal(modalContent, document.body);
}

export function CollapsibleExecutionLog({ className = '' }: CollapsibleExecutionLogProps) {
  const { logs, currentAgentId } = useAppStore();
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isHovered, setIsHovered] = useState(false);
  const { position, isDragging, dragRef, handleMouseDown } = useDraggable({ x: 16, y: 16 });
  
  // 获取最近的日志（折叠时显示2条，悬停时显示4条）
  const recentLogs = useMemo(() => {
    const count = isHovered ? 4 : 2;
    return logs.slice(-count);
  }, [logs, isHovered]);
  
  // 统计运行中的任务数
  const runningCount = useMemo(() => {
    return logs.filter(log => log.status === 'running').length;
  }, [logs]);
  
  // 如果没有 Agent 或没有日志，不显示浮动组件
  if (!currentAgentId || logs.length === 0) {
    return null;
  }
  
  return (
    <>
      <div 
        ref={dragRef}
        className={`
          absolute top-4 left-1/2 -translate-x-1/2 z-50 
          w-[70%]
          bg-nb-surface/85 backdrop-blur-md 
          rounded-lg shadow-lg border border-nb-border
          transition-all duration-200 ease-out
          ${isDragging ? 'cursor-grabbing shadow-xl scale-[1.02]' : ''}
          ${isHovered ? 'bg-nb-surface/95 shadow-xl' : ''}
          ${className}
        `}
        style={
          isDragging
            ? { top: position.y, left: position.x, transform: 'none' }
            : undefined
        }
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
      >
        {/* 拖拽手柄 */}
        <div 
          className={`
            absolute -top-0 left-1/2 -translate-x-1/2 
            px-3 py-0.5 cursor-grab
            text-nb-text-muted/50 hover:text-nb-text-muted
            transition-opacity duration-200
            ${isHovered ? 'opacity-100' : 'opacity-0'}
          `}
          onMouseDown={handleMouseDown}
        >
          <GripHorizontal size={12} />
        </div>
        
        {/* 头部 */}
        <div 
          className="px-3 py-2 cursor-pointer"
          onClick={() => setIsModalOpen(true)}
        >
          {/* 第一行：标题和展开按钮 */}
          <div className="flex items-center gap-2 mb-1.5">
            <Terminal size={12} className="text-nb-text-secondary shrink-0" />
            <span className="text-[11px] font-medium text-nb-text-muted">Execution Log</span>
            
            {/* 运行中计数 */}
            {runningCount > 0 && (
              <span className="flex items-center gap-1 px-1.5 py-0.5 bg-nb-accent/20 text-nb-accent rounded text-[10px]">
                <Loader2 size={8} className="animate-spin" />
                {runningCount}
              </span>
            )}
            
            {/* 总数 */}
            <span className="px-1.5 py-0.5 bg-nb-surface-2/80 text-nb-text-secondary rounded text-[10px]">
              {logs.length}
            </span>
            
            <div className="flex-1" />
            
            {/* 展开按钮 */}
            <button
              className={`
                flex items-center gap-1 px-2 py-0.5 rounded 
                text-[10px] text-nb-text-secondary 
                hover:text-nb-text hover:bg-nb-hover/50 
                transition-all duration-200
                ${isHovered ? 'opacity-100' : 'opacity-60'}
              `}
              onClick={(e) => {
                e.stopPropagation();
                setIsModalOpen(true);
              }}
            >
              <ChevronUp size={10} />
              展开
            </button>
          </div>
          
          {/* 日志预览列表 */}
          <div className="space-y-1">
            {recentLogs.map((log, idx) => (
              <LogPreviewItem key={log.id || idx} log={log} />
            ))}
          </div>
        </div>
      </div>
      
      {/* 全屏日志模态框 */}
      <FullLogModal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} />
    </>
  );
}
