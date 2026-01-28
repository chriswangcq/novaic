import { Settings, Maximize2, Minimize2 } from 'lucide-react';
import { useState } from 'react';
import { AgentSelector } from './AgentSelector';
import { CreateAgentModal } from '../Agent/CreateAgentModal';
import { useAppStore } from '../../store';

export function Header(props: { onOpenSettings: () => void }) {
  const [isMaximized, setIsMaximized] = useState(false);
  const { createAgentModalOpen, setCreateAgentModalOpen } = useAppStore();

  return (
    <>
      <header className="h-12 bg-nb-surface border-b border-nb-border flex items-center px-4 no-select" data-tauri-drag-region>
        {/* Logo */}
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center">
            <span className="text-white font-bold text-[11px]">NA</span>
          </div>
          <span className="font-semibold text-nb-text text-[14px]">NovAIC</span>
        </div>

        {/* Divider */}
        <div className="w-px h-5 bg-nb-border mx-3" />

        {/* Agent Selector */}
        <AgentSelector onCreateNew={() => setCreateAgentModalOpen(true)} />

        {/* Spacer */}
        <div className="flex-1" data-tauri-drag-region />

        {/* Actions */}
        <div className="flex items-center gap-2">
          {/* Settings */}
          <button
            className="p-2 hover:bg-nb-surface-2 rounded-lg transition-colors"
            onClick={props.onOpenSettings}
          >
            <Settings size={18} className="text-nb-text-muted" />
          </button>

          {/* Window controls (for custom titlebar) */}
          <div className="flex items-center ml-2 gap-1">
            <button
              onClick={() => setIsMaximized(!isMaximized)}
              className="p-1.5 hover:bg-nb-surface-2 rounded transition-colors"
            >
              {isMaximized ? (
                <Minimize2 size={14} className="text-nb-text-muted" />
              ) : (
                <Maximize2 size={14} className="text-nb-text-muted" />
              )}
            </button>
          </div>
        </div>
      </header>

      {/* Create Agent Modal */}
      <CreateAgentModal 
        isOpen={createAgentModalOpen} 
        onClose={() => setCreateAgentModalOpen(false)} 
      />
    </>
  );
}

