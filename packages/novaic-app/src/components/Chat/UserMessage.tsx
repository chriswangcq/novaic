import { Message } from '../../types';
import { User } from 'lucide-react';

interface UserMessageProps {
  message: Message;
}

export function UserMessage({ message }: UserMessageProps) {
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

