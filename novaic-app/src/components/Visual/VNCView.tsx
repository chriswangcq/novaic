import { useEffect, useState, useCallback, useRef } from 'react';
import { useAppStore } from '../../store';
import { Monitor, RefreshCw, Play, Loader2, Lock, Unlock, Copy, Check } from 'lucide-react';
import { vmService } from '../../services/vm';
import RFB from 'novnc-rfb';
import { LayoutToggle } from '../Layout/LayoutToggle';

// 配置 - 默认使用 Agent 0 的端口 (BASE_PORT=20000)
// 实际端口应从 VM status 获取
const CONFIG = {
  gatewayPort: 19999,  // Gateway API 端口 (固定)
  vncPort: 20006,     // VNC 端口 (Agent 0: 20006)
  wsPort: 20007,      // websockify 端口 (Agent 0: 20007)
};

type VncStatus = 'unknown' | 'stopped' | 'starting' | 'running' | 'error';

// 启动进度步骤
interface StartupProgress {
  step: number;  // 0-4
  stepName: string;
  progress: number;  // 0-100
  message: string;
}

const STARTUP_STEPS = [
  { name: '启动虚拟机', weight: 30 },
  { name: '等待 Agent 服务', weight: 30 },
  { name: '启动 VNC', weight: 20 },
  { name: '连接 WebSockify', weight: 20 },
];

interface VNCViewProps {
  isThumbnail?: boolean;
}

