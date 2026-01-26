import { useState } from 'react';
import { ToolCallEvent } from '../../types';
import { 
  ChevronRight, 
  Terminal, 
  FileCode, 
  FolderOpen, 
  FileText, 
  Globe,
  MousePointer,
  Keyboard,
  Camera,
  Check,
  X,
  Loader2,
  Copy,
  CheckCheck
} from 'lucide-react';

interface ToolCallCardProps {
  toolCall: ToolCallEvent;
}

// Tool icon mapping
const toolIcons: Record<string, typeof Terminal> = {
  run_command: Terminal,
  run_python: FileCode,
  list_files: FolderOpen,
  read_file: FileText,
  write_file: FileText,
  browser_navigate: Globe,
  browser_click: MousePointer,
  browser_type: Keyboard,
  browser_screenshot: Camera,
  browser_eval: FileCode,
  screenshot: Camera,
  mouse: MousePointer,
  keyboard: Keyboard,
};

// Tool display names
const toolDisplayNames: Record<string, string> = {
  run_command: 'Shell',
  run_python: 'Python',
  list_files: 'List Files',
  read_file: 'Read File',
  write_file: 'Write File',
  browser_navigate: 'Navigate',
  browser_click: 'Click',
  browser_type: 'Type',
  browser_screenshot: 'Screenshot',
  browser_eval: 'Eval JS',
  screenshot: 'Screenshot',
  mouse: 'Mouse',
  keyboard: 'Keyboard',
};

