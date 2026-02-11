use axum::extract::ws::{WebSocket, Message};
use tokio::process::Command;
use tokio::net::TcpStream;
use futures_util::{StreamExt, SinkExt};
use std::process::Stdio;
use crate::error::VmError;
use std::sync::Arc;
use std::sync::atomic::{AtomicBool, Ordering};
use tokio::io::{AsyncReadExt, AsyncWriteExt, BufReader};

/// scrcpy-server 版本 (必须与服务器版本匹配)
const SCRCPY_VERSION: &str = "3.3.4";

/// scrcpy-server.jar 路径
fn get_scrcpy_server_path() -> String {
    std::env::var("SCRCPY_SERVER").unwrap_or_else(|_| {
        // 尝试常见路径
        let paths = [
            "/opt/homebrew/share/scrcpy/scrcpy-server",
            "/opt/homebrew/Cellar/scrcpy/3.3.4/share/scrcpy/scrcpy-server",
            "/opt/homebrew/Cellar/scrcpy/3.1/share/scrcpy/scrcpy-server",
            "/opt/homebrew/Cellar/scrcpy/3.0/share/scrcpy/scrcpy-server",
            "/usr/local/share/scrcpy/scrcpy-server",
            "/usr/share/scrcpy/scrcpy-server",
        ];
        
        for path in paths {
            if std::path::Path::new(path).exists() {
                return path.to_string();
            }
        }
        
        // 默认路径
        "/opt/homebrew/share/scrcpy/scrcpy-server".to_string()
    })
}

/// 获取 ADB 路径
fn get_adb_path() -> String {
    std::env::var("ADB").unwrap_or_else(|_| {
        let home = std::env::var("HOME").unwrap_or_default();
        let custom_path = format!("{}/android-sdk/platform-tools/adb", home);
        if std::path::Path::new(&custom_path).exists() {
            return custom_path;
        }
        if std::path::Path::new("/opt/homebrew/bin/adb").exists() {
            return "/opt/homebrew/bin/adb".to_string();
        }
        "adb".to_string()
    })
}

/// Scrcpy 视频编解码器 ID
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
#[repr(u32)]
pub enum VideoCodecId {
    H264 = 0x68323634,  // "h264"
    H265 = 0x68323635,  // "h265"
    Av1 = 0x00617631,   // "av1\0"
}

impl VideoCodecId {
    pub fn from_u32(value: u32) -> Option<Self> {
        match value {
            0x68323634 => Some(VideoCodecId::H264),
            0x68323635 => Some(VideoCodecId::H265),
            0x00617631 => Some(VideoCodecId::Av1),
            _ => None,
        }
    }
    
    pub fn as_str(&self) -> &'static str {
        match self {
            VideoCodecId::H264 => "h264",
            VideoCodecId::H265 => "h265",
            VideoCodecId::Av1 => "av1",
        }
    }
}

/// 设备元数据
#[derive(Debug, Clone)]
pub struct DeviceMetadata {
    pub device_name: String,
    pub codec: VideoCodecId,
    pub width: u32,
    pub height: u32,
}

/// Android 设备流代理 - 使用真正的 scrcpy-server
pub struct ScrcpyProxy {
    device_serial: String,
}

impl ScrcpyProxy {
    pub fn new(device_serial: impl Into<String>) -> Self {
        Self {
            device_serial: device_serial.into(),
        }
    }

    /// 推送 scrcpy-server 到设备
    async fn push_server(&self) -> Result<(), VmError> {
        let adb_path = get_adb_path();
        let server_path = get_scrcpy_server_path();
        
        tracing::info!("Pushing scrcpy-server from {} to device {}", server_path, self.device_serial);
        
        // 检查服务器文件是否存在
        if !std::path::Path::new(&server_path).exists() {
            return Err(VmError::ScrcpyError(format!(
                "scrcpy-server not found at {}. Install scrcpy with: brew install scrcpy",
                server_path
            )));
        }
        
        let output = Command::new(&adb_path)
            .args(["-s", &self.device_serial, "push", &server_path, "/data/local/tmp/scrcpy-server.jar"])
            .output()
            .await
            .map_err(|e| VmError::ScrcpyError(format!("Failed to push scrcpy-server: {}", e)))?;
        
        if !output.status.success() {
            let stderr = String::from_utf8_lossy(&output.stderr);
            return Err(VmError::ScrcpyError(format!("Failed to push scrcpy-server: {}", stderr)));
        }
        
        tracing::info!("scrcpy-server pushed successfully");
        Ok(())
    }

