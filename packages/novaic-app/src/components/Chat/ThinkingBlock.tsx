import { useState } from 'react';
import { ChevronRight } from 'lucide-react';

interface ThinkingBlockProps {
  content: string;
  defaultCollapsed?: boolean;
}

export function ThinkingBlock({ content, defaultCollapsed = true }: ThinkingBlockProps) {
  const [isCollapsed, setIsCollapsed] = useState(defaultCollapsed);
  
  // 截取预览文本（折叠时显示）
  const preview = content.length > 80 
    ? content.slice(0, 80).trim() + '...' 
    : content;

  return (
    <div className="relative pl-3 border-l-2 border-violet-500/30">
      {/* Header - 可点击展开/折叠 */}
      <button
        onClick={() => setIsCollapsed(!isCollapsed)}
        className="flex items-center gap-1.5 text-left hover:bg-white/[0.02] rounded px-1 -ml-1 transition-colors"
      >
        <ChevronRight 
          size={12} 
          className={`text-violet-400/50 transition-transform shrink-0 ${!isCollapsed ? 'rotate-90' : ''}`}
        />
        <span className="text-[11px] font-medium text-violet-400/60 italic">Thinking</span>
        {isCollapsed && (
          <span className="text-[11px] text-white/25 truncate">
            {preview}
          </span>
        )}
      </button>
      
      {/* Content */}
      {!isCollapsed && (
        <div className="mt-1 ml-4">
          <p className="text-[12px] text-white/40 leading-relaxed whitespace-pre-wrap italic">
            {content}
          </p>
        </div>
      )}
    </div>
  );
}

