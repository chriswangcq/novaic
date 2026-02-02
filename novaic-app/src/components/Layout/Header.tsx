import { Settings, Trash2, ChevronLeft } from 'lucide-react';
import { AgentSelector } from './AgentSelector';
import { CreateAgentModal, SetupConfig } from '../Agent/CreateAgentModal';
import { useAppStore } from '../../store';

interface HeaderProps {
  onOpenSettings: () => void;
  onBackToDashboard?: () => void;
  onAgentCreated?: (config: SetupConfig) => void;
}

export function Header(props: HeaderProps) {
  const { onOpenSettings, onBackToDashboard, onAgentCreated } = props;
  const { createAgentModalOpen, setCreateAgentModalOpen, clearMessages } = useAppStore();

  return (
    <>
      <header className="h-10 bg-nb-surface border-b border-nb-border flex items-center px-3 no-select shrink-0" data-tauri-drag-region>
        {/* Back to Dashboard */}
        {onBackToDashboard && (
          <button
            onClick={onBackToDashboard}
            className="flex items-center gap-1 px-2 py-1 hover:bg-nb-surface-2 rounded-lg transition-colors mr-2 text-nb-text-secondary hover:text-nb-text"
            title="Back to Dashboard"
          >
            <ChevronLeft size={16} />
            <span className="text-xs">Dashboard</span>
          </button>
        )}

        {/* Logo */}
        <div className="flex items-center gap-2">
          <img src="/logo.png" alt="NovAIC" className="w-6 h-6" />
          <span className="font-semibold text-nb-text text-[13px]">NovAIC</span>
        </div>

        {/* Divider */}
        <div className="w-px h-4 bg-nb-border mx-2.5" />

        {/* Agent Selector */}
        <AgentSelector onCreateNew={() => setCreateAgentModalOpen(true)} />

        {/* Spacer */}
        <div className="flex-1" data-tauri-drag-region />

        {/* Actions */}
        <div className="flex items-center gap-1">
          {/* Clear chat */}
          <button
            className="p-1.5 hover:bg-nb-surface-2 rounded-lg transition-colors"
            onClick={clearMessages}
            title="Clear chat"
          >
            <Trash2 size={15} className="text-nb-text-muted" />
          </button>
          
          {/* Settings */}
          <button
            className="p-1.5 hover:bg-nb-surface-2 rounded-lg transition-colors"
            onClick={onOpenSettings}
            title="Settings"
          >
            <Settings size={15} className="text-nb-text-muted" />
          </button>
        </div>
      </header>

      {/* Create Agent Modal */}
      <CreateAgentModal 
        isOpen={createAgentModalOpen} 
        onClose={() => setCreateAgentModalOpen(false)}
        onCreated={onAgentCreated}
      />
    </>
  );
}