    /// 生成随机的 scid (用于区分不同的 scrcpy 实例)
    fn generate_scid() -> u32 {
        use std::time::{SystemTime, UNIX_EPOCH};
        let duration = SystemTime::now().duration_since(UNIX_EPOCH).unwrap();
        (duration.as_nanos() & 0x7FFFFFFF) as u32
    }

    /// 启动 scrcpy-server
    async fn start_server(&self, scid: u32) -> Result<tokio::process::Child, VmError> {
        let adb_path = get_adb_path();
        
        // scrcpy 3.x 启动命令
        // 参考: https://github.com/Genymobile/scrcpy/blob/master/doc/develop.md
        // 注意: scid 必须是十六进制格式
        let server_args = format!(
            "CLASSPATH=/data/local/tmp/scrcpy-server.jar app_process / com.genymobile.scrcpy.Server {} \
            scid={:08x} \
            log_level=info \
            tunnel_forward=true \
            video=true \
            audio=false \
            control=true \
            video_bit_rate=8000000 \
            max_size=0 \
            max_fps=60 \
            video_codec=h264 \
            send_device_meta=true \
            send_frame_meta=true \
            send_codec_meta=true \
            send_dummy_byte=true \
            cleanup=true \
            power_off_on_close=false \
            clipboard_autosync=false \
            downsize_on_error=true",
            SCRCPY_VERSION,
            scid
        );
        
        tracing::info!("Starting scrcpy-server: adb -s {} shell {}", self.device_serial, server_args);
        
        let child = Command::new(&adb_path)
            .args(["-s", &self.device_serial, "shell", &server_args])
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .spawn()
            .map_err(|e| VmError::ScrcpyError(format!("Failed to start scrcpy-server: {}", e)))?;
        
        Ok(child)
    }

    /// 建立 ADB 端口转发并连接
    async fn setup_and_connect(&self, scid: u32) -> Result<(TcpStream, TcpStream), VmError> {
        let adb_path = get_adb_path();
        
        // 使用 scid 创建唯一的 socket 名称
        let socket_name = format!("scrcpy_{:08x}", scid);
        
        // 设置端口转发
        // 视频 socket: 27183
        // 控制 socket: 27184
        let video_port = 27183;
        let control_port = 27184;
        
        // 先移除可能存在的旧转发
        let _ = Command::new(&adb_path)
            .args(["-s", &self.device_serial, "forward", "--remove", &format!("tcp:{}", video_port)])
            .output()
            .await;
        let _ = Command::new(&adb_path)
            .args(["-s", &self.device_serial, "forward", "--remove", &format!("tcp:{}", control_port)])
            .output()
            .await;
        
        // 建立视频端口转发
        let forward_target = format!("localabstract:{}", socket_name);
        tracing::info!("Setting up forward: tcp:{} -> {}", video_port, forward_target);
        
        let output = Command::new(&adb_path)
            .args(["-s", &self.device_serial, "forward", &format!("tcp:{}", video_port), &forward_target])
            .output()
            .await
            .map_err(|e| VmError::ScrcpyError(format!("Failed to forward video port: {}", e)))?;
        
        if !output.status.success() {
            let stderr = String::from_utf8_lossy(&output.stderr);
            return Err(VmError::ScrcpyError(format!("Failed to forward video port: {}", stderr)));
        }
        
        // 建立控制端口转发 (使用同一个 socket)
        let output = Command::new(&adb_path)
            .args(["-s", &self.device_serial, "forward", &format!("tcp:{}", control_port), &forward_target])
            .output()
            .await
            .map_err(|e| VmError::ScrcpyError(format!("Failed to forward control port: {}", e)))?;
        
        if !output.status.success() {
            let stderr = String::from_utf8_lossy(&output.stderr);
            return Err(VmError::ScrcpyError(format!("Failed to forward control port: {}", stderr)));
        }
        
        tracing::info!("Port forwarding established");
        
        // 等待服务器启动
        tokio::time::sleep(tokio::time::Duration::from_millis(1000)).await;
        
        // 连接到视频 socket (第一个 socket)
        let mut retry_count = 0;
        let video_stream = loop {
            match TcpStream::connect(format!("127.0.0.1:{}", video_port)).await {
                Ok(stream) => break stream,
                Err(e) => {
                    retry_count += 1;
                    if retry_count > 10 {
                        return Err(VmError::ScrcpyError(format!("Failed to connect to video socket after {} retries: {}", retry_count, e)));
                    }
                    tracing::warn!("Retry {} connecting to video socket: {}", retry_count, e);
                    tokio::time::sleep(tokio::time::Duration::from_millis(500)).await;
                }
            }
        };
        
        tracing::info!("Connected to video socket");
        
        // 连接到控制 socket (第二个 socket)
        let control_stream = TcpStream::connect(format!("127.0.0.1:{}", control_port))
            .await
            .map_err(|e| VmError::ScrcpyError(format!("Failed to connect to control socket: {}", e)))?;
        
        tracing::info!("Connected to control socket");
        
        Ok((video_stream, control_stream))
    }

