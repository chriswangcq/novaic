/**
 * VNC 连接管理 Hook
 * 
 * 职责：
 * 1. 管理 VNC 连接状态
 * 2. 处理轮询逻辑
 * 3. 处理初始化状态检查
 * 
 * 设计理念：
 * - 所有副作用封装在 hook 内部
 * - 对外暴露稳定的状态和方法
 * - 避免频繁的重新创建
 */

import { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import { vmService } from '../../services/vm';
import { WS_CONFIG, POLL_CONFIG, API_CONFIG } from '../../config';

export type VncStatus = 'unknown' | 'stopped' | 'starting' | 'running' | 'error' | 'initializing';

interface SetupStatus {
  phase: string;
  progress: number;
  message: string;
  steps: {
    vm_created?: boolean;
    vm_booted?: boolean;
    ssh_ready?: boolean;
    cloud_init?: boolean;
    vmuse_deployed?: boolean;
    cloud_init_detail?: string;
  };
  error: string | null;
}

interface VNCConnectionState {
  status: VncStatus;
  wsReady: boolean;
  errorMsg: string;
  setupStatus: SetupStatus | null;
}

interface VNCConnectionActions {
  startVm: () => Promise<void>;
  refreshStatus: () => Promise<void>;
  reset: () => void;
}

export function useVNCConnection(
  agentId: string | null,
  onConnected: (connected: boolean) => void
): [VNCConnectionState, VNCConnectionActions, string | null] {
  
  // 状态
  const [status, setStatus] = useState<VncStatus>('unknown');
  const [wsReady, setWsReady] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const [setupStatus, setSetupStatus] = useState<SetupStatus | null>(null);
  
  // Refs - 避免闭包陷阱
  const wsUrlRef = useRef<string | null>(null);
  const pollIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const setupPollIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const isConnectingRef = useRef(false);
  
  // 检查初始化状态
  const checkSetupStatus = useCallback(async (): Promise<'initializing' | 'complete' | 'error' | null> => {
    if (!agentId) return null;
    
    try {
      const data = await vmService.getSetupStatus(agentId);
      if (!data) return null;
      
      if (data.phase === 'complete') {
        setSetupStatus(null);
        return 'complete';
      } else if (data.phase === 'error') {
        setSetupStatus(data);
        setStatus('error');
        setErrorMsg(data.error || 'Initialization failed');
        return 'error';
      } else {
        // 只在真正变化时更新
        setSetupStatus(prev => {
          if (prev && 
              prev.phase === data.phase && 
              prev.progress === data.progress &&
              prev.message === data.message) {
            return prev;
          }
          return data;
        });
        setStatus('initializing');
        return 'initializing';
      }
    } catch (e) {
      console.error('[VNC Connection] Check setup status failed:', e);
      return null;
    }
  }, [agentId]);
  
  // 检查 WebSocket 连接（只测试可用性，不改变状态）
  const checkWebSocket = useCallback(async (): Promise<boolean> => {
    if (!agentId || isConnectingRef.current) return false;
    
    try {
      isConnectingRef.current = true;
      const wsUrl = wsUrlRef.current || (await vmService.getVncUrl(agentId));
      wsUrlRef.current = wsUrl;
      
      const ws = new WebSocket(wsUrl);
      await new Promise<void>((resolve, reject) => {
        const timeout = setTimeout(() => {
          ws.close();
          reject(new Error('timeout'));
        }, WS_CONFIG.CONNECTION_TIMEOUT);
        
        ws.onopen = () => {
          clearTimeout(timeout);
          ws.close();
          resolve();
        };
        ws.onerror = () => {
          clearTimeout(timeout);
          reject(new Error('ws error'));
        };
      });
      
      console.log('[VNC Connection] WebSocket available, preparing for RFB');
      // 只设置 wsReady，让 RFB 连接成功后再设置 running
      setWsReady(true);
      setStatus('running');  // 设置为 running，让 VNCView 开始 RFB 连接
      return true;
    } catch (e) {
      console.log('[VNC Connection] WebSocket not available');
      setWsReady(false);
      setStatus(prev => prev === 'starting' ? 'starting' : 'unknown');
      return false;
    } finally {
      isConnectingRef.current = false;
    }
  }, [agentId]);
  
  // 启动 VM
  const startVm = useCallback(async () => {
    if (!agentId) return;
    
    setStatus('starting');
    setErrorMsg('');
    
    try {
      await vmService.start(agentId);
      console.log('[VNC Connection] VM start command sent, waiting for connection...');
      
      // 启动后持续检查连接（最多 30 秒）
      for (let i = 0; i < 30; i++) {
        await new Promise(r => setTimeout(r, 1000)); // 每秒检查一次
        const connected = await checkWebSocket();
        if (connected) {
          console.log(`[VNC Connection] Connected after ${i + 1} seconds`);
          return;
        }
      }
      
      // 30 秒后还没连上，设置错误
      console.log('[VNC Connection] Timeout waiting for connection');
      setStatus('error');
      setErrorMsg('VM started but connection timeout. Please refresh.');
    } catch (e: any) {
      const errorMsg = typeof e === 'string' ? e : e?.message || '';
      if (!errorMsg.includes('already running')) {
        setStatus('error');
        setErrorMsg(e.message || 'Failed to start VM');
      } else {
        // 已经在运行，检查连接
        console.log('[VNC Connection] VM already running, checking connection...');
        await checkWebSocket();
      }
    }
  }, [agentId, checkWebSocket]);
  
  // 刷新状态
  const refreshStatus = useCallback(async () => {
    if (!agentId) return;
    
    try {
      const res = await fetch(`${API_CONFIG.GATEWAY_URL}/api/vnc/status?agent_id=${agentId}`, {
        signal: AbortSignal.timeout(API_CONFIG.ABORT_TIMEOUT),
      });
      const data = await res.json();
      
      if (data.ready || data.running) {
        await checkWebSocket();
      } else {
        setStatus('stopped');
        setWsReady(false);
        onConnected(false);
      }
    } catch (e) {
      setStatus('unknown');
      setWsReady(false);
      onConnected(false);
    }
  }, [agentId, checkWebSocket, onConnected]);
  
  // 重置连接
  const reset = useCallback(() => {
    setWsReady(false);
    setStatus('unknown');
    setErrorMsg('');
    setSetupStatus(null);
    wsUrlRef.current = null;
    onConnected(false);
  }, [onConnected]);
  
  // 主初始化逻辑
  useEffect(() => {
    if (!agentId) {
      reset();
      return;
    }
    
    let mounted = true;
    
    const init = async () => {
      console.log('[VNC Connection] Initializing for agent:', agentId);
      
      // 1. 检查是否正在初始化
      const initStatus = await checkSetupStatus();
      if (!mounted) return;
      
      if (initStatus === 'initializing') {
        // 启动初始化状态轮询
        setupPollIntervalRef.current = setInterval(async () => {
          const status = await checkSetupStatus();
          if (status === 'complete') {
            if (setupPollIntervalRef.current) {
              clearInterval(setupPollIntervalRef.current);
              setupPollIntervalRef.current = null;
            }
            // 初始化完成，检查 VM 状态
            await refreshStatus();
          } else if (status === 'error') {
            if (setupPollIntervalRef.current) {
              clearInterval(setupPollIntervalRef.current);
              setupPollIntervalRef.current = null;
            }
          }
        }, 3000);
        return;
      } else if (initStatus === 'error') {
        return;
      }
      
      // 2. 先检查 VM 是否真的在运行（而不是直接测端口）
      await refreshStatus();
      if (!mounted) return;
      
      // 3. 启动轮询（只在未连接时）
      pollIntervalRef.current = setInterval(async () => {
        if (wsReady) return; // 已连接时跳过
        await checkWebSocket();
      }, POLL_CONFIG.VNC_POLL_INTERVAL);
    };
    
    init();
    
    return () => {
      mounted = false;
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
        pollIntervalRef.current = null;
      }
      if (setupPollIntervalRef.current) {
        clearInterval(setupPollIntervalRef.current);
        setupPollIntervalRef.current = null;
      }
    };
  }, [agentId, checkSetupStatus, checkWebSocket, refreshStatus, reset, wsReady]);
  
  // 使用 useMemo 缓存对象，避免每次返回新引用
  const state = useMemo(
    () => ({ status, wsReady, errorMsg, setupStatus }),
    [status, wsReady, errorMsg, setupStatus]
  );
  
  const actions = useMemo(
    () => ({ startVm, refreshStatus, reset }),
    [startVm, refreshStatus, reset]
  );
  
  return [state, actions, wsUrlRef.current];
}
