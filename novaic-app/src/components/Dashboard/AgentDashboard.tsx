/**
 * Agent Dashboard - 一级管理页面
 * 
 * 显示所有 Agent 的列表，每个 Agent 占一个大 Banner
 * 展示状态：stopped | starting | running | error
 */

import { useState, useEffect, useCallback } from 'react';
import { invoke } from '@tauri-apps/api/core';
import { useAppStore } from '../../store';
import { AICAgent } from '../../services/api';
import { 
  Plus, 
  Play, 
  Square, 
  Trash2, 
  Monitor, 
  Cpu, 
  HardDrive,
  Loader2,
  AlertCircle,
  CheckCircle2,
  Circle
} from 'lucide-react';
import { CreateAgentModal } from '../Agent/CreateAgentModal';

interface AgentCardProps {
  agent: AICAgent;
  status: AICAgent['status'];  // Computed status from VM
  isSelected: boolean;
  onSelect: () => void;
  onStart: () => void;
  onStop: () => void;
  onDelete: () => void;
  onEnter: () => void;
}

// 状态配置
const statusConfig: Record<string, {
  color: string;
  textColor: string;
  label: string;
  icon: typeof Circle;
  animate?: boolean;
}> = {
  stopped: {
    color: 'bg-gray-500',
    textColor: 'text-gray-400',
    label: 'Stopped',
    icon: Circle,
  },
  starting: {
    color: 'bg-yellow-500',
    textColor: 'text-yellow-400',
    label: 'Starting...',
    icon: Loader2,
    animate: true,
  },
  running: {
    color: 'bg-green-500',
    textColor: 'text-green-400',
    label: 'Running',
    icon: CheckCircle2,
  },
  error: {
    color: 'bg-red-500',
    textColor: 'text-red-400',
    label: 'Error',
    icon: AlertCircle,
  },
};