    /// 读取设备元数据 (scrcpy 协议)
    /// 
    /// 协议格式 (tunnel_forward=true, send_device_meta=true, send_codec_meta=true):
    /// 1. 1 字节 dummy byte (仅在 forward 模式)
    /// 2. 64 字节设备名 (null-terminated)
    /// 3. 4 字节 codec ID (big-endian)
    /// 4. 4 字节 width (big-endian)
    /// 5. 4 字节 height (big-endian)
    async fn read_metadata(&self, stream: &mut TcpStream) -> Result<DeviceMetadata, VmError> {
        // 1. 读取 dummy byte (tunnel_forward=true 时发送)
        let mut dummy = [0u8; 1];
        stream.read_exact(&mut dummy).await
            .map_err(|e| VmError::ScrcpyError(format!("Failed to read dummy byte: {}", e)))?;
        tracing::debug!("Read dummy byte: {:02x}", dummy[0]);
        
        // 2. 读取设备名 (64 字节, null-terminated)
        let mut device_name_buf = [0u8; 64];
        stream.read_exact(&mut device_name_buf).await
            .map_err(|e| VmError::ScrcpyError(format!("Failed to read device name: {}", e)))?;
        
        let device_name = String::from_utf8_lossy(&device_name_buf)
            .trim_end_matches('\0')
            .to_string();
        tracing::info!("Device name: {}", device_name);
        
        // 3. 读取 codec ID (4 字节, big-endian)
        let mut codec_buf = [0u8; 4];
        stream.read_exact(&mut codec_buf).await
            .map_err(|e| VmError::ScrcpyError(format!("Failed to read codec: {}", e)))?;
        let codec_id = u32::from_be_bytes(codec_buf);
        let codec = VideoCodecId::from_u32(codec_id)
            .ok_or_else(|| VmError::ScrcpyError(format!("Unknown codec: {:08x}", codec_id)))?;
        tracing::info!("Codec: {:?} ({:08x})", codec, codec_id);
        
        // 4. 读取 width (4 字节, big-endian)
        let mut width_buf = [0u8; 4];
        stream.read_exact(&mut width_buf).await
            .map_err(|e| VmError::ScrcpyError(format!("Failed to read width: {}", e)))?;
        let width = u32::from_be_bytes(width_buf);
        
        // 5. 读取 height (4 字节, big-endian)
        let mut height_buf = [0u8; 4];
        stream.read_exact(&mut height_buf).await
            .map_err(|e| VmError::ScrcpyError(format!("Failed to read height: {}", e)))?;
        let height = u32::from_be_bytes(height_buf);
        
        tracing::info!("Video size: {}x{}", width, height);
        
        Ok(DeviceMetadata {
            device_name,
            codec,
            width,
            height,
        })
    }

