import { Message, MessageStatus } from '../../types';
import { User, Check, CheckCheck, Clock, AlertCircle, ChevronDown } from 'lucide-react';
import { Markdown } from './Markdown';
import { useAppStore } from '../../store';

interface UserMessageProps {
  message: Message;
}

// Status display configuration
const statusConfig: Record<MessageStatus, { icon: typeof Check; text: string; className: string }> = {
  sending: { icon: Clock, text: '发送中...', className: 'text-white/30' },
  delivered: { icon: Check, text: '已送达', className: 'text-white/40' },
  read: { icon: CheckCheck, text: '已读', className: 'text-blue-400' },
  error: { icon: AlertCircle, text: '发送失败', className: 'text-red-400' },
};

export function UserMessage({ message }: UserMessageProps) {
  const status = message.status || 'delivered';
  const statusInfo = statusConfig[status];
  const StatusIcon = statusInfo.icon;
  const expandMessage = useAppStore((state) => state.expandMessage);
  
  const handleExpand = () => {
    expandMessage(message.id);
  };
  
  return (
    <div className="group py-2">
      {/* Header: icon + label - right aligned */}
      <div className="flex items-center gap-1.5 mb-1 justify-end">
        <span className="text-[11px] font-medium text-white/40 uppercase tracking-wide">You</span>
        <User size={12} className="text-white/30" />
      </div>
      
      {/* Message content with bubble style */}
      <div className="bg-violet-600/20 border border-violet-500/20 rounded-lg px-3 py-2">
        <Markdown content={message.content} />
        
        {/* Expand button for truncated messages */}
        {message.isTruncated && (
          <button
            onClick={handleExpand}
            className="flex items-center gap-1 mt-2 text-[11px] text-violet-400 hover:text-violet-300 transition-colors"
          >
            <ChevronDown size={14} />
            <span>查看更多</span>
          </button>
        )}
      </div>

      {/* Message status - right aligned */}
      <div className={`flex items-center gap-1 mt-1 justify-end text-[10px] ${statusInfo.className}`}>
        <StatusIcon size={12} className={status === 'sending' ? 'animate-pulse' : ''} />
        <span>{statusInfo.text}</span>
      </div>

      {/* Attachments - right aligned */}
      {message.attachments && message.attachments.length > 0 && (
        <div className="mt-1.5 flex flex-wrap gap-1.5 justify-end">
          {message.attachments.map((attachment) => (
            <div
              key={attachment.id}
              className="flex items-center gap-1.5 px-2 py-1 rounded bg-white/[0.04] border border-white/[0.06] text-[11px] text-white/50"
            >
              <span className="truncate max-w-[120px]">{attachment.name}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

