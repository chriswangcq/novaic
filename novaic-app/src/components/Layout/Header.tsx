import { Settings, Trash2, Menu, Monitor } from 'lucide-react';
import { CreateAgentModal, SetupConfig } from '../Agent/CreateAgentModal';
import { useAppStore } from '../../store';

interface HeaderProps {
  onOpenSettings: () => void;
  onToggleDrawer: () => void;
  onAgentCreated?: (config: SetupConfig) => void;
}

export function Header(props: HeaderProps) {
  const { onOpenSettings, onToggleDrawer, onAgentCreated } = props;
  const { createAgentModalOpen, setCreateAgentModalOpen, clearMessages, agents, currentAgentId } = useAppStore();
  
  const currentAgent = agents.find(a => a.id === currentAgentId);

  return (
    <>
      <header className="h-10 bg-nb-surface border-b border-nb-border flex items-center px-3 no-select shrink-0" data-tauri-drag-region>
        {/* Logo */}
        <div className="flex items-center gap-2">
          <img src="/logo.png" alt="NovAIC" className="w-6 h-6" />
          <span className="font-semibold text-nb-text text-[13px]">NovAIC</span>
        </div>

        {/* Divider */}
        <div className="w-px h-4 bg-nb-border mx-2.5" />

        {/* Menu Button - 三横杠 */}
        <button
          onClick={onToggleDrawer}
          className="p-1.5 hover:bg-nb-surface-2 rounded-lg transition-colors mr-1"
          title="Agent List"
        >
          <Menu size={18} className="text-nb-text-muted" />
        </button>

        {/* Current Agent Display */}
        <div className="flex items-center gap-2 px-2 py-1 text-sm">
          <Monitor size={16} className="text-nb-text-secondary" />
          <span className="text-nb-text max-w-[150px] truncate">
            {currentAgent?.name || 'No Agent'}
          </span>
          {currentAgent && (
            <span className={`w-2 h-2 rounded-full ${
              currentAgent.setup_complete ? 'bg-green-500' : 'bg-blue-500'
            }`} />
          )}
        </div>

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

