import { Message } from '../../types';
import { UserMessage } from './UserMessage';
import { AssistantMessage } from './AssistantMessage';
import { WelcomeScreen } from './WelcomeScreen';
import { StreamingIndicator } from './StreamingIndicator';

interface MessageListProps {
  messages: Message[];
  isLoading: boolean;
}

export function MessageList({ messages, isLoading }: MessageListProps) {
  // Empty state
  if (messages.length === 0 && !isLoading) {
    return <WelcomeScreen />;
  }

  return (
    <div className="px-3 py-3 space-y-3">
      {messages.map((message) => (
        <div 
          key={message.id}
          className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
        >
          <div className={`max-w-[85%] ${message.role === 'user' ? '' : ''}`}>
            {message.role === 'user' 
              ? <UserMessage message={message} />
              : <AssistantMessage message={message} />
            }
          </div>
        </div>
      ))}
      
      {/* Loading indicator when waiting for first response */}
      {isLoading && messages.length > 0 && 
        messages[messages.length - 1].role === 'user' && (
        <div className="flex justify-start">
          <StreamingIndicator />
        </div>
      )}
    </div>
  );
}
