import { useEffect, useState } from 'react';
import { Header } from './components/Layout/Header';
import { ChatPanel } from './components/Chat/ChatPanel';
import { VisualPanel } from './components/Visual/VisualPanel';
import { useAppStore } from './store';
import { SettingsModal } from './components/Settings/SettingsModal';

function App() {
  const { initialize, isInitialized } = useAppStore();
  const [settingsOpen, setSettingsOpen] = useState(false);

  useEffect(() => {
    // Initialize app on mount
    initialize();
  }, [initialize]);

  return (
    <div className="h-screen flex flex-col bg-nb-bg">
      {/* Header */}
      <Header onOpenSettings={() => setSettingsOpen(true)} />
      
      {/* Main Content */}
      <main className="flex-1 flex overflow-hidden">
        {/* Left: Chat Panel */}
        <div className="w-[400px] min-w-[350px] border-r border-nb-border flex flex-col">
          <ChatPanel />
        </div>
        
        {/* Right: Visual Panel (VNC + Logs) */}
        <div className="flex-1 flex flex-col overflow-hidden">
          <VisualPanel />
        </div>
      </main>

      <SettingsModal open={settingsOpen} onClose={() => setSettingsOpen(false)} />
      
      {/* Status bar */}
      <footer className="h-6 bg-nb-surface border-t border-nb-border px-4 flex items-center text-xs text-nb-text-muted">
        <span className={`w-2 h-2 rounded-full mr-2 ${isInitialized ? 'bg-nb-success' : 'bg-nb-warning'}`} />
        <span>{isInitialized ? 'Connected' : 'Connecting...'}</span>
        <span className="ml-auto">NB-CC v0.1.0</span>
      </footer>
    </div>
  );
}

export default App;