    /// Handle WebSocket connection for Android device streaming
    pub async fn handle_websocket(&self, ws: WebSocket) -> Result<(), VmError> {
        tracing::info!("Starting scrcpy proxy for device: {}", self.device_serial);
        
        let (mut ws_sender, mut ws_receiver) = ws.split();
        
        // 生成唯一的 scid
        let scid = Self::generate_scid();
        tracing::info!("Generated scid: {:08x}", scid);
        
        // 1. 推送 scrcpy-server
        if let Err(e) = self.push_server().await {
            let error_msg = serde_json::json!({
                "type": "error",
                "message": e.to_string()
            });
            let _ = ws_sender.send(Message::Text(error_msg.to_string())).await;
            return Err(e);
        }
        
        // 2. 启动 scrcpy-server
        let mut server_process = match self.start_server(scid).await {
            Ok(p) => p,
            Err(e) => {
                let error_msg = serde_json::json!({
                    "type": "error",
                    "message": e.to_string()
                });
                let _ = ws_sender.send(Message::Text(error_msg.to_string())).await;
                return Err(e);
            }
        };
        
        // 3. 建立端口转发并连接
        let (mut video_stream, mut control_stream) = match self.setup_and_connect(scid).await {
            Ok(streams) => streams,
            Err(e) => {
                let _ = server_process.kill().await;
                let error_msg = serde_json::json!({
                    "type": "error",
                    "message": e.to_string()
                });
                let _ = ws_sender.send(Message::Text(error_msg.to_string())).await;
                return Err(e);
            }
        };
        
        // 4. 读取元数据
        let metadata = match self.read_metadata(&mut video_stream).await {
            Ok(m) => m,
            Err(e) => {
                let _ = server_process.kill().await;
                let error_msg = serde_json::json!({
                    "type": "error",
                    "message": e.to_string()
                });
                let _ = ws_sender.send(Message::Text(error_msg.to_string())).await;
                return Err(e);
            }
        };
        
        // 发送设备信息到前端
        let info_msg = serde_json::json!({
            "type": "info",
            "device": metadata.device_name,
            "codec": metadata.codec.as_str(),
            "width": metadata.width,
            "height": metadata.height,
        });
        if ws_sender.send(Message::Text(info_msg.to_string())).await.is_err() {
            let _ = server_process.kill().await;
            return Err(VmError::ScrcpyError("Failed to send device info".to_string()));
        }
        
        let stop_flag = Arc::new(AtomicBool::new(false));
        let stop_flag_video = stop_flag.clone();
        let stop_flag_control = stop_flag.clone();
        
        let screen_width = metadata.width;
        let screen_height = metadata.height;
        
        // 任务1: 读取视频流并转发到 WebSocket
        // 
        // scrcpy 帧格式 (send_frame_meta=true):
        // - 8 字节: flags (2 bits) + PTS (62 bits), big-endian
        //   - bit 63: config packet flag
        //   - bit 62: key frame flag
        //   - bits 0-61: PTS in microseconds
        // - 4 字节: packet size, big-endian
        // - N 字节: H.264 数据
        let video_task = tokio::spawn(async move {
            let mut reader = BufReader::new(video_stream);
            let mut frame_count = 0u64;
            
            loop {
                if stop_flag_video.load(Ordering::Relaxed) {
                    break;
                }
                
                // 读取帧头 (12 字节)
                let mut header = [0u8; 12];
                if reader.read_exact(&mut header).await.is_err() {
                    tracing::info!("Video stream ended");
                    break;
                }
                
                // 解析 PTS 和 flags
                let pts_and_flags = u64::from_be_bytes(header[0..8].try_into().unwrap());
                let is_config = (pts_and_flags >> 63) & 1 == 1;
                let is_keyframe = (pts_and_flags >> 62) & 1 == 1;
                let pts = pts_and_flags & 0x3FFFFFFFFFFFFFFF; // 62 bits
                
                // 解析 packet size
                let packet_size = u32::from_be_bytes(header[8..12].try_into().unwrap()) as usize;
                
                // 检查 packet size 是否合理
                if packet_size == 0 || packet_size > 10 * 1024 * 1024 {
                    tracing::warn!("Invalid packet size: {}", packet_size);
                    continue;
                }
                
                // 读取 H.264 数据
                let mut data = vec![0u8; packet_size];
                if reader.read_exact(&mut data).await.is_err() {
                    tracing::info!("Video stream ended (data)");
                    break;
                }
                
                frame_count += 1;
                
                if frame_count <= 5 || frame_count % 100 == 0 {
                    tracing::debug!(
                        "Frame {}: pts={}, size={}, config={}, keyframe={}",
                        frame_count, pts, packet_size, is_config, is_keyframe
                    );
                }
                
                // 构建发送给前端的消息
                // 格式: [8 字节 PTS+flags] [4 字节 size] [H.264 数据]
                // 前端需要解析这个格式
                let mut message = Vec::with_capacity(12 + packet_size);
                message.extend_from_slice(&header);
                message.extend_from_slice(&data);
                
                // 发送到 WebSocket
                if ws_sender.send(Message::Binary(message)).await.is_err() {
                    tracing::info!("WebSocket send failed, stopping");
                    break;
                }
            }
            
            tracing::info!("Video task finished, sent {} frames", frame_count);
        });

        // 任务2: 处理控制消息
        let control_task = tokio::spawn(async move {
            while let Some(msg) = ws_receiver.next().await {
                match msg {
                    Ok(Message::Text(text)) => {
                        if let Err(e) = handle_control_message(&mut control_stream, &text, screen_width, screen_height).await {
                            tracing::error!("Failed to handle control message: {}", e);
                        }
                    }
                    Ok(Message::Binary(data)) => {
                        // 直接转发二进制控制消息
                        if control_stream.write_all(&data).await.is_err() {
                            tracing::error!("Failed to write control message");
                            break;
                        }
                    }
                    Ok(Message::Close(_)) => {
                        tracing::info!("WebSocket closed by client");
                        stop_flag_control.store(true, Ordering::Relaxed);
                        break;
                    }
                    Err(e) => {
                        tracing::error!("WebSocket error: {}", e);
                        stop_flag_control.store(true, Ordering::Relaxed);
                        break;
                    }
                    _ => {}
                }
            }
        });

        tokio::select! {
            _ = video_task => {
                tracing::debug!("Video task finished");
            }
            _ = control_task => {
                tracing::debug!("Control task finished");
            }
        }
        
        stop_flag.store(true, Ordering::Relaxed);
        
        // 清理
        let _ = server_process.kill().await;
        
        // 移除端口转发
        let adb_path = get_adb_path();
        let _ = Command::new(&adb_path)
            .args(["-s", &self.device_serial, "forward", "--remove", "tcp:27183"])
            .output()
            .await;
        let _ = Command::new(&adb_path)
            .args(["-s", &self.device_serial, "forward", "--remove", "tcp:27184"])
            .output()
            .await;

        tracing::info!("Scrcpy proxy session ended");
        Ok(())
    }
}

