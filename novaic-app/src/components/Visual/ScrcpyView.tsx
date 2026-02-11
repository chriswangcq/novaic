/**
 * Scrcpy View 组件
 * 
 * 使用 WebCodecs 解码 H.264 视频流，实现低延迟的 Android 屏幕投射
 * 
 * 架构:
 * 前端 React (WebCodecs 解码) <--WebSocket--> Rust 后端 <--ADB 端口转发--> Android scrcpy-server
 */

import { useEffect, useRef, useState, memo, useCallback } from 'react';
import { Play, Loader2, Smartphone, Square } from 'lucide-react';

interface ScrcpyViewProps {
  /** 设备序列号，如 "emulator-5554" */
  deviceSerial?: string;
  /** WebSocket URL，默认为 ws://localhost:8080/api/android/scrcpy */
  wsUrl?: string;
  /** 是否为缩略图模式 */
  isThumbnail?: boolean;
  /** 是否自动连接 */
  autoConnect?: boolean;
  /** 自定义 className */
  className?: string;
  /** 连接成功回调 */
  onConnected?: () => void;
  /** 断开连接回调 */
  onDisconnected?: () => void;
  /** 错误回调 */
  onError?: (error: string) => void;
}

interface DeviceInfo {
  device: string;
  codec: string;
  width: number;
  height: number;
}

interface NALUnit {
  type: number;
  data: Uint8Array;
  startCodeLen: number;
}

interface PendingFrame {
  data: Uint8Array;
  pts: number;
  isKeyFrame: boolean;
}

type ConnectionStatus = 'disconnected' | 'connecting' | 'connected' | 'error';

// 检查 WebCodecs 是否支持
const isWebCodecsSupported = typeof VideoDecoder !== 'undefined';

// ==================== H.264 NAL 解析工具 ====================

/**
 * 从 Annex B 格式的 H.264 数据中解析 NAL 单元
 * Annex B 使用 start code (0x00000001 或 0x000001) 分隔 NAL 单元
 */
function parseNALUnits(data: Uint8Array): NALUnit[] {
  const nalUnits: NALUnit[] = [];
  let i = 0;
  
  while (i < data.length) {
    // 查找 start code
    let startCodeLen = 0;
    if (i + 3 < data.length && data[i] === 0 && data[i + 1] === 0) {
      if (data[i + 2] === 1) {
        startCodeLen = 3; // 0x000001
      } else if (data[i + 2] === 0 && i + 4 <= data.length && data[i + 3] === 1) {
        startCodeLen = 4; // 0x00000001
      }
    }
    
    if (startCodeLen === 0) {
      i++;
      continue;
    }
    
    // 找到 start code，现在找下一个 start code 或数据结束
    const nalStart = i + startCodeLen;
    let nalEnd = data.length;
    
    for (let j = nalStart; j < data.length - 2; j++) {
      if (data[j] === 0 && data[j + 1] === 0) {
        if (data[j + 2] === 1 || (j + 3 < data.length && data[j + 2] === 0 && data[j + 3] === 1)) {
          nalEnd = j;
          break;
        }
      }
    }
    
    if (nalEnd > nalStart) {
      const nalData = data.slice(nalStart, nalEnd);
      const nalType = nalData[0] & 0x1F;
      nalUnits.push({
        type: nalType,
        data: nalData,
        startCodeLen: startCodeLen
      });
    }
    
    i = nalEnd;
  }
  
  return nalUnits;
}

/**
 * 从 SPS 中解析 profile, level 等信息
 */
function parseSPS(spsData: Uint8Array): { profileIdc: number; constraintFlags: number; levelIdc: number } | null {
  if (spsData.length < 4) return null;
  
  const profileIdc = spsData[1];
  const constraintFlags = spsData[2];
  const levelIdc = spsData[3];
  
  return { profileIdc, constraintFlags, levelIdc };
}

/**
 * 构建 AVC Decoder Configuration Record
 */