export function ToolCallCard({ toolCall }: ToolCallCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [copied, setCopied] = useState(false);

  const Icon = toolIcons[toolCall.tool] || Terminal;
  const displayName = toolDisplayNames[toolCall.tool] || toolCall.tool;

  // Status styling
  const statusConfig = {
    pending: { icon: null, color: 'text-white/40', bg: 'bg-white/[0.02]', border: 'border-white/[0.06]' },
    running: { icon: <Loader2 size={12} className="animate-spin" />, color: 'text-violet-400', bg: 'bg-violet-500/5', border: 'border-violet-500/20' },
    success: { icon: <Check size={12} />, color: 'text-emerald-400', bg: 'bg-emerald-500/5', border: 'border-emerald-500/20' },
    error: { icon: <X size={12} />, color: 'text-red-400', bg: 'bg-red-500/5', border: 'border-red-500/20' },
  };

  const status = statusConfig[toolCall.status] || statusConfig.pending;

  // Format input for display
  const getInputDisplay = () => {
    if (toolCall.tool === 'run_command') {
      return toolCall.input.command as string;
    }
    if (toolCall.tool === 'run_python') {
      return toolCall.input.code as string;
    }
    if (toolCall.tool === 'browser_navigate') {
      return toolCall.input.url as string;
    }
    if (toolCall.tool === 'browser_click' || toolCall.tool === 'browser_type') {
      return toolCall.input.selector as string;
    }
    return JSON.stringify(toolCall.input, null, 2);
  };

  // Format output for display
  const getOutputDisplay = () => {
    const result = toolCall.result;
    if (!result) return null;

    // Helper: format collapsed HTML data (used by multiple tools)
    const formatHtmlData = (data: Record<string, unknown>) => {
      const parts: string[] = [];
      if (data.state_id) parts.push(`State: ${data.state_id}`);
      if (data.url) parts.push(`URL: ${data.url}`);
      if (data.title) parts.push(`Title: ${data.title}`);
      if (data.path) parts.push(`Path: ${data.path}`);
      if (data.html) {
        const html = String(data.html);
        const truncated = html.length > 800 ? html.slice(0, 800) + '...' : html;
        parts.push(`\nHTML:\n${truncated}`);
      }
      if (data.expandable && Array.isArray(data.expandable) && data.expandable.length > 0) {
        parts.push(`\nExpandable (${data.expandable.length}):`);
        const paths = data.expandable.slice(0, 10).join('\n  ');
        parts.push(`  ${paths}`);
        if (data.expandable.length > 10) {
          parts.push(`  ... +${data.expandable.length - 10} more`);
        }
      }
      return parts.length > 0 ? parts.join('\n') : null;
    };

    // Direct result format (browser_expand, browser_get_html)
    if (result.html !== undefined || result.expandable !== undefined || result.state_id !== undefined) {
      return formatHtmlData(result);
    }

    // Check for observation (Executor API format)
    const observation = result.observation || result.output;
    
    if (observation) {
      // Shell command output
      if (observation.stdout) return observation.stdout;
      if (observation.content) return observation.content;
      if (observation.error) return observation.error;
      
      // Collapsed HTML format (browser_navigate, browser_click, etc.)
      if (observation.html !== undefined || observation.expandable !== undefined || observation.state_id !== undefined) {
        return formatHtmlData(observation);
      }
      
      // Legacy format: page_summary
      if (observation.page_summary) {
        return observation.page_summary;
      }
      
      // Legacy format: url, title only
      if (observation.url !== undefined || observation.title !== undefined) {
        const parts: string[] = [];
        if (observation.url) parts.push(`URL: ${observation.url}`);
        if (observation.title) parts.push(`Title: ${observation.title}`);
        if (parts.length > 0) return parts.join('\n');
      }
    }
    
    if (result.error) return result.error;
    
    // For successful operations with no output
    if (result.success && !observation) return '✓ Success';
    
    return null;
  };

  const inputDisplay = getInputDisplay();
  const outputDisplay = getOutputDisplay();
  const exitCode = toolCall.result?.output?.exit_code ?? toolCall.result?.observation?.exit_code;
  const duration = toolCall.result?.duration_ms;

  const copyToClipboard = async (text: string) => {
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className={`rounded-lg ${status.bg} border ${status.border} overflow-hidden transition-colors`}>
      {/* Header */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center gap-2 px-3 py-2 hover:bg-white/[0.02] transition-colors text-left"
      >
        <ChevronRight 
          size={14} 
          className={`text-white/30 transition-transform ${isExpanded ? 'rotate-90' : ''}`}
        />
        <Icon size={14} className={status.color} />
        <span className={`text-xs font-medium ${status.color}`}>{displayName}</span>
        
        {/* Inline preview when collapsed */}
        {!isExpanded && inputDisplay && (
          <code className="flex-1 text-xs text-white/40 font-mono truncate ml-1">
            {inputDisplay.slice(0, 50)}{inputDisplay.length > 50 ? '...' : ''}
          </code>
        )}
        
        {/* Status indicator */}
        <div className="flex items-center gap-2 ml-auto">
          {duration && (
            <span className="text-[10px] text-white/30">{duration}ms</span>
          )}
          {status.icon && <span className={status.color}>{status.icon}</span>}
        </div>
      </button>

      {/* Expanded content */}
      {isExpanded && (
        <div className="border-t border-white/[0.04]">
          {/* Input */}
          <div className="px-3 py-2">
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-[10px] uppercase tracking-wider text-white/30">Input</span>
              <button
                onClick={(e) => { e.stopPropagation(); copyToClipboard(inputDisplay); }}
                className="p-1 hover:bg-white/[0.06] rounded transition-colors"
              >
                {copied 
                  ? <CheckCheck size={12} className="text-emerald-400" /> 
                  : <Copy size={12} className="text-white/30" />
                }
              </button>
            </div>
            <pre className="text-[12px] text-white/70 font-mono whitespace-pre-wrap break-all bg-black/20 rounded px-2 py-1.5 max-h-32 overflow-auto">
              {inputDisplay}
            </pre>
          </div>

          {/* Output */}
          {toolCall.result && (
            <div className="px-3 py-2 border-t border-white/[0.04]">
              <div className="flex items-center gap-2 mb-1.5">
                <span className="text-[10px] uppercase tracking-wider text-white/30">Output</span>
                {exitCode !== undefined && (
                  <span className={`text-[10px] ${exitCode === 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                    exit: {exitCode}
                  </span>
                )}
              </div>
              {outputDisplay && (
                <pre className="text-[12px] text-white/70 font-mono whitespace-pre-wrap break-all bg-black/20 rounded px-2 py-1.5 max-h-48 overflow-auto">
                  {outputDisplay}
                </pre>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

