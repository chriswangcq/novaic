import { Message, MessageStatus } from '../../types';
import { User, Check, CheckCheck, Clock, AlertCircle } from 'lucide-react';

interface UserMessageProps {
  message: Message;
}

// Status display configuration
const statusConfig: Record<MessageStatus, { icon: typeof Check; text: string; className: string }> = {
  sending: { icon: Clock, text: '发送中...', className: 'text-white/30' },
  delivered: { icon: Check, text: '已送达', className: 'text-white/40' },
  read: { icon: CheckCheck, text: '已读', className: 'text-blue-400' },
  replied: { icon: CheckCheck, text: '已回复', className: 'text-green-400' },
  error: { icon: AlertCircle, text: '发送失败', className: 'text-red-400' },
};

export function UserMessage({ message }: UserMessageProps) {
  const status = message.status || 'delivered';
  const statusInfo = statusConfig[status];
  const StatusIcon = statusInfo.icon;
  
  return (
    <div className="group py-2">
      {/* Header: icon + label */}
      <div className="flex items-center gap-1.5 mb-1">
        <User size={12} className="text-white/30" />
        <span className="text-[11px] font-medium text-white/40 uppercase tracking-wide">You</span>
      </div>
      
      {/* Message content - no bubble, just text */}
      <div className="text-[13px] text-white/90 leading-relaxed whitespace-pre-wrap pl-[18px]">
        {message.content}
      </div>

      {/* Message status */}
      <div className={`flex items-center gap-1 mt-1 pl-[18px] text-[10px] ${statusInfo.className}`}>
        <StatusIcon size={12} className={status === 'sending' ? 'animate-pulse' : ''} />
        <span>{statusInfo.text}</span>
      </div>

      {/* Attachments */}
      {message.attachments && message.attachments.length > 0 && (
        <div className="mt-1.5 pl-[18px] flex flex-wrap gap-1.5">
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