function buildAVCDecoderConfigurationRecord(sps: Uint8Array, pps: Uint8Array): Uint8Array | null {
  const spsInfo = parseSPS(sps);
  if (!spsInfo) {
    console.error('[Scrcpy] Failed to parse SPS');
    return null;
  }
  
  console.log(`[Scrcpy] SPS: profile=${spsInfo.profileIdc}, level=${spsInfo.levelIdc}`);
  
  const totalLength = 6 + 2 + sps.length + 1 + 2 + pps.length;
  const record = new Uint8Array(totalLength);
  
  let offset = 0;
  
  // configurationVersion
  record[offset++] = 1;
  
  // AVCProfileIndication
  record[offset++] = spsInfo.profileIdc;
  
  // profile_compatibility
  record[offset++] = spsInfo.constraintFlags;
  
  // AVCLevelIndication
  record[offset++] = spsInfo.levelIdc;
  
  // lengthSizeMinusOne (使用 4 字节长度前缀)
  record[offset++] = 0xFF;
  
  // numOfSequenceParameterSets
  record[offset++] = 0xE1;
  
  // SPS length (big-endian)
  record[offset++] = (sps.length >> 8) & 0xFF;
  record[offset++] = sps.length & 0xFF;
  
  // SPS data
  record.set(sps, offset);
  offset += sps.length;
  
  // numOfPictureParameterSets
  record[offset++] = 1;
  
  // PPS length (big-endian)
  record[offset++] = (pps.length >> 8) & 0xFF;
  record[offset++] = pps.length & 0xFF;
  
  // PPS data
  record.set(pps, offset);
  
  return record;
}

/**
 * 将 Annex B 格式转换为 AVC 格式 (length-prefixed)
 */
function annexBToAVC(annexBData: Uint8Array): Uint8Array | null {
  const nalUnits = parseNALUnits(annexBData);
  
  // 过滤掉 SPS (7) 和 PPS (8)
  const filteredNALs = nalUnits.filter(nal => nal.type !== 7 && nal.type !== 8);
  
  if (filteredNALs.length === 0) {
    return null;
  }
  
  let totalLength = 0;
  for (const nal of filteredNALs) {
    totalLength += 4 + nal.data.length;
  }
  
  const avcData = new Uint8Array(totalLength);
  let offset = 0;
  
  for (const nal of filteredNALs) {
    const len = nal.data.length;
    avcData[offset++] = (len >> 24) & 0xFF;
    avcData[offset++] = (len >> 16) & 0xFF;
    avcData[offset++] = (len >> 8) & 0xFF;
    avcData[offset++] = len & 0xFF;
    
    avcData.set(nal.data, offset);
    offset += len;
  }
  
  return avcData;
}

/**
 * 检查数据中是否包含关键帧 (IDR)
 */
function containsKeyFrame(nalUnits: NALUnit[]): boolean {
  return nalUnits.some(nal => nal.type === 5);
}

