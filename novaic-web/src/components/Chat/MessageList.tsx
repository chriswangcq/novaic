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
        message.role === 'user' 
          ? <UserMessage key={message.id} message={message} />
          : <AssistantMessage key={message.id} message={message} />
      ))}
      
      {/* Loading indicator when waiting for first response */}
      {isLoading && messages.length > 0 && 
        messages[messages.length - 1].role === 'user' && (
        <StreamingIndicator />
      )}
    </div>
  );
}
