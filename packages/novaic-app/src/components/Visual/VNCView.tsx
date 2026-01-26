import { useEffect, useState, useCallback, useRef } from 'react';
import { useAppStore } from '../../store';
import { Monitor, RefreshCw, ExternalLink, Play, Square, Loader2 } from 'lucide-react';
import { vmService } from '../../services/vm';
import RFB from 'novnc-rfb';

// 配置
const CONFIG = {
  agentPort: 9000,    // Agent API 端口 (宿主机本地)
  vncPort: 5900,      // VNC 端口
  wsPort: 6080,       // websockify 端口
};

type VncStatus = 'unknown' | 'stopped' | 'starting' | 'running' | 'error';

export function VNCView() {
  const { setVncConnected } = useAppStore();
  const [status, setStatus] = useState<VncStatus>('unknown');
  const [errorMsg, setErrorMsg] = useState('');
  const [wsReady, setWsReady] = useState(false);
  const rfbRef = useRef<RFB | null>(null);
  const rfbContainerRef = useRef<HTMLDivElement>(null);
  const wsUrlRef = useRef<string | null>(null);
  // 检查 Agent 的 VNC 状态 (使用新的 ready 字段)
  const checkVncStatus = useCallback(async () => {
    try {
      const res = await fetch(`http://localhost:${CONFIG.agentPort}/api/vnc/status`, {
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
  }, [setVncConnected]);

  // 检查 websockify 是否可用
  const checkWebsockify = useCallback(async () => {
    const timestamp = new Date().toLocaleTimeString();
    console.log(`[VNC checkWebsockify ${timestamp}] Checking WebSocket connection...`);
    try {
      const wsUrl = wsUrlRef.current || (await vmService.getVncUrl());
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
  }, [setVncConnected]);

  // 启动 VNC (先启动 QEMU，再启动 VNC 服务)
  const startVnc = useCallback(async () => {
    const startTime = Date.now();
    const log = (msg: string) => console.log(`[VNC startVnc ${((Date.now() - startTime) / 1000).toFixed(1)}s] ${msg}`);
    
    log('=== startVnc() BEGIN ===');
    setStatus('starting');
    setErrorMsg('');
    
    try {
      // Step 1: 先启动 QEMU VM
      log('Step 1: Starting QEMU VM...');
      try {
        await vmService.start();
        log('QEMU VM started');
      } catch (vmError: any) {
        // Tauri 返回的错误可能是字符串或 Error 对象
        const errorMsg = typeof vmError === 'string' ? vmError : vmError?.message || '';
        // 如果 VM 已经在运行，继续
        if (!errorMsg.includes('already running')) {
          throw vmError;
        }
        log('VM already running, continuing...');
      }
      
      // Step 2: 等待 Agent 服务就绪 (VM 启动需要时间)
      log('Step 2: Waiting for Agent service...');
      let agentReady = false;
      for (let i = 0; i < 30; i++) {
        try {
          const healthRes = await fetch(`http://localhost:${CONFIG.agentPort}/api/health`, {
            method: 'GET',
            signal: AbortSignal.timeout(3000),
          });
          if (healthRes.ok) {
            agentReady = true;
            log(`Agent ready after ${i + 1} attempts`);
            break;
          }
        } catch {
          // Agent 还没准备好
        }
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
      const res = await fetch(`http://localhost:${CONFIG.agentPort}/api/vnc/start`, {
        method: 'POST',
      });
      const data = await res.json();
      log(`/api/vnc/start response: ${JSON.stringify(data)}`);
      
      if (data.status === 'started' || data.status === 'running') {
        setStatus('running');
        
        // 快速轮询等待 websockify 就绪 (每 500ms 检查一次，最多 10 秒)
        log('Step 4: Fast polling websockify...');
        let wsConnected = false;
        for (let i = 0; i < 20; i++) {
          try {
            const wsUrl = wsUrlRef.current || (await vmService.getVncUrl());
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
            break;
          } catch {
            // 继续等待
          }
          await new Promise(r => setTimeout(r, 500));
        }
        
        if (wsConnected) {
          log('=== startVnc() SUCCESS ===');
          setWsReady(true);
          setVncConnected(true);
        } else {
          log('WebSocket not ready after 10s, falling back to background check');
          checkWebsockify();
        }
      } else {
        setStatus('error');
        setErrorMsg(data.error || 'Failed to start VNC');
        log(`=== startVnc() FAILED: ${data.error} ===`);
      }
    } catch (e: any) {
      log(`=== startVnc() ERROR: ${e.message} ===`);
      setStatus('error');
      setErrorMsg(e.message || 'Failed to start VM or VNC');
    }
  }, [checkWebsockify]);

  // 停止 VNC
  const stopVnc = useCallback(async () => {
    try {
      await fetch(`http://localhost:${CONFIG.agentPort}/api/vnc/stop`, {
        method: 'POST',
      });
      setStatus('stopped');
      setWsReady(false);
      setVncConnected(false);
    } catch (e) {
      console.error('Failed to stop VNC:', e);
    }
  }, [setVncConnected]);

  // 重启 xfce4（专门修复桌面环境黑屏）
  const restartXfce4 = useCallback(async () => {
    const startTime = Date.now();
    const log = (msg: string) => console.log(`[VNC restartXfce4 ${((Date.now() - startTime) / 1000).toFixed(1)}s] ${msg}`);
    
    log('=== restartXfce4() BEGIN ===');
    setStatus('starting');
    setErrorMsg('');
    
    try {
      log('Calling /api/vnc/restart-xfce4...');
      const res = await fetch(`http://localhost:${CONFIG.agentPort}/api/vnc/restart-xfce4`, {
        method: 'POST',
      });
      
      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP ${res.status}`);
      }
      
      const data = await res.json();
      log(`/api/vnc/restart-xfce4 response: ${JSON.stringify(data)}`);
      
      setStatus('running');
      log('=== restartXfce4() SUCCESS ===');
      
      // 提示用户刷新连接
      setErrorMsg('xfce4 已重启，请等待几秒后刷新 VNC 连接');
      
      // 3秒后清除提示
      setTimeout(() => {
        setErrorMsg('');
      }, 3000);
    } catch (e: any) {
      log(`=== restartXfce4() ERROR: ${e.message} ===`);
      setStatus('error');
      setErrorMsg(e.message || 'Failed to restart xfce4');
    }
  }, []);

  // 重启 VNC（修复黑屏问题）
  const restartVnc = useCallback(async () => {
    const startTime = Date.now();
    const log = (msg: string) => console.log(`[VNC restartVnc ${((Date.now() - startTime) / 1000).toFixed(1)}s] ${msg}`);
    
    log('=== restartVnc() BEGIN ===');
    setStatus('starting');
    setErrorMsg('');
    setWsReady(false);
    setVncConnected(false);
    
    try {
      log('Calling /api/vnc/restart...');
      const res = await fetch(`http://localhost:${CONFIG.agentPort}/api/vnc/restart`, {
        method: 'POST',
      });
      
      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP ${res.status}`);
      }
      
      const data = await res.json();
      log(`/api/vnc/restart response: ${JSON.stringify(data)}`);
      
      setStatus('running');
      
      // 等待服务就绪
      log('Waiting for services to be ready...');
      let wsConnected = false;
      for (let i = 0; i < 20; i++) {
        try {
          const wsUrl = wsUrlRef.current || (await vmService.getVncUrl());
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
          break;
        } catch {
          // 继续等待
        }
        await new Promise(r => setTimeout(r, 500));
      }
      
      if (wsConnected) {
        log('=== restartVnc() SUCCESS ===');
        setWsReady(true);
        setVncConnected(true);
      } else {
        log('WebSocket not ready after 10s, will retry in background');
        checkWebsockify();
      }
    } catch (e: any) {
      log(`=== restartVnc() ERROR: ${e.message} ===`);
      setStatus('error');
      setErrorMsg(e.message || 'Failed to restart VNC');
    }
  }, [checkWebsockify, setVncConnected]);

  // 初始化：优先直接连接 websockify，不依赖 Agent
  useEffect(() => {
    let intervalId: ReturnType<typeof setInterval> | null = null;
    const startTime = Date.now();
    const log = (msg: string) => console.log(`[VNC ${((Date.now() - startTime) / 1000).toFixed(1)}s] ${msg}`);
    
    const init = async () => {
      log('init() called');
      
      // 策略 1: 直接尝试连接 websockify（不依赖 Agent，最快路径）
      log('Step 1: Trying direct websockify connection...');
      try {
        const wsUrl = `ws://localhost:${CONFIG.wsPort}`;
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
        // WebSocket 直接可用！不需要等 Agent
        log('Direct websockify connection SUCCESS! Skipping Agent check.');
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
        const res = await fetch(`http://localhost:${CONFIG.agentPort}/api/vnc/status`, {
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
        // 如果已连接，不做任何检测，避免创建测试连接导致闪烁
        if (wsReady) {
          return;
        }
        // 未连接时尝试直接连 websockify
        try {
          const wsUrl = `ws://localhost:${CONFIG.wsPort}`;
          const ws = new WebSocket(wsUrl);
          await new Promise<void>((resolve, reject) => {
            const timeout = setTimeout(() => { ws.close(); reject(new Error('timeout')); }, 1500);
            ws.onopen = () => { clearTimeout(timeout); ws.close(); resolve(); };
            ws.onerror = () => { clearTimeout(timeout); reject(new Error('ws error')); };
          });
          console.log('[VNC poll] Direct websockify connected!');
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
  }, [checkVncStatus, checkWebsockify, startVnc, setVncConnected, wsReady]);

  const openVncClient = () => {
    window.open(`vnc://localhost:${CONFIG.vncPort}`, '_blank');
  };

  // Connect/disconnect RFB inside the app
  useEffect(() => {
    if (!(status === 'running' && wsReady)) return;
    if (!rfbContainerRef.current) return;

    let disposed = false;

    const connect = async () => {
      try {
        const wsUrl = wsUrlRef.current || (await vmService.getVncUrl());
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
  }, [status, wsReady, setVncConnected]);

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

  return (
    <div className="h-full flex flex-col bg-nb-bg">
      {/* Toolbar */}
      <div className="h-10 px-4 flex items-center gap-2 bg-nb-surface border-b border-nb-border shrink-0">
        <div className="flex items-center gap-2">
          <span className={`w-2 h-2 rounded-full ${statusDisplay.color}`} />
          <span className="text-xs text-nb-text-muted">{statusDisplay.text}</span>
        </div>

        <div className="flex-1" />

        {/* 控制按钮 */}
        {status === 'stopped' || status === 'unknown' || status === 'error' ? (
          <button
            onClick={startVnc}
            className="flex items-center gap-1.5 px-2 py-1 bg-nb-success hover:bg-nb-success/80 text-white rounded text-xs transition-colors"
            title="启动 VNC"
          >
            <Play size={12} />
            <span>Start</span>
          </button>
        ) : status === 'running' ? (
          <>
            <button
              onClick={restartXfce4}
              className="flex items-center gap-1.5 px-2 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded text-xs transition-colors"
              title="重启 xfce4 桌面环境（修复黑屏）"
            >
              <RefreshCw size={12} />
              <span>Fix Desktop</span>
            </button>
            <button
              onClick={restartVnc}
              className="flex items-center gap-1.5 px-2 py-1 bg-nb-warning hover:bg-nb-warning/80 text-white rounded text-xs transition-colors"
              title="重启所有 VNC 服务"
            >
              <RefreshCw size={12} />
              <span>Restart All</span>
            </button>
            <button
              onClick={stopVnc}
              className="flex items-center gap-1.5 px-2 py-1 bg-nb-error hover:bg-nb-error/80 text-white rounded text-xs transition-colors"
              title="停止 VNC"
            >
              <Square size={12} />
              <span>Stop</span>
            </button>
          </>
        ) : null}

        <button
          onClick={checkVncStatus}
          className="p-1.5 hover:bg-nb-surface-2 rounded transition-colors"
          title="刷新状态"
        >
          <RefreshCw size={14} className={`text-nb-text-muted ${status === 'starting' ? 'animate-spin' : ''}`} />
        </button>

        <button
          onClick={openVncClient}
          className="flex items-center gap-1.5 px-2 py-1 bg-nb-accent hover:bg-nb-accent/80 text-white rounded text-xs transition-colors"
          title="在 VNC 客户端中打开"
        >
          <ExternalLink size={12} />
          <span>VNC</span>
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 relative overflow-hidden bg-black">
        {status === 'running' && wsReady ? (
          // VNC 已连接 - 直接渲染 noVNC canvas
          <div ref={rfbContainerRef} className="absolute inset-0" />
        ) : status === 'starting' ? (
          // 启动中
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
