import { useState } from 'react';
import { ToolCallEvent } from '../../types';
import { ImagePreview } from './ImagePreview';
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

  // Extract screenshot from result (checks multiple locations)
  const getScreenshot = (): string | null => {
    const result = toolCall.result;
    if (!result) return null;

    // Check top level
    if (result.screenshot && typeof result.screenshot === 'string' && result.screenshot.length > 100) {
      return result.screenshot;
    }
    // Check observation
    if (result.observation?.screenshot && typeof result.observation.screenshot === 'string') {
      return result.observation.screenshot;
    }
    // Check output
    if (result.output?.screenshot && typeof result.output.screenshot === 'string') {
      return result.output.screenshot;
    }
    return null;
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
  const screenshot = getScreenshot();
  const exitCode = toolCall.result?.output?.exit_code ?? toolCall.result?.observation?.exit_code;
  const duration = toolCall.result?.duration_ms;

  const copyToClipboard = async (text: string) => {
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // Get short preview for collapsed state
  const getShortPreview = () => {
    if (toolCall.tool === 'run_command') {
      const cmd = toolCall.input.command as string;
      return cmd.length > 40 ? cmd.slice(0, 40) + '...' : cmd;
    }
    if (toolCall.tool === 'run_python') {
      const code = toolCall.input.code as string;
      const firstLine = code.split('\n')[0];
      return firstLine.length > 40 ? firstLine.slice(0, 40) + '...' : firstLine;
    }
    if (toolCall.tool === 'browser_navigate') {
      return toolCall.input.url as string;
    }
    return null;
  };

  const shortPreview = getShortPreview();

  return (
    <div className={`rounded ${status.bg} border ${status.border} overflow-hidden transition-colors`}>
      {/* Header - compact single line */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center gap-1.5 px-2 py-1.5 hover:bg-white/[0.02] transition-colors text-left"
      >
        <ChevronRight 
          size={12} 
          className={`text-white/30 transition-transform shrink-0 ${isExpanded ? 'rotate-90' : ''}`}
        />
        <Icon size={12} className={status.color} />
        <span className={`text-[11px] font-medium ${status.color}`}>{displayName}</span>
        
        {/* Inline preview when collapsed */}
        {!isExpanded && shortPreview && (
          <code className="flex-1 text-[11px] text-white/30 font-mono truncate">
            {shortPreview}
          </code>
        )}
        
        {/* Status indicator */}
        <div className="flex items-center gap-1.5 ml-auto shrink-0">
          {duration && (
            <span className="text-[10px] text-white/20">{duration}ms</span>
          )}
          {status.icon && <span className={status.color}>{status.icon}</span>}
        </div>
      </button>

      {/* Expanded content */}
      {isExpanded && (
        <div className="border-t border-white/[0.04]">
          {/* Input */}
          <div className="px-2 py-1.5">
            <div className="flex items-center justify-between mb-1">
              <span className="text-[9px] uppercase tracking-wider text-white/25 font-medium">Input</span>
              <button
                onClick={(e) => { e.stopPropagation(); copyToClipboard(inputDisplay); }}
                className="p-0.5 hover:bg-white/[0.06] rounded transition-colors"
              >
                {copied 
                  ? <CheckCheck size={10} className="text-emerald-400" /> 
                  : <Copy size={10} className="text-white/25" />
                }
              </button>
            </div>
            <pre className="text-[11px] text-white/60 font-mono whitespace-pre-wrap break-all bg-black/20 rounded px-2 py-1.5 max-h-28 overflow-auto">
              {inputDisplay}
            </pre>
          </div>

          {/* Output */}
          {toolCall.result && (
            <div className="px-2 py-1.5 border-t border-white/[0.04]">
              <div className="flex items-center gap-1.5 mb-1">
                <span className="text-[9px] uppercase tracking-wider text-white/25 font-medium">Output</span>
                {exitCode !== undefined && (
                  <span className={`text-[9px] ${exitCode === 0 ? 'text-emerald-400/70' : 'text-red-400/70'}`}>
                    exit {exitCode}
                  </span>
                )}
              </div>
              {/* Screenshot preview */}
              {screenshot && (
                <div className="mb-2">
                  <ImagePreview 
                    src={screenshot} 
                    alt={`${toolCall.tool} result`}
                  />
                </div>
              )}
              {outputDisplay && (
                <pre className="text-[11px] text-white/60 font-mono whitespace-pre-wrap break-all bg-black/20 rounded px-2 py-1.5 max-h-40 overflow-auto">
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

