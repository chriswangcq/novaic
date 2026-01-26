import { useState } from 'react';
import { ChevronRight, Brain } from 'lucide-react';

interface ThinkingBlockProps {
  content: string;
  defaultCollapsed?: boolean;
}

export function ThinkingBlock({ content, defaultCollapsed = false }: ThinkingBlockProps) {
  const [isCollapsed, setIsCollapsed] = useState(defaultCollapsed);
  
  // 截取预览文本（折叠时显示）
  const preview = content.length > 150 
    ? content.slice(0, 150).trim() + '...' 
    : content;

  return (
    <div className="rounded-lg bg-white/[0.02] border border-white/[0.06] overflow-hidden">
      {/* Header - 可点击展开/折叠 */}
      <button
        onClick={() => setIsCollapsed(!isCollapsed)}
        className="w-full flex items-center gap-2 px-3 py-2 hover:bg-white/[0.02] transition-colors text-left"
      >
        <ChevronRight 
          size={14} 
          className={`text-white/30 transition-transform ${!isCollapsed ? 'rotate-90' : ''}`}
        />
        <Brain size={14} className="text-violet-400/60" />
        <span className="text-xs font-medium text-white/40">Thinking</span>
        {isCollapsed && (
          <span className="flex-1 text-xs text-white/30 truncate ml-2">
            {preview}
          </span>
        )}
      </button>
      
      {/* Content */}
      {!isCollapsed && (
        <div className="px-3 pb-3 pt-1 border-t border-white/[0.04]">
          <p className="text-[13px] text-white/50 leading-relaxed whitespace-pre-wrap">
            {content}
          </p>
        </div>
      )}
    </div>
  );
}