function ScrcpyViewComponent({ 
  deviceSerial, 
  wsUrl: customWsUrl,
  isThumbnail = false,
  autoConnect = false,
  className,
  onConnected,
  onDisconnected,
  onError,
}: ScrcpyViewProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const decoderRef = useRef<VideoDecoder | null>(null);
  const [status, setStatus] = useState<ConnectionStatus>('disconnected');
  const [errorMsg, setErrorMsg] = useState('');
  const [deviceInfo, setDeviceInfo] = useState<DeviceInfo | null>(null);
  const [fps, setFps] = useState(0);
  const frameCountRef = useRef(0);
  const lastFpsUpdateRef = useRef(Date.now());
  
  // H.264 解析相关状态
  const spsDataRef = useRef<Uint8Array | null>(null);
  const ppsDataRef = useRef<Uint8Array | null>(null);
  const decoderConfiguredRef = useRef(false);
  const pendingFramesRef = useRef<PendingFrame[]>([]);
  const deviceInfoRef = useRef<DeviceInfo | null>(null);
  
  // 用于触控检测
  const touchStartRef = useRef<{ x: number; y: number; time: number } | null>(null);
  
  // 构建 WebSocket URL
  const wsUrl = customWsUrl || `ws://localhost:8080/api/android/scrcpy${deviceSerial ? `?device=${deviceSerial}` : ''}`;
  
  // 渲染 VideoFrame 到 Canvas
  const renderFrame = useCallback((frame: VideoFrame) => {
    const canvas = canvasRef.current;
    if (!canvas) {
      frame.close();
      return;
    }
    
    const ctx = canvas.getContext('2d');
    if (!ctx) {
      frame.close();
      return;
    }
    
    // 更新 canvas 尺寸
    if (canvas.width !== frame.displayWidth || canvas.height !== frame.displayHeight) {
      canvas.width = frame.displayWidth;
      canvas.height = frame.displayHeight;
    }
    
    // 绘制帧
    ctx.drawImage(frame, 0, 0);
    frame.close();
    
    // 更新 FPS
    frameCountRef.current++;
    const now = Date.now();
    if (now - lastFpsUpdateRef.current >= 1000) {
      setFps(frameCountRef.current);
      frameCountRef.current = 0;
      lastFpsUpdateRef.current = now;
    }
  }, []);
  
  // 创建 VideoDecoder 实例（但不配置）
  const createDecoder = useCallback(() => {
    if (decoderRef.current) {
      decoderRef.current.close();
    }
    
    const decoder = new VideoDecoder({
      output: (frame) => {
        renderFrame(frame);
      },
      error: (e) => {
        console.error('[Scrcpy] VideoDecoder error:', e);
        setErrorMsg(`Decoder error: ${e.message}`);
      }
    });
    
    decoderRef.current = decoder;
    console.log('[Scrcpy] VideoDecoder created (waiting for SPS/PPS)');
  }, [renderFrame]);
  
  // 解码一帧
  const decodeFrame = useCallback((h264Data: Uint8Array, pts: number, isKeyFrame: boolean) => {
    const decoder = decoderRef.current;
    if (!decoder || decoder.state !== 'configured') {
      return;
    }
    
    // 转换为 AVC 格式
    const avcData = annexBToAVC(h264Data);
    if (!avcData) {
      return;
    }
    
    try {
      const chunk = new EncodedVideoChunk({
        type: isKeyFrame ? 'key' : 'delta',
        timestamp: pts,
        data: avcData,
      });
      
      decoder.decode(chunk);
    } catch (e) {
      console.error('[Scrcpy] Decode error:', e);
    }
  }, []);
  
  // 使用 SPS/PPS 配置解码器
  const configureDecoderWithAVC = useCallback((_codec: string, width: number, height: number, sps: Uint8Array, pps: Uint8Array) => {
    if (!decoderRef.current) {
      createDecoder();
    }
    
    // 构建 AVC decoder configuration record
    const avcConfig = buildAVCDecoderConfigurationRecord(sps, pps);
    if (!avcConfig) {
      console.error('[Scrcpy] Failed to build AVC config');
      return false;
    }
    
    // 根据 SPS 构建 codec 字符串
    const spsInfo = parseSPS(sps);
    let codecString = 'avc1.';
    if (spsInfo) {
      codecString += spsInfo.profileIdc.toString(16).padStart(2, '0');
      codecString += spsInfo.constraintFlags.toString(16).padStart(2, '0');
      codecString += spsInfo.levelIdc.toString(16).padStart(2, '0');
    } else {
      codecString = 'avc1.640028';
    }
    
    console.log(`[Scrcpy] Configuring decoder with codec: ${codecString}`);
    console.log(`[Scrcpy] AVC config size: ${avcConfig.length} bytes`);
    
    try {
      decoderRef.current!.configure({
        codec: codecString,
        codedWidth: width,
        codedHeight: height,
        description: avcConfig,
        optimizeForLatency: true,
      });
      
      decoderConfiguredRef.current = true;
      console.log('[Scrcpy] VideoDecoder configured with AVC description');
      
      // 处理等待中的帧
      if (pendingFramesRef.current.length > 0) {
        console.log(`[Scrcpy] Processing ${pendingFramesRef.current.length} pending frames`);
        for (const frame of pendingFramesRef.current) {
          decodeFrame(frame.data, frame.pts, frame.isKeyFrame);
        }
        pendingFramesRef.current = [];
      }
      
      return true;
    } catch (e) {
      console.error('[Scrcpy] Failed to configure decoder:', e);
      return false;
    }
  }, [createDecoder, decodeFrame]);
  
  // 初始化 VideoDecoder（重置状态）
  const initDecoder = useCallback((codec: string, width: number, height: number) => {
    // 重置状态
    spsDataRef.current = null;
    ppsDataRef.current = null;
    decoderConfiguredRef.current = false;
    pendingFramesRef.current = [];
    
    // 保存设备信息供后续使用
    deviceInfoRef.current = { device: '', codec, width, height };
    
    // 创建解码器实例
    createDecoder();
    
    console.log('[Scrcpy] VideoDecoder initialized');
  }, [createDecoder]);
  
  // 发送控制消息
  const sendControlMessage = useCallback((event: object) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(event));
    }
  }, []);
  
  // 计算实际坐标（考虑缩放）
  const getScaledCoords = useCallback((clientX: number, clientY: number) => {
    const canvas = canvasRef.current;
    if (!canvas || !deviceInfo) return null;
    
    const rect = canvas.getBoundingClientRect();
    const scaleX = deviceInfo.width / rect.width;
    const scaleY = deviceInfo.height / rect.height;
    
    const x = Math.round((clientX - rect.left) * scaleX);
    const y = Math.round((clientY - rect.top) * scaleY);
    
    return { x, y };
  }, [deviceInfo]);
  
  // 处理鼠标按下
  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    const coords = getScaledCoords(e.clientX, e.clientY);
    if (coords && deviceInfo) {
      touchStartRef.current = { ...coords, time: Date.now() };
      
      // 发送 touch down 事件
      sendControlMessage({
        type: 'inject_touch',
        action: 0, // ACTION_DOWN
        pointerId: 0,
        x: coords.x,
        y: coords.y,
        screenWidth: deviceInfo.width,
        screenHeight: deviceInfo.height,
      });
    }
  }, [getScaledCoords, deviceInfo, sendControlMessage]);
  
  // 处理鼠标移动
  const handleMouseMove = useCallback((e: React.MouseEvent) => {
    if (!touchStartRef.current) return;
    
    const coords = getScaledCoords(e.clientX, e.clientY);
    if (coords && deviceInfo) {
      // 发送 touch move 事件
      sendControlMessage({
        type: 'inject_touch',
        action: 2, // ACTION_MOVE
        pointerId: 0,
        x: coords.x,
        y: coords.y,
        screenWidth: deviceInfo.width,
        screenHeight: deviceInfo.height,
      });
    }
  }, [getScaledCoords, deviceInfo, sendControlMessage]);
  
  // 处理鼠标抬起
  const handleMouseUp = useCallback((e: React.MouseEvent) => {
    const coords = getScaledCoords(e.clientX, e.clientY);
    if (coords && deviceInfo) {
      // 发送 touch up 事件
      sendControlMessage({
        type: 'inject_touch',
        action: 1, // ACTION_UP
        pointerId: 0,
        x: coords.x,
        y: coords.y,
        screenWidth: deviceInfo.width,
        screenHeight: deviceInfo.height,
      });
    }
    touchStartRef.current = null;
  }, [getScaledCoords, deviceInfo, sendControlMessage]);
  
  // 处理键盘事件
  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    // 映射常用按键到 Android keycode
    const keyMap: Record<string, number> = {
      'Backspace': 67,    // KEYCODE_DEL
      'Enter': 66,        // KEYCODE_ENTER
      'Escape': 111,      // KEYCODE_ESCAPE
      'ArrowUp': 19,      // KEYCODE_DPAD_UP
      'ArrowDown': 20,    // KEYCODE_DPAD_DOWN
      'ArrowLeft': 21,    // KEYCODE_DPAD_LEFT
      'ArrowRight': 22,   // KEYCODE_DPAD_RIGHT
      'Home': 3,          // KEYCODE_HOME
      'Tab': 61,          // KEYCODE_TAB
    };
    
    const keycode = keyMap[e.key];
    if (keycode) {
      e.preventDefault();
      sendControlMessage({
        type: 'inject_keycode',
        action: 0, // ACTION_DOWN
        keycode,
        repeat: 0,
        metastate: 0,
      });
    }
  }, [sendControlMessage]);
  
  const handleKeyUp = useCallback((e: React.KeyboardEvent) => {
    const keyMap: Record<string, number> = {
      'Backspace': 67,
      'Enter': 66,
      'Escape': 111,
      'ArrowUp': 19,
      'ArrowDown': 20,
      'ArrowLeft': 21,
      'ArrowRight': 22,
      'Home': 3,
      'Tab': 61,
    };
    
    const keycode = keyMap[e.key];
    if (keycode) {
      e.preventDefault();
      sendControlMessage({
        type: 'inject_keycode',
        action: 1, // ACTION_UP
        keycode,
        repeat: 0,
        metastate: 0,
      });
    }
  }, [sendControlMessage]);
  
  // 连接到 Android 设备
  const connect = useCallback(async () => {
    if (!isWebCodecsSupported) {
      setErrorMsg('WebCodecs API not supported in this browser');
      setStatus('error');
      return;
    }
    
    if (wsRef.current) {
      wsRef.current.close();
    }
    
    setStatus('connecting');
    setErrorMsg('');
    frameCountRef.current = 0;
    
    try {
      const ws = new WebSocket(wsUrl);
      ws.binaryType = 'arraybuffer';
      wsRef.current = ws;
      
      ws.onopen = () => {
        console.log('[Scrcpy] WebSocket connected');
      };
      
      ws.onmessage = (event) => {
        if (typeof event.data === 'string') {
          // JSON 消息（设备信息或错误）
          try {
            const message = JSON.parse(event.data);
            
            if (message.type === 'info') {
              console.log('[Scrcpy] Device info:', message);
              setDeviceInfo({
                device: message.device,
                codec: message.codec,
                width: message.width,
                height: message.height,
              });
              
              // 初始化解码器
              initDecoder(message.codec, message.width, message.height);
              setStatus('connected');
              onConnected?.();
            } else if (message.type === 'error') {
              console.error('[Scrcpy] Error:', message.message);
              setErrorMsg(message.message);
              setStatus('error');
              onError?.(message.message);
            }
          } catch (e) {
            console.warn('[Scrcpy] Failed to parse message:', e);
          }
        } else if (event.data instanceof ArrayBuffer) {
          // 二进制数据（H.264 视频帧）
          // scrcpy 帧格式:
          // - 8 字节: flags (2 bits) + PTS (62 bits), big-endian
          //   - bit 63: config packet flag
          //   - bit 62: key frame flag
          //   - bits 0-61: PTS in microseconds
          // - 4 字节: packet size, big-endian
          // - N 字节: H.264 数据 (Annex B 格式)
          const data = new Uint8Array(event.data);
          
          if (data.length < 12) {
            console.warn('[Scrcpy] Invalid packet size:', data.length);
            return;
          }
          
          // 解析 PTS 和 flags (8 字节, big-endian)
          const headerView = new DataView(event.data, 0, 8);
          const ptsHigh = headerView.getUint32(0, false);
          const ptsLow = headerView.getUint32(4, false);
          
          // 提取 flags
          const isConfig = (ptsHigh >> 31) & 1;
          const isKeyFrame = (ptsHigh >> 30) & 1;
          
          // 提取 PTS (62 bits)
          const pts = BigInt(ptsHigh & 0x3FFFFFFF) * BigInt(0x100000000) + BigInt(ptsLow);
          
          // 解析 size (4 字节, big-endian)
          const sizeView = new DataView(event.data, 8, 4);
          const packetSize = sizeView.getUint32(0, false);
          
          // 提取 H.264 数据 (Annex B 格式)
          const h264Data = data.slice(12);
          
          if (h264Data.length !== packetSize) {
            console.warn('[Scrcpy] Size mismatch:', h264Data.length, 'vs', packetSize);
          }
          
          // 解析 NAL 单元
          const nalUnits = parseNALUnits(h264Data);
          
          // 提取 SPS 和 PPS
          for (const nal of nalUnits) {
            if (nal.type === 7) { // SPS
              spsDataRef.current = nal.data;
              console.log(`[Scrcpy] Found SPS: ${nal.data.length} bytes`);
            } else if (nal.type === 8) { // PPS
              ppsDataRef.current = nal.data;
              console.log(`[Scrcpy] Found PPS: ${nal.data.length} bytes`);
            }
          }
          
          // 如果有 SPS 和 PPS 但解码器未配置，则配置解码器
          if (spsDataRef.current && ppsDataRef.current && !decoderConfiguredRef.current && deviceInfoRef.current) {
            configureDecoderWithAVC(
              deviceInfoRef.current.codec,
              deviceInfoRef.current.width,
              deviceInfoRef.current.height,
              spsDataRef.current,
              ppsDataRef.current
            );
          }
          
          // 检查是否包含关键帧
          const hasKeyFrame = containsKeyFrame(nalUnits) || isKeyFrame === 1 || isConfig === 1;
          
          // 解码
          if (decoderConfiguredRef.current && decoderRef.current && decoderRef.current.state === 'configured') {
            decodeFrame(h264Data, Number(pts), hasKeyFrame);
          } else if (hasKeyFrame) {
            // 缓存关键帧，等待配置完成
            pendingFramesRef.current.push({
              data: h264Data,
              pts: Number(pts),
              isKeyFrame: true
            });
            console.log('[Scrcpy] Buffered key frame (waiting for decoder config)');
          }
        }
      };
      
      ws.onerror = (e) => {
        console.error('[Scrcpy] WebSocket error:', e);
        // 不立即显示错误，可能是连接正在建立中
        // 只有在 onclose 时才确定连接失败
      };
      
      ws.onclose = (e) => {
        console.log('[Scrcpy] WebSocket closed, code:', e.code);
        
        // 清理解码器
        if (decoderRef.current) {
          decoderRef.current.close();
          decoderRef.current = null;
        }
        
        // 如果从未成功连接过（没有收到设备信息），显示错误
        if (!deviceInfoRef.current) {
          setStatus('error');
          setErrorMsg('连接失败，请确保 vmcontrol 服务正在运行');
          onError?.('连接失败');
        } else {
          setStatus('disconnected');
          onDisconnected?.();
        }
      };
      
    } catch (e: unknown) {
      console.error('[Scrcpy] Connection error:', e);
      setStatus('error');
      const errorMessage = e instanceof Error ? e.message : 'Failed to connect';
      setErrorMsg(errorMessage);
      onError?.(errorMessage);
    }
  }, [wsUrl, initDecoder, configureDecoderWithAVC, decodeFrame, onConnected, onDisconnected, onError]);
  
  // 断开连接
  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    
    if (decoderRef.current) {
      decoderRef.current.close();
      decoderRef.current = null;
    }
    
    // 重置 H.264 解析状态
    spsDataRef.current = null;
    ppsDataRef.current = null;
    decoderConfiguredRef.current = false;
    pendingFramesRef.current = [];
    deviceInfoRef.current = null;
    
    setStatus('disconnected');
    setFps(0);
    setDeviceInfo(null);
  }, []);
  
  // 自动连接和重试
  const retryCountRef = useRef(0);
  const maxRetries = 3;
  const retryDelay = 2000; // 2秒
  
  useEffect(() => {
    if (!autoConnect) return;
    
    let retryTimer: NodeJS.Timeout | null = null;
    
    const attemptConnect = () => {
      connect();
    };
    
    attemptConnect();
    
    return () => {
      if (retryTimer) clearTimeout(retryTimer);
      disconnect();
    };
  }, [autoConnect, connect, disconnect]);
  
  // 自动重试（当连接失败时）
  useEffect(() => {
    if (status === 'error' && autoConnect && retryCountRef.current < maxRetries) {
      const timer = setTimeout(() => {
        retryCountRef.current++;
        console.log(`[Scrcpy] Retrying connection (${retryCountRef.current}/${maxRetries})...`);
        setStatus('connecting');
        setErrorMsg('');
        connect();
      }, retryDelay);
      
      return () => clearTimeout(timer);
    }
    
    // 连接成功后重置重试计数
    if (status === 'connected') {
      retryCountRef.current = 0;
    }
  }, [status, autoConnect, connect]);
  
  // 渲染内容
  const renderContent = () => {
    if (status === 'connected') {
      return (
        <div 
          ref={containerRef}
          className="w-full h-full flex items-center justify-center"
          tabIndex={0}
          onKeyDown={handleKeyDown}
          onKeyUp={handleKeyUp}
        >
          <canvas
            ref={canvasRef}
            className="max-w-full max-h-full object-contain cursor-pointer select-none"
            style={{ 
              imageRendering: 'auto',
            }}
            onMouseDown={handleMouseDown}
            onMouseMove={handleMouseMove}
            onMouseUp={handleMouseUp}
            onMouseLeave={handleMouseUp}
          />
        </div>
      );
    }
    
    if (status === 'connecting') {
      return (
        <div className="absolute inset-0 flex flex-col items-center justify-center text-nb-text-muted">
          <Loader2 size={48} className="mb-4 opacity-50 animate-spin" />
          <p className="text-sm">
            {retryCountRef.current > 0 
              ? `正在重试连接 (${retryCountRef.current}/${maxRetries})...` 
              : '正在连接 Android 设备...'}
          </p>
          <p className="text-xs text-gray-500 mt-2">启动 scrcpy-server 中</p>
        </div>
      );
    }
    
    // 未连接
    const isRetrying = status === 'error' && autoConnect && retryCountRef.current < maxRetries;
    
    return (
      <div className="absolute inset-0 flex flex-col items-center justify-center text-nb-text-muted">
        <Smartphone size={48} className="mb-4 opacity-50" />
        <p className="text-sm mb-2">
          {status === 'error' 
            ? (isRetrying ? `正在重试连接 (${retryCountRef.current + 1}/${maxRetries})...` : '连接失败') 
            : 'Android 设备未连接'}
        </p>
        {!isWebCodecsSupported && (
          <p className="text-xs text-yellow-500 mb-2">WebCodecs API 不支持</p>
        )}
        {errorMsg && !isRetrying && <p className="text-xs text-red-500 mb-4 max-w-xs text-center">{errorMsg}</p>}
        <button
          onClick={connect}
          disabled={!isWebCodecsSupported || isRetrying}
          className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Play size={16} />
          连接设备
        </button>
      </div>
    );
  };
  
  if (isThumbnail) {
    return (
      <div className={`h-full w-full bg-black relative ${className || ''}`}>
        <canvas ref={canvasRef} className="w-full h-full object-contain" />
        {status !== 'connected' && renderContent()}
      </div>
    );
  }
  
  return (
    <div className={`flex flex-col h-full bg-black ${className || ''}`}>
      {/* 工具栏 */}
      <div className="flex items-center justify-between px-4 py-2 bg-gray-900 border-b border-gray-700">
        <div className="flex items-center gap-2">
          <Smartphone size={16} className="text-green-500" />
          <span className="text-sm text-gray-300">
            {deviceInfo?.device || deviceSerial || 'Android Device'}
          </span>
          {status === 'connected' && deviceInfo && (
            <>
              <span className="text-xs text-gray-500">
                {deviceInfo.width}x{deviceInfo.height}
              </span>
              <span className="text-xs text-blue-400">
                {deviceInfo.codec.toUpperCase()}
              </span>
              <span className="text-xs text-green-500">
                {fps} FPS
              </span>
            </>
          )}
        </div>
        <div className="flex items-center gap-2">
          {status === 'connected' ? (
            <button
              onClick={disconnect}
              className="px-3 py-1 text-xs bg-red-600 hover:bg-red-700 text-white rounded transition-colors flex items-center gap-1"
            >
              <Square size={12} />
              断开
            </button>
          ) : (
            <button
              onClick={connect}
              disabled={status === 'connecting' || !isWebCodecsSupported}
              className="px-3 py-1 text-xs bg-green-600 hover:bg-green-700 text-white rounded transition-colors disabled:opacity-50 flex items-center gap-1"
            >
              <Play size={12} />
              连接
            </button>
          )}
        </div>
      </div>
      
      {/* 视频区域 */}
      <div className="flex-1 relative overflow-hidden bg-black">
        {renderContent()}
      </div>
    </div>
  );
}

export const ScrcpyView = memo(ScrcpyViewComponent);
