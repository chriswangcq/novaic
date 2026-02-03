/**
 * Agent Drawer Component
 * 
 * 微信风格的侧边抽屉，用于显示和切换 Agent 列表
 */

import { useEffect, useRef, useCallback, useState } from 'react';
import { X, Plus, Trash2, Monitor, Loader2, Settings, Play, Square } from 'lucide-react';
import { useAppStore } from '../../store';
import type { AICAgent } from '../../services/api';
import { vmService, VmStatus } from '../../services/vm';

interface AgentDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectAgent: (agentId: string, needsSetup: boolean) => void;
  onCreateNew: () => void;
}

export function AgentDrawer({ isOpen, onClose, onSelectAgent, onCreateNew }: AgentDrawerProps) {
  const { agents, currentAgentId, loadAgents, deleteAgent } = useAppStore();
  const [isLoading, setIsLoading] = useState(false);
  const [vmStatuses, setVmStatuses] = useState<Record<string, VmStatus>>({});
  const [startingVm, setStartingVm] = useState<string | null>(null);
  const drawerRef = useRef<HTMLDivElement>(null);

  // Load agents on mount
  useEffect(() => {
    if (isOpen) {
      loadAgents();
    }
  }, [isOpen, loadAgents]);

  // Poll VM statuses
  const refreshVmStatuses = useCallback(async () => {
    try {
      const allStatuses = await vmService.getAllStatus();
      setVmStatuses(allStatuses || {});
    } catch (error) {
      // Ignore
    }
  }, []);

  useEffect(() => {
    if (isOpen) {
      refreshVmStatuses();
      const interval = setInterval(refreshVmStatuses, 5000);
      return () => clearInterval(interval);
    }
  }, [isOpen, refreshVmStatuses]);

  // Close drawer when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (drawerRef.current && !drawerRef.current.contains(event.target as Node)) {
        onClose();
      }
    }
    if (isOpen) {
      // 延迟添加监听，避免打开时立即触发
      const timeout = setTimeout(() => {
        document.addEventListener('mousedown', handleClickOutside);
      }, 100);
      return () => {
        clearTimeout(timeout);
        document.removeEventListener('mousedown', handleClickOutside);
      };
    }
  }, [isOpen, onClose]);

  // Handle keyboard escape
  useEffect(() => {
    function handleEscape(event: KeyboardEvent) {
      if (event.key === 'Escape') {
        onClose();
      }
    }
    if (isOpen) {
      document.addEventListener('keydown', handleEscape);
      return () => document.removeEventListener('keydown', handleEscape);
    }
  }, [isOpen, onClose]);

  const handleSelect = (agent: AICAgent) => {
    const needsSetup = !agent.setup_complete;
    onSelectAgent(agent.id, needsSetup);
    onClose();
  };

  const handleDelete = async (e: React.MouseEvent, agentId: string) => {
    e.stopPropagation();
    if (agents.length <= 1) {
      alert('Cannot delete the only agent');
      return;
    }
    if (!confirm('Are you sure you want to delete this agent?')) {
      return;
    }

    setIsLoading(true);
    try {
      // Stop VM first if it's running
      const vmStatus = vmStatuses[agentId];
      if (vmStatus?.running) {
        try {
          await vmService.stop(agentId);
          await new Promise(resolve => setTimeout(resolve, 1000));
        } catch (e) {
          console.warn('Failed to stop VM, continuing with delete:', e);
        }
      }
      
      await deleteAgent(agentId);
      await loadAgents();
    } catch (error) {
      console.error('Failed to delete agent:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleStartVm = async (e: React.MouseEvent, agent: AICAgent) => {
    e.stopPropagation();
    if (!agent.setup_complete) return;
    
    setStartingVm(agent.id);
    try {
      const agentIndex = agent.vm.agent_index ?? 0;
      await vmService.start(agent.id, agentIndex);
      await refreshVmStatuses();
    } catch (error) {
      console.error('Failed to start VM:', error);
    } finally {
      setStartingVm(null);
    }
  };

  const handleStopVm = async (e: React.MouseEvent, agentId: string) => {
    e.stopPropagation();
    setIsLoading(true);
    try {
      await vmService.stop(agentId);
      await refreshVmStatuses();
    } catch (error) {
      console.error('Failed to stop VM:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // Get status info for an agent
  const getStatusInfo = (agent: AICAgent) => {
    const vmStatus = vmStatuses[agent.id];
    
    if (!agent.setup_complete) {
      if (agent.setup_progress?.error) {
        return { color: 'bg-red-500', text: 'Setup failed' };
      }
      if (agent.setup_progress) {
        return { color: 'bg-yellow-500', text: 'Setting up...' };
      }
      return { color: 'bg-blue-500', text: 'Needs setup' };
    }
    
    if (vmStatus?.running) {
      return { color: 'bg-green-500', text: 'Running' };
    }
    return { color: 'bg-gray-500', text: 'Stopped' };
  };

  return (
    <>
      {/* Backdrop */}
      <div 
        className={`fixed inset-0 bg-black/50 z-40 transition-opacity duration-300 ${
          isOpen ? 'opacity-100' : 'opacity-0 pointer-events-none'
        }`}
      />
      
      {/* Drawer */}
      <div
        ref={drawerRef}
        className={`fixed top-0 left-0 h-full w-72 bg-nb-surface border-r border-nb-border z-50 transform transition-transform duration-300 ease-out flex flex-col ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        {/* Header */}
        <div className="h-12 px-4 flex items-center justify-between border-b border-nb-border shrink-0">
          <span className="font-semibold text-nb-text text-sm">Agents</span>
          <button
            onClick={onClose}
            className="p-1.5 hover:bg-nb-hover rounded-lg transition-colors"
          >
            <X size={18} className="text-nb-text-muted" />
          </button>
        </div>

        {/* Agent List */}
        <div className="flex-1 overflow-y-auto">
          {agents.length === 0 ? (
            <div className="px-4 py-8 text-center text-nb-text-secondary text-sm">
              <Monitor size={32} className="mx-auto mb-3 opacity-50" />
              <p>No agents yet</p>
              <p className="text-xs mt-1">Create one to get started</p>
            </div>
          ) : (
            <div className="py-2">
              {agents.map(agent => {
                const statusInfo = getStatusInfo(agent);
                const vmStatus = vmStatuses[agent.id];
                const isSelected = agent.id === currentAgentId;
                const isVmRunning = vmStatus?.running;
                
                return (
                  <div
                    key={agent.id}
                    onClick={() => handleSelect(agent)}
                    className={`px-4 py-3 cursor-pointer hover:bg-nb-hover transition-colors ${
                      isSelected ? 'bg-nb-hover border-l-2 border-l-blue-500' : ''
                    }`}
                  >
                    <div className="flex items-start gap-3">
                      {/* Avatar/Icon */}
                      <div className="w-10 h-10 rounded-lg bg-nb-surface-2 flex items-center justify-center shrink-0">
                        <Monitor size={20} className="text-nb-text-muted" />
                      </div>
                      
                      {/* Info */}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-medium text-nb-text truncate">
                            {agent.name}
                          </span>
                          <span className={`w-2 h-2 rounded-full shrink-0 ${statusInfo.color}`} />
                        </div>
                        <div className="text-xs text-nb-text-secondary mt-0.5">
                          {agent.vm.os_type} {agent.vm.os_version}
                        </div>
                        <div className="text-xs text-nb-text-muted mt-0.5">
                          {statusInfo.text}
                        </div>
                      </div>
                      
                      {/* Actions */}
                      <div className="flex items-center gap-1 shrink-0">
                        {/* VM Control */}
                        {agent.setup_complete && (
                          isVmRunning ? (
                            <button
                              onClick={(e) => handleStopVm(e, agent.id)}
                              className="p-1.5 rounded hover:bg-red-500/20 text-nb-text-secondary hover:text-red-400 transition-colors"
                              title="Stop VM"
                            >
                              <Square size={14} />
                            </button>
                          ) : (
                            <button
                              onClick={(e) => handleStartVm(e, agent)}
                              disabled={startingVm === agent.id}
                              className="p-1.5 rounded hover:bg-green-500/20 text-nb-text-secondary hover:text-green-400 transition-colors disabled:opacity-50"
                              title="Start VM"
                            >
                              {startingVm === agent.id ? (
                                <Loader2 size={14} className="animate-spin" />
                              ) : (
                                <Play size={14} />
                              )}
                            </button>
                          )
                        )}
                        
                        {/* Setup button for incomplete agents */}
                        {!agent.setup_complete && (
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              handleSelect(agent);
                            }}
                            className="p-1.5 rounded hover:bg-blue-500/20 text-nb-text-secondary hover:text-blue-400 transition-colors"
                            title="Setup"
                          >
                            <Settings size={14} />
                          </button>
                        )}
                        
                        {/* Delete */}
                        {agents.length > 1 && (
                          <button
                            onClick={(e) => handleDelete(e, agent.id)}
                            disabled={isLoading}
                            className="p-1.5 rounded hover:bg-red-500/20 text-nb-text-secondary hover:text-red-400 transition-colors disabled:opacity-50"
                            title="Delete"
                          >
                            <Trash2 size={14} />
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Footer - Create New */}
        <div className="p-3 border-t border-nb-border shrink-0">
          <button
            onClick={() => {
              onCreateNew();
              onClose();
            }}
            className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-nb-accent hover:bg-nb-accent/80 text-white rounded-lg transition-colors text-sm font-medium"
          >
            <Plus size={18} />
            <span>Create New Agent</span>
          </button>
        </div>
      </div>
    </>
  );
}