/// 处理控制消息 (JSON 格式转 scrcpy 二进制协议)
/// 
/// scrcpy 控制消息格式参考:
/// https://github.com/Genymobile/scrcpy/blob/master/app/tests/test_control_msg_serialize.c
async fn handle_control_message(stream: &mut TcpStream, event_json: &str, screen_width: u32, screen_height: u32) -> Result<(), VmError> {
    let event: serde_json::Value = serde_json::from_str(event_json)
        .map_err(|e| VmError::ScrcpyError(format!("Invalid event JSON: {}", e)))?;
    
    let event_type = event.get("type")
        .and_then(|v| v.as_str())
        .ok_or_else(|| VmError::ScrcpyError("Missing event type".to_string()))?;
    
    let message = match event_type {
        "inject_touch" | "touch" | "tap" => {
            // scrcpy 触控消息格式 (SC_CONTROL_MSG_TYPE_INJECT_TOUCH_EVENT = 2):
            // - 1 字节: 消息类型 (2)
            // - 1 字节: action (0 = down, 1 = up, 2 = move)
            // - 8 字节: pointer id (big-endian, i64)
            // - 4 字节: x position (big-endian, i32)
            // - 4 字节: y position (big-endian, i32)
            // - 2 字节: screen width (big-endian, u16)
            // - 2 字节: screen height (big-endian, u16)
            // - 2 字节: pressure (big-endian, u16, 0-65535, 0xFFFF = 1.0)
            // - 4 字节: action button (big-endian, i32)
            // - 4 字节: buttons (big-endian, i32)
            
            let action = event.get("action").and_then(|v| v.as_u64()).unwrap_or(0) as u8;
            let pointer_id = event.get("pointerId").and_then(|v| v.as_i64()).unwrap_or(-1);
            let x = event.get("x").and_then(|v| v.as_i64()).unwrap_or(0) as i32;
            let y = event.get("y").and_then(|v| v.as_i64()).unwrap_or(0) as i32;
            let width = event.get("screenWidth").and_then(|v| v.as_u64()).unwrap_or(screen_width as u64) as u16;
            let height = event.get("screenHeight").and_then(|v| v.as_u64()).unwrap_or(screen_height as u64) as u16;
            let pressure = if action == 1 { 0u16 } else { 0xFFFF }; // 1.0 for down/move, 0 for up
            
            let mut msg = Vec::with_capacity(32);
            msg.push(2); // SC_CONTROL_MSG_TYPE_INJECT_TOUCH_EVENT
            msg.push(action);
            msg.extend_from_slice(&pointer_id.to_be_bytes());
            msg.extend_from_slice(&x.to_be_bytes());
            msg.extend_from_slice(&y.to_be_bytes());
            msg.extend_from_slice(&width.to_be_bytes());
            msg.extend_from_slice(&height.to_be_bytes());
            msg.extend_from_slice(&pressure.to_be_bytes());
            msg.extend_from_slice(&0i32.to_be_bytes()); // action button
            msg.extend_from_slice(&0i32.to_be_bytes()); // buttons
            
            tracing::debug!("Touch event: action={}, x={}, y={}, pointer_id={}", action, x, y, pointer_id);
            msg
        }
        "inject_keycode" | "key" => {
            // scrcpy 按键消息格式 (SC_CONTROL_MSG_TYPE_INJECT_KEYCODE = 0):
            // - 1 字节: 消息类型 (0)
            // - 1 字节: action (0 = down, 1 = up)
            // - 4 字节: keycode (big-endian, i32)
            // - 4 字节: repeat (big-endian, i32)
            // - 4 字节: metastate (big-endian, i32)
            
            let action = event.get("action").and_then(|v| v.as_u64()).unwrap_or(0) as u8;
            let keycode = event.get("keycode").and_then(|v| v.as_i64()).unwrap_or(0) as i32;
            let repeat = event.get("repeat").and_then(|v| v.as_i64()).unwrap_or(0) as i32;
            let metastate = event.get("metastate").and_then(|v| v.as_i64()).unwrap_or(0) as i32;
            
            let mut msg = Vec::with_capacity(14);
            msg.push(0); // SC_CONTROL_MSG_TYPE_INJECT_KEYCODE
            msg.push(action);
            msg.extend_from_slice(&keycode.to_be_bytes());
            msg.extend_from_slice(&repeat.to_be_bytes());
            msg.extend_from_slice(&metastate.to_be_bytes());
            
            tracing::debug!("Key event: action={}, keycode={}", action, keycode);
            msg
        }
        "inject_text" | "text" => {
            // scrcpy 文本消息格式 (SC_CONTROL_MSG_TYPE_INJECT_TEXT = 1):
            // - 1 字节: 消息类型 (1)
            // - 4 字节: text length (big-endian, u32)
            // - N 字节: text (UTF-8)
            
            let text = event.get("text").and_then(|v| v.as_str()).unwrap_or("");
            let text_bytes = text.as_bytes();
            
            let mut msg = Vec::with_capacity(5 + text_bytes.len());
            msg.push(1); // SC_CONTROL_MSG_TYPE_INJECT_TEXT
            msg.extend_from_slice(&(text_bytes.len() as u32).to_be_bytes());
            msg.extend_from_slice(text_bytes);
            
            tracing::debug!("Text event: {}", text);
            msg
        }
        "back_or_screen_on" => {
            // SC_CONTROL_MSG_TYPE_BACK_OR_SCREEN_ON = 4
            let action = event.get("action").and_then(|v| v.as_u64()).unwrap_or(0) as u8;
            vec![4, action]
        }
        "expand_notification_panel" => {
            // SC_CONTROL_MSG_TYPE_EXPAND_NOTIFICATION_PANEL = 5
            vec![5]
        }
        "expand_settings_panel" => {
            // SC_CONTROL_MSG_TYPE_EXPAND_SETTINGS_PANEL = 6
            vec![6]
        }
        "collapse_panels" => {
            // SC_CONTROL_MSG_TYPE_COLLAPSE_PANELS = 7
            vec![7]
        }
        "get_clipboard" => {
            // SC_CONTROL_MSG_TYPE_GET_CLIPBOARD = 8
            // - 1 字节: 消息类型 (8)
            // - 1 字节: copy key (0 = none, 1 = copy, 2 = cut)
            let copy_key = event.get("copyKey").and_then(|v| v.as_u64()).unwrap_or(0) as u8;
            vec![8, copy_key]
        }
        "set_clipboard" => {
            // SC_CONTROL_MSG_TYPE_SET_CLIPBOARD = 9
            // - 1 字节: 消息类型 (9)
            // - 8 字节: sequence (big-endian, u64)
            // - 1 字节: paste (bool)
            // - 4 字节: text length (big-endian, u32)
            // - N 字节: text (UTF-8)
            let sequence = event.get("sequence").and_then(|v| v.as_u64()).unwrap_or(0);
            let paste = event.get("paste").and_then(|v| v.as_bool()).unwrap_or(false);
            let text = event.get("text").and_then(|v| v.as_str()).unwrap_or("");
            let text_bytes = text.as_bytes();
            
            let mut msg = Vec::with_capacity(14 + text_bytes.len());
            msg.push(9);
            msg.extend_from_slice(&sequence.to_be_bytes());
            msg.push(if paste { 1 } else { 0 });
            msg.extend_from_slice(&(text_bytes.len() as u32).to_be_bytes());
            msg.extend_from_slice(text_bytes);
            msg
        }
        "set_screen_power_mode" => {
            // SC_CONTROL_MSG_TYPE_SET_SCREEN_POWER_MODE = 10
            let mode = event.get("mode").and_then(|v| v.as_u64()).unwrap_or(2) as u8; // 2 = normal
            vec![10, mode]
        }
        "rotate_device" => {
            // SC_CONTROL_MSG_TYPE_ROTATE_DEVICE = 11
            vec![11]
        }
        _ => {
            tracing::warn!("Unknown control event type: {}", event_type);
            return Ok(());
        }
    };
    
    stream.write_all(&message).await
        .map_err(|e| VmError::ScrcpyError(format!("Failed to send control message: {}", e)))?;
    
    Ok(())
}

