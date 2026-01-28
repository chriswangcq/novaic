import { useEffect, useCallback, useState, Component, ReactNode, ErrorInfo } from 'react';
import { ChatPanel } from './components/Chat/ChatPanel';
import { VisualPanel } from './components/Visual/VisualPanel';
import { Resizer } from './components/Layout/Resizer';
import { Header } from './components/Layout/Header';
import { useAppStore } from './store';
import { SettingsModal } from './components/Settings/SettingsModal';
import { AgentDashboard } from './components/Dashboard';
import { Loader2, AlertTriangle, RefreshCw } from 'lucide-react';

// Layout constraints
const MIN_CHAT_WIDTH = 300;
const MAX_CHAT_WIDTH = 800;
const MIN_VM_WIDTH = 400;

// Global Error Boundary
interface ErrorBoundaryState {
  hasError: boolean;
  error?: Error;
  errorInfo?: ErrorInfo;
}

class AppErrorBoundary extends Component<{ children: ReactNode }, ErrorBoundaryState> {
  constructor(props: { children: ReactNode }) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('[App] Uncaught error:', error, errorInfo);
    this.setState({ errorInfo });
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="h-screen flex flex-col items-center justify-center bg-[#0a0a0a] text-white p-8">
          <AlertTriangle size={48} className="text-red-500 mb-4" />
          <h1 className="text-xl font-bold mb-2">Something went wrong</h1>
          <p className="text-white/60 mb-4 text-center max-w-md">
            {this.state.error?.message || 'An unexpected error occurred'}
          </p>
          <button
            onClick={() => {
              this.setState({ hasError: false, error: undefined, errorInfo: undefined });
              window.location.reload();
            }}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors"
          >
            <RefreshCw size={16} />
            Reload App
          </button>
          {this.state.errorInfo && (
            <details className="mt-4 text-[11px] text-white/40 max-w-lg overflow-auto">
              <summary className="cursor-pointer">Error Details</summary>
              <pre className="mt-2 p-2 bg-black/50 rounded text-left whitespace-pre-wrap">
                {this.state.error?.stack}
              </pre>
            </details>
          )}
        </div>
      );
    }
    return this.props.children;
  }
}

function App() {
  const { 
    initialize, 
    isInitialized, 
    layoutMode, 
    leftPanelWidth, 
    setLeftPanelWidth,
    settingsOpen,
    setSettingsOpen,
    agents,
    currentAgentId,
    loadAgents
  } = useAppStore();

  const [isLoadingAgents, setIsLoadingAgents] = useState(true);
  const [inWorkspace, setInWorkspace] = useState(false);

  useEffect(() => {
    // Initialize app on mount
    initialize();
  }, [initialize]);

  // Load agents after gateway is initialized
  useEffect(() => {
    const checkAgents = async () => {
      setIsLoadingAgents(true);
      try {
        await loadAgents();
      } catch (error) {
        console.error('Failed to load agents:', error);
      } finally {
        setIsLoadingAgents(false);
      }
    };
    
    if (isInitialized) {
      checkAgents();
    }
  }, [isInitialized, loadAgents]);

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

  // Enter workspace for an agent
  const handleEnterWorkspace = useCallback((agentId: string) => {
    console.log('[App] Entering workspace for agent:', agentId);
    setInWorkspace(true);
  }, []);

  // Back to dashboard
  const handleBackToDashboard = useCallback(() => {
    setInWorkspace(false);
  }, []);

  // Show loading screen while initializing
  if (!isInitialized || isLoadingAgents) {
    return (
      <div className="h-screen flex flex-col items-center justify-center bg-nb-bg">
        <Loader2 size={32} className="animate-spin text-blue-500 mb-4" />
        <p className="text-nb-text-secondary">
          {!isInitialized ? 'Connecting to services...' : 'Loading...'}
        </p>
      </div>
    );
  }

  // Show Dashboard (agent list) if not in workspace
  if (!inWorkspace) {
    return <AgentDashboard onEnterWorkspace={handleEnterWorkspace} />;
  }

  return (
    <div className="h-screen flex flex-col bg-nb-bg">
      {/* Header with Agent Selector */}
      <Header 
        onOpenSettings={() => setSettingsOpen(true)} 
        onBackToDashboard={handleBackToDashboard}
      />

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

// Wrap App with Error Boundary
function AppWithErrorBoundary() {
  return (
    <AppErrorBoundary>
      <App />
    </AppErrorBoundary>
  );
}

export default AppWithErrorBoundary;

