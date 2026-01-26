import { Message } from '../../types';

interface UserMessageProps {
  message: Message;
}

export function UserMessage({ message }: UserMessageProps) {
  return (
    <div className="group">
      {/* User label */}
      <div className="flex items-center gap-2 mb-1.5">
        <span className="text-xs font-medium text-white/40">You</span>
        <span className="text-xs text-white/20">
          {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </span>
      </div>
      
      {/* Message content */}
      <div className="text-[14px] text-white/90 leading-relaxed whitespace-pre-wrap">
        {message.content}
      </div>

      {/* Attachments */}
      {message.attachments && message.attachments.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-2">
          {message.attachments.map((attachment) => (
            <div
              key={attachment.id}
              className="flex items-center gap-2 px-2.5 py-1.5 rounded-md bg-white/[0.04] border border-white/[0.06] text-xs text-white/60"
            >
              <span className="truncate max-w-[150px]">{attachment.name}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