export function VNCView({ isThumbnail = false }: VNCViewProps) {
  const { setVncConnected, vncLocked, setVncLocked, currentAgentId, agents } = useAppStore();
  
  // 获取当前 agent 的信息
  const currentAgent = agents.find(a => a.id === currentAgentId);
  const [status, setStatus] = useState<VncStatus>('unknown');
  const [errorMsg, setErrorMsg] = useState('');
  const [wsReady, setWsReady] = useState(false);
  const [copied, setCopied] = useState(false);
  const [startupProgress, setStartupProgress] = useState<StartupProgress | null>(null);
  const rfbRef = useRef<RFB | null>(null);
  const rfbContainerRef = useRef<HTMLDivElement>(null);
  const wsUrlRef = useRef<string | null>(null);

  // 复制 MCP Server 配置到剪贴板
  const copyMcpConfig = useCallback(async () => {
    if (!currentAgentId) {
      console.error('No agent selected');
      return;
    }
    const mcpConfig = {
      "mcpServers": {
        "novaic-gateway": {
          "url": `http://127.0.0.1:${CONFIG.gatewayPort}/agents/${currentAgentId}/mcp`
        }
      }
    };
    try {
      await navigator.clipboard.writeText(JSON.stringify(mcpConfig, null, 2));
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (e) {
      console.error('Failed to copy MCP config:', e);
    }
  }, [currentAgentId]);

  // 检查 websockify 是否可用 (必须在 checkVncStatus 之前声明)
  const checkWebsockify = useCallback(async () => {
    const timestamp = new Date().toLocaleTimeString();
    console.log(`[VNC checkWebsockify ${timestamp}] Checking WebSocket connection...`);
    try {
      if (!currentAgentId) {
        console.log(`[VNC checkWebsockify ${timestamp}] No agent selected`);
        setWsReady(false);
        return;
      }
      const wsUrl = wsUrlRef.current || (await vmService.getVncUrl(currentAgentId));
      wsUrlRef.current = wsUrl;
      const ws = new WebSocket(wsUrl);
      await new Promise<void>((resolve, reject) => {
        const timeout = setTimeout(() => {
          ws.close();
          reject(new Error('timeout'));
        }, 2000);

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
      console.log(`[VNC checkWebsockify ${timestamp}] SUCCESS - WebSocket connected!`);
      setWsReady(true);
      setVncConnected(true);
    } catch (e) {
      console.log(`[VNC checkWebsockify ${timestamp}] FAILED - ${e}`);
      setWsReady(false);
      setVncConnected(false);
    }
  }, [setVncConnected, currentAgentId]);

  // 检查 Agent 的 VNC 状态 (使用新的 ready 字段)
  const checkVncStatus = useCallback(async () => {
    // 需要有选中的 agent 才能检查状态
    if (!currentAgentId) {
      console.log('[VNC checkVncStatus] No agent selected');
      setStatus('unknown');
      setWsReady(false);
      setVncConnected(false);
      return;
    }
    
    try {
      const res = await fetch(`http://localhost:${CONFIG.gatewayPort}/api/vnc/status?agent_id=${currentAgentId}`, {
        signal: AbortSignal.timeout(3000),
      });
      const data = await res.json();
      
      if (data.ready) {
        // VNC + websockify 都就绪
        setStatus('running');
        checkWebsockify();
      } else if (data.running) {
        // VNC 运行但 websockify 未就绪
        setStatus('running');
        setWsReady(false);
        // 尝试检查 websockify
        checkWebsockify();
      } else {
        setStatus('stopped');
        setWsReady(false);
        setVncConnected(false);
      }
    } catch (e) {
      // Agent 不可用
      setStatus('unknown');
      setWsReady(false);
      setVncConnected(false);
    }
  }, [setVncConnected, currentAgentId, checkWebsockify]);

  // 更新启动进度的辅助函数
  const updateProgress = useCallback((step: number, subProgress: number, message: string) => {
    const baseProgress = STARTUP_STEPS.slice(0, step).reduce((sum, s) => sum + s.weight, 0);
    const stepWeight = STARTUP_STEPS[step]?.weight || 0;
    const totalProgress = baseProgress + (stepWeight * subProgress / 100);
    
    setStartupProgress({
      step,
      stepName: STARTUP_STEPS[step]?.name || '',
      progress: Math.min(100, Math.round(totalProgress)),
      message,
    });
  }, []);

  // 启动 VNC (先启动 QEMU，再启动 VNC 服务)
  const startVnc = useCallback(async () => {
    const startTime = Date.now();
    const log = (msg: string) => console.log(`[VNC startVnc ${((Date.now() - startTime) / 1000).toFixed(1)}s] ${msg}`);
    
    log('=== startVnc() BEGIN ===');
    setStatus('starting');
    setErrorMsg('');
    setStartupProgress({ step: 0, stepName: STARTUP_STEPS[0].name, progress: 0, message: '准备启动...' });
    
    try {
      // Step 1: 先启动 QEMU VM
      if (!currentAgentId || !currentAgent) {
        throw new Error('No agent selected');
      }
      const agentIndex = currentAgent.vm.agent_index ?? 0;
      log(`Step 1: Starting QEMU VM... (agentId: ${currentAgentId}, agentIndex: ${agentIndex})`);
      updateProgress(0, 0, '正在启动虚拟机...');
      
      try {
        await vmService.start(currentAgentId, agentIndex);
        log('QEMU VM started');
        updateProgress(0, 100, '虚拟机已启动');
      } catch (vmError: any) {
        // Tauri 返回的错误可能是字符串或 Error 对象
        const errorMsg = typeof vmError === 'string' ? vmError : vmError?.message || '';
        // 如果 VM 已经在运行，继续
        if (!errorMsg.includes('already running')) {
          throw vmError;
        }
        log('VM already running, continuing...');
        updateProgress(0, 100, '虚拟机已在运行');
      }
      
      // Step 2: 等待 Agent 服务就绪 (VM 启动需要时间)
      log('Step 2: Waiting for Agent service...');
      updateProgress(1, 0, '等待 Agent 服务启动...');
      let agentReady = false;
      for (let i = 0; i < 30; i++) {
        try {
          const healthRes = await fetch(`http://localhost:${CONFIG.gatewayPort}/api/health`, {
            method: 'GET',
            signal: AbortSignal.timeout(3000),
          });
          if (healthRes.ok) {
            agentReady = true;
            log(`Agent ready after ${i + 1} attempts`);
            updateProgress(1, 100, 'Agent 服务已就绪');
            break;
          }
        } catch {
          // Agent 还没准备好
        }
        updateProgress(1, Math.min(90, (i + 1) * 3), `等待 Agent 服务... (${i + 1}/30)`);
        if (i > 0 && i % 5 === 0) {
          log(`Still waiting for Agent... attempt ${i + 1}/30`);
        }
        await new Promise(r => setTimeout(r, 2000));
      }
      
      if (!agentReady) {
        throw new Error('Agent service not responding after VM start');
      }
      
      // Step 3: 调用 Agent 启动 VNC
      log('Step 3: Calling /api/vnc/start...');
      updateProgress(2, 0, '正在启动 VNC 服务...');
      const res = await fetch(`http://localhost:${CONFIG.gatewayPort}/api/vnc/start?agent_id=${currentAgentId}`, {
        method: 'POST',
      });
      const data = await res.json();
      log(`/api/vnc/start response: ${JSON.stringify(data)}`);
      
      if (data.status === 'started' || data.status === 'running') {
        updateProgress(2, 100, 'VNC 服务已启动');
        setStatus('running');
        
        // 快速轮询等待 websockify 就绪 (每 500ms 检查一次，最多 10 秒)
        log('Step 4: Fast polling websockify...');
        updateProgress(3, 0, '正在连接 WebSockify...');
        let wsConnected = false;
        for (let i = 0; i < 20; i++) {
          try {
            const wsUrl = wsUrlRef.current || (await vmService.getVncUrl(currentAgentId));
            wsUrlRef.current = wsUrl;
            const ws = new WebSocket(wsUrl);
            await new Promise<void>((resolve, reject) => {
              const timeout = setTimeout(() => {
                ws.close();
                reject(new Error('timeout'));
              }, 1000);
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
            wsConnected = true;
            log(`WebSocket connected after ${i + 1} attempts!`);
            updateProgress(3, 100, '连接成功！');
            break;
          } catch {
            // 继续等待
          }
          updateProgress(3, Math.min(90, (i + 1) * 5), `连接 WebSockify... (${i + 1}/20)`);
          await new Promise(r => setTimeout(r, 500));
        }
        
        if (wsConnected) {
          log('=== startVnc() SUCCESS ===');
          setWsReady(true);
          setVncConnected(true);
          setStartupProgress(null);  // 清除进度，显示正常界面
        } else {
          log('WebSocket not ready after 10s, falling back to background check');
          checkWebsockify();
        }
      } else {
        setStatus('error');
        setErrorMsg(data.error || 'Failed to start VNC');
        setStartupProgress(null);
        log(`=== startVnc() FAILED: ${data.error} ===`);
      }
    } catch (e: any) {
      log(`=== startVnc() ERROR: ${e.message} ===`);
      setStatus('error');
      setErrorMsg(e.message || 'Failed to start VM or VNC');
      setStartupProgress(null);
    }
  }, [checkWebsockify, currentAgentId, currentAgent, setVncConnected, updateProgress]);

  // 当 agent 切换时，重置 VNC 连接
  useEffect(() => {
    console.log('[VNC] Agent changed to:', currentAgentId);
    
    // 清除缓存的 WebSocket URL，强制重新获取
    wsUrlRef.current = null;
    
    // 断开现有 RFB 连接
    if (rfbRef.current) {
      console.log('[VNC] Disconnecting existing RFB connection');
      rfbRef.current.disconnect();
      rfbRef.current = null;
    }
    
    // 重置状态，触发重新连接
    setWsReady(false);
    setVncConnected(false);
    setStatus('unknown');
  }, [currentAgentId, setVncConnected]);

  // 初始化：优先直接连接 websockify，不依赖 Agent
  useEffect(() => {
    let intervalId: ReturnType<typeof setInterval> | null = null;
    const startTime = Date.now();
    const log = (msg: string) => console.log(`[VNC ${((Date.now() - startTime) / 1000).toFixed(1)}s] ${msg}`);
    
    const init = async () => {
      log('init() called');
      
      // 需要有选中的 agent 才能连接
      if (!currentAgentId) {
        log('No agent selected, waiting...');
        setStatus('unknown');
        return;
      }
      
      // 策略 1: 直接尝试连接当前 agent 的 websockify
      log(`Step 1: Trying direct websockify connection for agent ${currentAgentId}...`);
      try {
        // 获取当前 agent 的 VNC URL
        const wsUrl = await vmService.getVncUrl(currentAgentId);
        wsUrlRef.current = wsUrl;
        log(`Got VNC URL: ${wsUrl}`);
        
        const ws = new WebSocket(wsUrl);
        await new Promise<void>((resolve, reject) => {
          const timeout = setTimeout(() => {
            ws.close();
            reject(new Error('timeout'));
          }, 2000);
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
        // WebSocket 直接可用！
        log('Direct websockify connection SUCCESS!');
        setStatus('running');
        setWsReady(true);
        setVncConnected(true);
        return; // 快速返回，不需要进一步操作
      } catch (e) {
        log(`Direct websockify failed: ${e}, falling back to Agent check...`);
      }
      
      // 策略 2: 如果直接连接失败，尝试通过 Agent API
      try {
        log('Step 2: Checking Agent VNC status...');
        const res = await fetch(`http://localhost:${CONFIG.gatewayPort}/api/vnc/status?agent_id=${currentAgentId}`, {
          signal: AbortSignal.timeout(3000),
        });
        const data = await res.json();
        log(`VNC status: running=${data.running}, websockify=${data.websockify}, ready=${data.ready}`);
        
        if (data.ready) {
          log('Already ready via Agent, connecting...');
          setStatus('running');
          setWsReady(true);
          setVncConnected(true);
        } else if (data.running) {
          log('VNC running but websockify not ready, checking...');
          setStatus('running');
          checkWebsockify();
        } else {
          log('VNC not running, calling startVnc()...');
          startVnc();
        }
      } catch (e) {
        log(`Agent not available: ${e}`);
        // Agent 不可用，可能 VM 正在启动中，进入轮询等待
        setStatus('starting');
      }
    };
    
    init();
    
    // 定期检查：只在未连接时尝试重连，已连接时不轮询（RFB 会自己处理断开）
    const startPolling = () => {
      const pollFn = async () => {
        // 如果已连接或没有选中 agent，不做任何检测
        if (wsReady || !currentAgentId) {
          return;
        }
        // 未连接时尝试获取当前 agent 的 websockify URL 并连接
        try {
          const wsUrl = wsUrlRef.current || (await vmService.getVncUrl(currentAgentId));
          wsUrlRef.current = wsUrl;
          const ws = new WebSocket(wsUrl);
          await new Promise<void>((resolve, reject) => {
            const timeout = setTimeout(() => { ws.close(); reject(new Error('timeout')); }, 1500);
            ws.onopen = () => { clearTimeout(timeout); ws.close(); resolve(); };
            ws.onerror = () => { clearTimeout(timeout); reject(new Error('ws error')); };
          });
          console.log(`[VNC poll] Websockify connected for agent ${currentAgentId}!`);
          setStatus('running');
          setWsReady(true);
          setVncConnected(true);
        } catch {
          // 继续等待
        }
      };
      // 未连接时 5 秒检测一次
      intervalId = setInterval(pollFn, 5000);
    };
    
    startPolling();
    
    return () => {
      if (intervalId) clearInterval(intervalId);
    };
  }, [checkVncStatus, checkWebsockify, startVnc, setVncConnected, wsReady, currentAgentId]);

  // Connect/disconnect RFB inside the app
  useEffect(() => {
    if (!(status === 'running' && wsReady)) return;
    if (!rfbContainerRef.current) return;

    let disposed = false;

    const connect = async () => {
      try {
        if (!currentAgentId) {
          console.log('[VNC] No agent selected, skipping connection');
          return;
        }
        const wsUrl = wsUrlRef.current || (await vmService.getVncUrl(currentAgentId));
        wsUrlRef.current = wsUrl;

        // Clean up any existing connection
        if (rfbRef.current) {
          rfbRef.current.disconnect();
          rfbRef.current = null;
        }

        // Create a new RFB connection
        const rfb = new RFB(rfbContainerRef.current!, wsUrl, {
          shared: true,
          credentials: {},
        });

        rfb.scaleViewport = true;
        rfb.clipViewport = true;
        rfb.resizeSession = false;
        rfb.focusOnClick = true;
        rfb.viewOnly = vncLocked;

        rfb.addEventListener('connect', () => {
          if (disposed) return;
          console.log('[VNC] RFB connected');
          setVncConnected(true);
        });

        rfb.addEventListener('disconnect', (e: any) => {
          if (disposed) return;
          const clean = Boolean(e?.detail?.clean);
          console.log(`[VNC] RFB disconnected (clean: ${clean})`);
          if (!clean) {
            setVncConnected(false);
            setWsReady(false);
            setErrorMsg('VNC disconnected');
          }
        });

        rfb.addEventListener('securityfailure', (e: any) => {
          if (disposed) return;
          setErrorMsg(e?.detail?.reason || 'VNC security failure');
        });

        rfbRef.current = rfb;
      } catch (e: any) {
        if (disposed) return;
        setErrorMsg(e?.message || 'Failed to connect VNC');
      }
    };

    connect();

    return () => {
      disposed = true;
      if (rfbRef.current) {
        try {
          rfbRef.current.disconnect();
        } catch {
          // ignore
        }
        rfbRef.current = null;
      }
    };
  }, [status, wsReady, setVncConnected, vncLocked]);

  // Update viewOnly when vncLocked changes
  useEffect(() => {
    if (rfbRef.current) {
      rfbRef.current.viewOnly = vncLocked;
    }
  }, [vncLocked]);

  const getStatusDisplay = () => {
    switch (status) {
      case 'running':
        return wsReady ? { text: 'Connected', color: 'bg-nb-success' } : { text: 'VNC Ready', color: 'bg-nb-warning' };
      case 'starting':
        return { text: 'Starting...', color: 'bg-nb-warning animate-pulse' };
      case 'stopped':
        return { text: 'Stopped', color: 'bg-nb-error' };
      case 'error':
        return { text: 'Error', color: 'bg-nb-error' };
      default:
        return { text: 'Unknown', color: 'bg-gray-500' };
    }
  };

  const statusDisplay = getStatusDisplay();

  // Thumbnail mode: simplified view without toolbar
  if (isThumbnail) {
    return (
      <div className="h-full w-full relative overflow-hidden bg-black">
        {status === 'running' && wsReady ? (
          <div ref={rfbContainerRef} className="absolute inset-0 pointer-events-none" />
        ) : (
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="text-center">
              <Monitor size={24} className="mx-auto mb-1 text-nb-text-muted/50" />
              <span className="text-[10px] text-nb-text-muted/50">{statusDisplay.text}</span>
            </div>
          </div>
        )}
        {/* Status indicator */}
        <div className="absolute top-2 left-2">
          <span className={`w-2 h-2 rounded-full ${statusDisplay.color} block`} />
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col bg-nb-bg">
      {/* Toolbar - simplified */}
      <div className="h-10 px-3 flex items-center gap-2 bg-nb-surface border-b border-nb-border shrink-0">
        {/* Layout toggle - left side */}
        <LayoutToggle />

        <div className="flex-1" />

        {/* Main actions - right side */}
        {status === 'stopped' || status === 'unknown' || status === 'error' ? (
          <button
            onClick={startVnc}
            className="flex items-center gap-1.5 px-2.5 py-1 bg-nb-success hover:bg-nb-success/80 text-white rounded text-[11px] font-medium transition-colors"
            title="Start VM"
          >
            <Play size={12} />
            <span>Start</span>
          </button>
        ) : status === 'running' ? (
          <>
            {/* Lock toggle button */}
            <button
              onClick={() => setVncLocked(!vncLocked)}
              className={`p-1.5 rounded transition-colors ${
                vncLocked 
                  ? 'bg-amber-500/20 text-amber-400' 
                  : 'hover:bg-white/[0.06] text-nb-text-muted'
              }`}
              title={vncLocked ? 'Unlock (enable interaction)' : 'Lock (view-only mode)'}
            >
              {vncLocked ? <Lock size={14} /> : <Unlock size={14} />}
            </button>

            {/* Refresh button */}
            <button
              onClick={checkVncStatus}
              className="p-1.5 hover:bg-white/[0.06] rounded transition-colors"
              title="Refresh status"
            >
              <RefreshCw size={14} className="text-nb-text-muted" />
            </button>
          </>
        ) : null}

        {/* Copy MCP Config */}
        <button
          onClick={copyMcpConfig}
          disabled={!currentAgentId}
          className={`p-1.5 rounded transition-colors ${
            copied 
              ? 'bg-nb-success/20 text-nb-success' 
              : !currentAgentId
                ? 'text-nb-text-muted/50 cursor-not-allowed'
                : 'hover:bg-white/[0.06] text-nb-text-muted'
          }`}
          title={copied ? 'Copied!' : !currentAgentId ? 'No agent selected' : 'Copy Gateway MCP Server config'}
        >
          {copied ? <Check size={14} /> : <Copy size={14} />}
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 relative overflow-hidden bg-black">
        {status === 'running' && wsReady ? (
          // VNC 已连接 - 直接渲染 noVNC canvas
          <div ref={rfbContainerRef} className="absolute inset-0" />
        ) : status === 'starting' && startupProgress ? (
          // 启动中 - 显示多步骤进度条
          <div className="absolute inset-0 flex flex-col items-center justify-center text-nb-text-muted p-8">
            {/* 进度环 */}
            <div className="relative w-24 h-24 mb-6">
              <svg className="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
                {/* 背景圆 */}
                <circle
                  cx="50"
                  cy="50"
                  r="42"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="8"
                  className="opacity-20"
                />
                {/* 进度圆 */}
                <circle
                  cx="50"
                  cy="50"
                  r="42"
                  fill="none"
                  stroke="url(#progressGradient)"
                  strokeWidth="8"
                  strokeLinecap="round"
                  strokeDasharray={`${startupProgress.progress * 2.64} 264`}
                  className="transition-all duration-300"
                />
                <defs>
                  <linearGradient id="progressGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                    <stop offset="0%" stopColor="#3b82f6" />
                    <stop offset="100%" stopColor="#8b5cf6" />
                  </linearGradient>
                </defs>
              </svg>
              {/* 百分比 */}
              <div className="absolute inset-0 flex items-center justify-center">
                <span className="text-xl font-semibold text-white">{startupProgress.progress}%</span>
              </div>
            </div>
            
            {/* 当前步骤 */}
            <p className="text-sm font-medium text-white mb-2">{startupProgress.stepName}</p>
            <p className="text-xs text-nb-text-muted mb-6">{startupProgress.message}</p>
            
            {/* 步骤指示器 */}
            <div className="flex items-center gap-2">
              {STARTUP_STEPS.map((step, index) => (
                <div key={step.name} className="flex items-center">
                  <div
                    className={`w-2.5 h-2.5 rounded-full transition-all duration-300 ${
                      index < startupProgress.step
                        ? 'bg-nb-success'
                        : index === startupProgress.step
                        ? 'bg-blue-500 animate-pulse'
                        : 'bg-gray-600'
                    }`}
                  />
                  {index < STARTUP_STEPS.length - 1 && (
                    <div
                      className={`w-6 h-0.5 transition-all duration-300 ${
                        index < startupProgress.step ? 'bg-nb-success' : 'bg-gray-600'
                      }`}
                    />
                  )}
                </div>
              ))}
            </div>
            
            {/* 步骤标签 */}
            <div className="flex gap-1 mt-2 text-[10px] text-nb-text-muted">
              {STARTUP_STEPS.map((step, index) => (
                <span
                  key={step.name}
                  className={`w-12 text-center truncate ${
                    index === startupProgress.step ? 'text-blue-400' : ''
                  }`}
                >
                  {index + 1}
                </span>
              ))}
            </div>
          </div>
        ) : status === 'starting' ? (
          // 启动中 - 简单加载（fallback）
          <div className="absolute inset-0 flex flex-col items-center justify-center text-nb-text-muted">
            <Loader2 size={48} className="mb-4 opacity-50 animate-spin" />
            <p className="text-sm">正在启动 VNC 服务器...</p>
          </div>
        ) : (
          // 未连接
          <div className="absolute inset-0 flex flex-col items-center justify-center text-nb-text-muted">
            <Monitor size={48} className="mb-4 opacity-50" />
            <p className="text-sm mb-2">
              {status === 'error' ? 'VNC 启动失败' : status === 'unknown' ? 'Agent 未连接' : 'VNC 未启动'}
            </p>
            {errorMsg && (
              <p className="text-xs text-nb-error mb-4">{errorMsg}</p>
            )}
            <p className="text-xs opacity-75 max-w-md text-center mb-6">
              {status === 'unknown' 
                ? '请确保 VM 正在运行且 Agent 服务已启动'
                : '点击 Start 按钮启动虚拟机桌面'
              }
            </p>
            
            <button
              onClick={startVnc}
              className="px-4 py-2 bg-nb-accent text-white rounded-md hover:bg-nb-accent/80 transition-colors flex items-center gap-2"
            >
              <Play size={16} />
              <span>启动 VNC</span>
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