function AgentCard({ agent, status: agentStatus, isSelected, onSelect, onStart, onStop, onDelete, onEnter }: AgentCardProps) {
  const status = statusConfig[agentStatus] || statusConfig.stopped;
  const StatusIcon = status.icon;
  const isRunning = agentStatus === 'running';
  const isStarting = agentStatus === 'starting';

  return (
    <div 
      className={`
        relative p-6 rounded-xl border-2 transition-all duration-200 cursor-pointer
        ${isSelected 
          ? 'border-blue-500 bg-blue-500/10' 
          : 'border-nb-border bg-nb-surface hover:border-nb-border-hover hover:bg-nb-surface-hover'
        }
      `}
      onClick={onSelect}
    >
      {/* 状态指示器 */}
      <div className="absolute top-4 right-4 flex items-center gap-2">
        <StatusIcon 
          size={16} 
          className={`${status.textColor} ${status.animate ? 'animate-spin' : ''}`} 
        />
        <span className={`text-sm ${status.textColor}`}>{status.label}</span>
      </div>

      {/* Agent 名称 */}
      <h3 className="text-xl font-semibold text-nb-text mb-4 pr-24">{agent.name}</h3>

      {/* VM 配置信息 */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="flex items-center gap-2 text-nb-text-secondary">
          <Monitor size={16} />
          <span className="text-sm">{agent.vm.os_type || 'Ubuntu'}</span>
        </div>
        <div className="flex items-center gap-2 text-nb-text-secondary">
          <Cpu size={16} />
          <span className="text-sm">{agent.vm.cpus || 2} CPU</span>
        </div>
        <div className="flex items-center gap-2 text-nb-text-secondary">
          <HardDrive size={16} />
          <span className="text-sm">{agent.vm.memory || '4G'}</span>
        </div>
      </div>

      {/* 操作按钮 */}
      <div className="flex items-center gap-3">
        {isRunning ? (
          <>
            <button
              onClick={(e) => { e.stopPropagation(); onEnter(); }}
              className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors font-medium"
            >
              <Monitor size={18} />
              Enter Workspace
            </button>
            <button
              onClick={(e) => { e.stopPropagation(); onStop(); }}
              className="px-4 py-2.5 bg-nb-surface-hover hover:bg-red-500/20 text-nb-text-secondary hover:text-red-400 rounded-lg transition-colors border border-nb-border"
              title="Stop VM"
            >
              <Square size={18} />
            </button>
          </>
        ) : (
          <>
            <button
              onClick={(e) => { e.stopPropagation(); onStart(); }}
              disabled={isStarting}
              className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 bg-green-600 hover:bg-green-700 disabled:bg-green-600/50 text-white rounded-lg transition-colors font-medium"
            >
              {isStarting ? (
                <>
                  <Loader2 size={18} className="animate-spin" />
                  Starting...
                </>
              ) : (
                <>
                  <Play size={18} />
                  Start VM
                </>
              )}
            </button>
            <button
              onClick={(e) => { e.stopPropagation(); onDelete(); }}
              disabled={isStarting}
              className="px-4 py-2.5 bg-nb-surface-hover hover:bg-red-500/20 text-nb-text-secondary hover:text-red-400 disabled:opacity-50 rounded-lg transition-colors border border-nb-border"
              title="Delete Agent"
            >
              <Trash2 size={18} />
            </button>
          </>
        )}
      </div>

      {/* 创建时间 */}
      <p className="mt-4 text-xs text-nb-text-muted">
        Created: {new Date(agent.created_at).toLocaleDateString()}
      </p>
    </div>
  );
}

interface AgentDashboardProps {
  onEnterWorkspace: (agentId: string) => void;
}

// VM status from Tauri (must match Rust VmStatus struct)
interface VmStatus {
  running: boolean;
  agent_healthy: boolean;
  mcp_healthy: boolean;
  websockify_running: boolean;
  vnc_port: number;
  agent_port: number;
  mcp_host_port: number;
  websocket_port: number;
  vnc_url: string;
  agent_url: string;
  mcp_url: string;
  agent_id: string | null;
}

export function AgentDashboard({ onEnterWorkspace }: AgentDashboardProps) {
  const { agents, currentAgentId, selectAgent, deleteAgent, loadAgents } = useAppStore();
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [loadingAgent, setLoadingAgent] = useState<string | null>(null);
  const [vmStatus, setVmStatus] = useState<VmStatus | null>(null);

  // Poll VM status
  const refreshVmStatus = useCallback(async () => {
    try {
      const status = await invoke<VmStatus>('get_vm_status');
      setVmStatus(status);
    } catch (error) {
      console.error('Failed to get VM status:', error);
    }
  }, []);

  // Poll status periodically
  useEffect(() => {
    refreshVmStatus();
    const interval = setInterval(refreshVmStatus, 3000);
    return () => clearInterval(interval);
  }, [refreshVmStatus]);

  // Derive agent status from VM status
  const getAgentStatus = (agent: AICAgent): AICAgent['status'] => {
    if (!vmStatus) return 'stopped';
    if (loadingAgent === agent.id) return 'starting';
    
    // Check if this agent's VM is running
    if (vmStatus.agent_id === agent.id && vmStatus.running) {
      return 'running';
    }
    
    // VM is running but for a different agent
    if (vmStatus.running && vmStatus.agent_id !== agent.id) {
      return 'stopped';
    }
    
    return 'stopped';
  };

  const handleStartAgent = async (agentId: string) => {
    setLoadingAgent(agentId);
    try {
      // First select this agent
      await selectAgent(agentId);
      
      // Call Tauri to start VM
      console.log('[Dashboard] Starting VM for agent:', agentId);
      await invoke('start_vm', { agentId });
      console.log('[Dashboard] VM started');
      
      // Refresh status
      await refreshVmStatus();
      await loadAgents();
    } catch (error) {
      console.error('Failed to start agent:', error);
      alert(`Failed to start VM: ${error}`);
    } finally {
      setLoadingAgent(null);
    }
  };

  const handleStopAgent = async (_agentId: string) => {
    setLoadingAgent(_agentId);
    try {
      // Call Tauri to stop VM
      console.log('[Dashboard] Stopping VM');
      await invoke('stop_vm');
      console.log('[Dashboard] VM stopped');
      
      // Refresh status
      await refreshVmStatus();
      await loadAgents();
    } catch (error) {
      console.error('Failed to stop agent:', error);
      alert(`Failed to stop VM: ${error}`);
    } finally {
      setLoadingAgent(null);
    }
  };

  const handleDeleteAgent = async (agentId: string) => {
    if (!confirm('Are you sure you want to delete this agent? This action cannot be undone.')) {
      return;
    }
    try {
      await deleteAgent(agentId);
    } catch (error) {
      console.error('Failed to delete agent:', error);
    }
  };

  const handleEnterWorkspace = (agentId: string) => {
    selectAgent(agentId);
    onEnterWorkspace(agentId);
  };

  const handleCreateComplete = async () => {
    setCreateModalOpen(false);
    await loadAgents();
  };

  return (
    <div className="h-screen flex flex-col bg-nb-bg">
      {/* Header */}
      <header className="h-14 border-b border-nb-border flex items-center justify-between px-6">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
            <span className="text-white font-bold text-sm">N</span>
          </div>
          <h1 className="text-lg font-semibold text-nb-text">NovAIC</h1>
        </div>
        <button
          onClick={() => setCreateModalOpen(true)}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors font-medium"
        >
          <Plus size={18} />
          New Agent
        </button>
      </header>

      {/* Main Content */}
      <main className="flex-1 overflow-auto p-6">
        <div className="max-w-6xl mx-auto">
          {/* Title */}
          <div className="mb-8">
            <h2 className="text-2xl font-bold text-nb-text mb-2">Your Agents</h2>
            <p className="text-nb-text-secondary">
              Manage your AI agents and their virtual environments
            </p>
          </div>

          {/* Agent Grid */}
          {agents.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-20">
              <div className="w-20 h-20 rounded-full bg-nb-surface flex items-center justify-center mb-6">
                <Monitor size={40} className="text-nb-text-muted" />
              </div>
              <h3 className="text-xl font-semibold text-nb-text mb-2">No agents yet</h3>
              <p className="text-nb-text-secondary mb-6">Create your first AI agent to get started</p>
              <button
                onClick={() => setCreateModalOpen(true)}
                className="flex items-center gap-2 px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors font-medium"
              >
                <Plus size={20} />
                Create Your First Agent
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {agents.map((agent) => (
                <AgentCard
                  key={agent.id}
                  agent={agent}
                  status={getAgentStatus(agent)}
                  isSelected={agent.id === currentAgentId}
                  onSelect={() => selectAgent(agent.id)}
                  onStart={() => handleStartAgent(agent.id)}
                  onStop={() => handleStopAgent(agent.id)}
                  onDelete={() => handleDeleteAgent(agent.id)}
                  onEnter={() => handleEnterWorkspace(agent.id)}
                />
              ))}
            </div>
          )}
        </div>
      </main>

      {/* Footer */}
      <footer className="h-8 border-t border-nb-border flex items-center justify-center text-xs text-nb-text-muted">
        NovAIC v0.3.0 • {agents.length} Agent{agents.length !== 1 ? 's' : ''}
      </footer>

      {/* Create Agent Modal */}
      <CreateAgentModal 
        isOpen={createModalOpen} 
        onClose={handleCreateComplete}
      />
    </div>
  );
}
