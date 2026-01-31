import { useState, useCallback, useEffect } from 'react';
import { vmService, VmStatus } from '../services/vm';
import { useAppStore } from '../store';

interface UseVmReturn {
  status: VmStatus | null;
  isLoading: boolean;
  error: string | null;
  startVm: () => Promise<void>;
  stopVm: () => Promise<void>;
  restartVm: () => Promise<void>;
  refreshStatus: () => Promise<void>;
}

// Default status with Agent 0 ports (BASE_PORT=20000)
const DEFAULT_STATUS: VmStatus = {
  agent_id: '',
  running: false,
  agent_healthy: false,
  mcp_healthy: false,
  websockify_running: false,
  ports: {
    vm: 20000,
    session: 20001,
    local: 20002,
    memory: 20003,
    chat: 20004,
    qemudebug: 20005,
    vnc: 20006,
    websocket: 20007,
    ssh: 20008,
  },
  vnc_url: 'ws://localhost:20007/websockify',
  mcp_url: 'http://127.0.0.1:20000/mcp',
};

export function useVm(): UseVmReturn {
  const [status, setStatus] = useState<VmStatus | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const currentAgentId = useAppStore((state) => state.currentAgentId);
  const agents = useAppStore((state) => state.agents);
  
  // 获取当前 agent 的信息
  const currentAgent = agents.find(a => a.id === currentAgentId);

  // 刷新状态
  const refreshStatus = useCallback(async () => {
    if (!currentAgentId) {
      setStatus(DEFAULT_STATUS);
      return;
    }
    
    try {
      const newStatus = await vmService.getStatus(currentAgentId);
      setStatus(newStatus || DEFAULT_STATUS);
      setError(null);
    } catch (err) {
      console.warn('[useVm] Failed to get status:', err);
      // 不设置错误，使用默认状态
      setStatus(DEFAULT_STATUS);
    }
  }, [currentAgentId]);

  // 启动 VM
  const startVm = useCallback(async () => {
    if (!currentAgentId || !currentAgent) {
      setError('No agent selected');
      return;
    }
    
    setIsLoading(true);
    setError(null);
    
    const agentIndex = currentAgent.vm.agent_index ?? 0;
    console.log('[useVm] startVm called, currentAgentId:', currentAgentId, 'agentIndex:', agentIndex);
    
    try {
      console.log('[useVm] Calling vmService.start with agentId:', currentAgentId);
      await vmService.start(currentAgentId, agentIndex);
      // 等待 VM 就绪
      await vmService.waitForReady(currentAgentId, 15, 2000);
      await refreshStatus();
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to start VM';
      console.error('[useVm] startVm error:', errorMessage);
      setError(errorMessage);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [refreshStatus, currentAgentId, currentAgent]);

  // 停止 VM
  const stopVm = useCallback(async () => {
    if (!currentAgentId) {
      setError('No agent selected');
      return;
    }
    
    setIsLoading(true);
    setError(null);
    
    try {
      await vmService.stop(currentAgentId);
      await refreshStatus();
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to stop VM';
      setError(errorMessage);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [refreshStatus, currentAgentId]);

  // 重启 VM
  const restartVm = useCallback(async () => {
    if (!currentAgentId || !currentAgent) {
      setError('No agent selected');
      return;
    }
    
    setIsLoading(true);
    setError(null);
    
    const agentIndex = currentAgent.vm.agent_index ?? 0;
    
    try {
      await vmService.restart(currentAgentId, agentIndex);
      // 等待 VM 就绪
      await vmService.waitForReady(currentAgentId, 15, 2000);
      await refreshStatus();
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to restart VM';
      setError(errorMessage);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [refreshStatus, currentAgentId, currentAgent]);

  // 初始化时获取状态
  useEffect(() => {
    refreshStatus();
  }, [refreshStatus]);

  // 定期轮询状态
  useEffect(() => {
    const interval = setInterval(() => {
      refreshStatus();
    }, 10000); // 每 10 秒刷新一次

    return () => clearInterval(interval);
  }, [refreshStatus]);

  return {
    status,
    isLoading,
    error,
    startVm,
    stopVm,
    restartVm,
    refreshStatus,
  };
}