/// 检查 scrcpy 是否可用
pub async fn check_scrcpy_available() -> bool {
    let server_path = get_scrcpy_server_path();
    std::path::Path::new(&server_path).exists()
}

/// 获取已连接的 Android 设备列表
pub async fn list_android_devices() -> Result<Vec<String>, VmError> {
    let adb_path = get_adb_path();
    let output = Command::new(&adb_path)
        .args(["devices", "-l"])
        .output()
        .await
        .map_err(|e| VmError::ScrcpyError(format!("Failed to run adb devices: {}", e)))?;
    
    if !output.status.success() {
        return Err(VmError::ScrcpyError("adb devices failed".to_string()));
    }
    
    let stdout = String::from_utf8_lossy(&output.stdout);
    let devices: Vec<String> = stdout
        .lines()
        .skip(1)
        .filter_map(|line| {
            let parts: Vec<&str> = line.split_whitespace().collect();
            if parts.len() >= 2 && parts[1] == "device" {
                Some(parts[0].to_string())
            } else {
                None
            }
        })
        .collect();
    
    Ok(devices)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_scrcpy_proxy_creation() {
        let proxy = ScrcpyProxy::new("emulator-5554");
        assert_eq!(proxy.device_serial, "emulator-5554");
    }

    #[test]
    fn test_video_codec_id() {
        assert_eq!(VideoCodecId::from_u32(0x68323634), Some(VideoCodecId::H264));
        assert_eq!(VideoCodecId::H264.as_str(), "h264");
    }

    #[tokio::test]
    async fn test_list_devices() {
        let result = list_android_devices().await;
        println!("Devices: {:?}", result);
    }
}
