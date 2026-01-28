import { useEffect, useCallback } from 'react';
import { ChatPanel } from './components/Chat/ChatPanel';
import { VisualPanel } from './components/Visual/VisualPanel';
import { Resizer } from './components/Layout/Resizer';
import { Header } from './components/Layout/Header';
import { useAppStore } from './store';
import { SettingsModal } from './components/Settings/SettingsModal';

// Layout constraints
const MIN_CHAT_WIDTH = 300;
const MAX_CHAT_WIDTH = 800;
const MIN_VM_WIDTH = 400;

function App() {
  const { 
    initialize, 
    isInitialized, 
    layoutMode, 
    leftPanelWidth, 
    setLeftPanelWidth,
    settingsOpen,
    setSettingsOpen
  } = useAppStore();

  useEffect(() => {
    // Initialize app on mount
    initialize();
  }, [initialize]);

  // Handle resize with constraints
  const handleResize = useCallback((delta: number) => {
    const newWidth = Math.max(
      MIN_CHAT_WIDTH,
      Math.min(MAX_CHAT_WIDTH, leftPanelWidth + delta)
    );
    // Also ensure VM panel has minimum width
    const containerWidth = window.innerWidth;
    const maxAllowedWidth = containerWidth - MIN_VM_WIDTH;
    setLeftPanelWidth(Math.min(newWidth, maxAllowedWidth));
  }, [leftPanelWidth, setLeftPanelWidth]);

  // Reset to default width on double-click
  const handleResetWidth = useCallback(() => {
    setLeftPanelWidth(400);
  }, [setLeftPanelWidth]);

  return (
    <div className="h-screen flex flex-col bg-nb-bg">
      {/* Header with Agent Selector */}
      <Header onOpenSettings={() => setSettingsOpen(true)} />

      {/* Main Content */}
      <main className="flex-1 flex overflow-hidden relative">
        {/* Full mode: only VM */}
        {layoutMode === 'full' && (
          <div className="flex-1 flex flex-col overflow-hidden">
            <VisualPanel />
          </div>
        )}

        {/* Normal mode: Chat + Resizer + VM */}
        {layoutMode === 'normal' && (
          <>
            {/* Left: Chat Panel */}
            <div 
              className="border-r border-nb-border flex flex-col shrink-0"
              style={{ width: leftPanelWidth }}
            >
              <ChatPanel />
            </div>
            
            {/* Resizer */}
            <Resizer onResize={handleResize} onDoubleClick={handleResetWidth} />
            
            {/* Right: Visual Panel (VNC + Logs) */}
            <div className="flex-1 flex flex-col overflow-hidden min-w-0">
              <VisualPanel />
            </div>
          </>
        )}

        {/* Mini mode: Chat expanded + VM thumbnail */}
        {layoutMode === 'mini' && (
          <>
            {/* Full width Chat Panel */}
            <div className="flex-1 flex flex-col overflow-hidden">
              <ChatPanel />
            </div>
            
            {/* Floating VM Thumbnail - entire div is clickable */}
            <div 
              className="absolute bottom-4 right-4 w-[280px] h-[200px] rounded-lg overflow-hidden shadow-2xl border border-nb-border bg-nb-surface z-50 group cursor-pointer"
              onClick={() => useAppStore.getState().setLayoutMode('normal')}
            >
              <VisualPanel isThumbnail />
              {/* Expand hint on hover */}
              <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center pointer-events-none">
                <span className="text-white text-sm">Click to expand</span>
              </div>
            </div>
          </>
        )}
      </main>

      <SettingsModal open={settingsOpen} onClose={() => setSettingsOpen(false)} />
      
      {/* Status bar */}
      <footer className="h-6 bg-nb-surface border-t border-nb-border px-4 flex items-center text-xs text-nb-text-muted">
        <span className={`w-2 h-2 rounded-full mr-2 ${isInitialized ? 'bg-nb-success' : 'bg-nb-warning'}`} />
        <span>{isInitialized ? 'Connected' : 'Connecting...'}</span>
        <span className="ml-auto">NovAIC v0.1.0</span>
      </footer>
    </div>
  );
}

export default App;

