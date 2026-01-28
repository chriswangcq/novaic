use std::path::PathBuf;
use std::process::{Child, Command, Stdio};
use tokio::sync::Mutex;
use tokio::time::{sleep, Duration};
use std::net::TcpStream;

/// VM 配置
#[derive(Clone, Debug, serde::Serialize, serde::Deserialize)]
pub struct VmConfig {
    pub memory: String,      // 内存大小, e.g., "4G"
    pub cpus: u32,           // CPU 核心数
    pub vnc_port: u16,       // VNC 端口 (VM 内部使用，通过 QEMU 转发)
    pub agent_port: u16,     // Agent API 端口 (宿主机)
    pub websocket_port: u16, // WebSocket 端口 (VM 内的 websockify 提供)
    pub ssh_port: u16,       // SSH 端口
    pub image_path: Option<String>,  // 自定义镜像路径 (可选)
    // VSOCK 配置 (替代 executor_port)
    pub vsock_cid: u32,      // VSOCK Context ID (3+, 0/1/2 是保留值)
    pub mcp_vsock_port: u32, // VSOCK 端口 (VM 内 MCP Server 监听)
}

impl Default for VmConfig {
    fn default() -> Self {
        Self {
            memory: "4096".to_string(),
            cpus: 4,
            vnc_port: 5900,      // VNC 端口 (宿主机 5900 → VM 5900)
            agent_port: 9000,    // Agent API 端口 (宿主机本地)
            websocket_port: 6080,// WebSocket 端口 (宿主机 6080 → VM 6080)
            ssh_port: 2222,      // SSH 端口 (宿主机 2222 → VM 22)
            image_path: None,    // 使用默认镜像
            // VSOCK 配置
            vsock_cid: 3,        // 默认 CID=3 (第一个 VM)
            mcp_vsock_port: 8080,// MCP Server 在 VSOCK 上的端口
        }
    }
}

/// VM Manager - handles QEMU virtual machine lifecycle
/// websockify 运行在 VM 内部，通过 QEMU 端口转发访问
pub struct VmManager {
    qemu_process: Mutex<Option<Child>>,
    vm_dir: PathBuf,        // VM 目录 (包含镜像、固件等)
    config: Mutex<VmConfig>,
    current_agent_id: Mutex<Option<String>>,
}

impl VmManager {
    pub fn new(vm_dir: PathBuf) -> Self {
        Self {
            qemu_process: Mutex::new(None),
            vm_dir,
            config: Mutex::new(VmConfig::default()),
            current_agent_id: Mutex::new(None),
        }
    }

    /// Update VM configuration (for switching agents)
    pub async fn set_config(&self, config: VmConfig, agent_id: Option<String>) {
        let mut cfg = self.config.lock().await;
        *cfg = config;
        let mut aid = self.current_agent_id.lock().await;
        *aid = agent_id;
    }

    /// Get current configuration
    pub async fn get_config(&self) -> VmConfig {
        self.config.lock().await.clone()
    }

    /// Get current agent ID
    pub async fn get_current_agent_id(&self) -> Option<String> {
        self.current_agent_id.lock().await.clone()
    }

    #[allow(dead_code)]
    pub fn with_config(self, _config: VmConfig) -> Self {
        // Deprecated: use set_config instead
        self
    }

    /// 获取镜像路径
    fn get_image_path(&self, config: &VmConfig) -> PathBuf {
        // 如果配置了自定义镜像路径，使用它
        if let Some(ref path) = config.image_path {
            let custom_path = PathBuf::from(path);
            if custom_path.exists() {
                return custom_path;
            }
        }
        
        // 优先使用 novaic-vm.qcow2，其次是 ubuntu-linux2mcp.qcow2，最后是 nb-cc-vm.qcow2
        let novaic_image = self.vm_dir.join("images").join("novaic-vm.qcow2");
        if novaic_image.exists() {
            return novaic_image;
        }
        let ubuntu_image = self.vm_dir.join("images").join("ubuntu-linux2mcp.qcow2");
        if ubuntu_image.exists() {
            return ubuntu_image;
        }
        self.vm_dir.join("images").join("nb-cc-vm.qcow2")
    }

    /// 获取固件路径 (仅 ARM64 需要)
    fn get_firmware_path(&self) -> PathBuf {
        self.vm_dir.join("firmware").join("QEMU_EFI.fd")
    }

    /// 获取 UEFI 变量路径 (仅 ARM64 需要)
    fn get_uefi_vars_path(&self) -> PathBuf {
        // 优先使用 Ubuntu 专用的 UEFI 变量文件
        let ubuntu_vars = self.vm_dir.join("firmware").join("QEMU_VARS_ubuntu.fd");
        if ubuntu_vars.exists() {
            ubuntu_vars
        } else {
            self.vm_dir.join("firmware").join("QEMU_VARS.fd")
        }
    }

    /// Start the virtual machine
    pub async fn start(&self) -> Result<(), String> {
        let config = self.config.lock().await.clone();
        let image_path = self.get_image_path(&config);
        
        // 检查镜像文件是否存在
        if !image_path.exists() {
            return Err(format!(
                "VM image not found: {}. Please build the VM image first.",
                image_path.display()
            ));
        }

        let mut qemu_guard = self.qemu_process.lock().await;
        
        if qemu_guard.is_some() {
            println!("[VM] VM process already tracked, skipping start");
            return Ok(());
        }

        // 检查 websockify 端口是否被占用 - 用于检测 VM 是否在运行
        // (MCP 现在通过 VSOCK 通信，不再使用端口转发)
        if TcpStream::connect(format!("127.0.0.1:{}", config.websocket_port)).is_ok() {
            println!("[VM] VM already running (detected via websockify port {}), skipping start", config.websocket_port);
            // 等待 websockify 就绪
            drop(qemu_guard);
            self.wait_for_websockify().await?;
            return Ok(());
        }
        
        // 确保端口可用
        self.check_port_available(config.vnc_port)?;
        self.check_port_available(config.websocket_port)?;

        // 根据操作系统和架构选择 QEMU 命令和参数
        let qemu_cmd = self.get_qemu_command();
        let qemu_args = self.build_qemu_args(&config, &image_path)?;

        println!("[VM] Starting QEMU: {} {:?}", qemu_cmd, qemu_args);

        let child = Command::new(&qemu_cmd)
            .args(&qemu_args)
            .current_dir(&self.vm_dir)  // 设置工作目录为 VM 目录
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .spawn()
            .map_err(|e| format!("Failed to start QEMU: {}. Make sure QEMU is installed.", e))?;

        *qemu_guard = Some(child);
        drop(qemu_guard);

        // 等待 QEMU 启动
        println!("[VM] Waiting for QEMU to start...");
        sleep(Duration::from_secs(5)).await;

        // websockify 运行在 VM 内部，通过 QEMU 端口转发自动可用
        // 等待 websockify 端口可用
        self.wait_for_websockify().await?;

        // 等待 Executor 可用（Agent 现在在宿主机运行）
        self.wait_for_executor().await?;

        println!("[VM] Virtual machine started successfully");
        Ok(())
    }

    /// 等待 VM 内的 websockify 服务可用
    async fn wait_for_websockify(&self) -> Result<(), String> {
        let config = self.config.lock().await.clone();
        let start = std::time::Instant::now();
        println!("[VM] Waiting for websockify service (port {})...", config.websocket_port);
        
        let max_attempts = 30;
        for attempt in 1..=max_attempts {
            if TcpStream::connect(format!("127.0.0.1:{}", config.websocket_port)).is_ok() {
                println!("[VM] Websockify TCP ready after {:.1}s (attempt {})", start.elapsed().as_secs_f32(), attempt);
                return Ok(());
            }
            if attempt % 5 == 0 {
                println!("[VM] Still waiting for websockify... {:.1}s (attempt {})", start.elapsed().as_secs_f32(), attempt);
            }
            if attempt < max_attempts {
                sleep(Duration::from_secs(2)).await;
            }
        }

        // websockify 未能启动，但继续运行
        println!("[VM] Warning: Websockify not responding after {:.1}s", start.elapsed().as_secs_f32());
        Ok(())
    }

    /// 等待 MCP Server 可用（在 VM 内运行，通过 VSOCK 通信）
    /// 注意：实际的 VSOCK 连接由 Gateway 处理，这里只等待一个合理的启动时间
    async fn wait_for_executor(&self) -> Result<(), String> {
        let config = self.config.lock().await.clone();
        let start = std::time::Instant::now();
        println!("[VM] Waiting for MCP Server (VSOCK CID={}, port={})...", 
            config.vsock_cid, config.mcp_vsock_port);
        
        // VM 启动后，给 systemd 服务一些时间启动
        // VSOCK 连接由 Gateway 侧的 Python 代码处理
        // 这里只等待一个合理的时间让 VM 内的服务启动
        let wait_secs = 15;
        println!("[VM] Waiting {}s for VM services to start...", wait_secs);
        sleep(Duration::from_secs(wait_secs)).await;
        
        println!("[VM] MCP Server should be ready (elapsed: {:.1}s)", start.elapsed().as_secs_f32());
        println!("[VM] Note: MCP communication uses VSOCK, health check done by Gateway");
        Ok(())
    }

    /// 检查 MCP Server 健康状态
    /// 注意：MCP 现在通过 VSOCK 通信，健康检查由 Gateway 侧执行
    /// 这个方法保留用于状态查询，返回 false 表示需要通过 VSOCK 检查
    #[allow(dead_code)]
    async fn check_executor_health(&self) -> Result<bool, String> {
        // MCP Server 现在通过 VSOCK 通信，不再使用 TCP 端口
        // 健康检查应该由 Gateway 通过 VSOCK 执行
        // 这里简单返回 true，表示"假设健康"
        // 实际健康状态由 Gateway 的 VSOCK 连接决定
        Ok(true)
    }
    
    /// 检查宿主机 Agent 健康状态（用于状态查询）
    async fn check_agent_health(&self) -> Result<bool, String> {
        let config = self.config.lock().await.clone();
        let url = format!("http://127.0.0.1:{}/api/health", config.agent_port);
        
        // 使用本地服务客户端（不走代理）
        let client = crate::http_client::local_client()
            .timeout(Duration::from_secs(2))
            .build()
            .map_err(|e| e.to_string())?;

        match client.get(&url).send().await {
            Ok(response) => Ok(response.status().is_success()),
            Err(_) => Ok(false),
        }
    }

    /// Stop the virtual machine
    pub async fn stop(&self) -> Result<(), String> {
        println!("[VM] Stopping virtual machine...");

        // 停止 QEMU (websockify 在 VM 内，会随 VM 一起停止)
        let mut qemu_guard = self.qemu_process.lock().await;
        if let Some(mut child) = qemu_guard.take() {
            // 尝试优雅关闭
            let _ = child.kill();
            let _ = child.wait();
        }

        println!("[VM] Virtual machine stopped");
        Ok(())
    }

    /// Check if VM is running
    pub async fn is_running(&self) -> bool {
        let qemu_guard = self.qemu_process.lock().await;
        if qemu_guard.is_none() {
            return false;
        }

        let config = self.config.lock().await.clone();
        // 检查 Agent 端口是否可连接
        TcpStream::connect(format!("127.0.0.1:{}", config.agent_port)).is_ok()
    }

    /// Get VM status
    pub async fn get_status(&self) -> VmStatus {
        let config = self.config.lock().await.clone();
        let agent_id = self.current_agent_id.lock().await.clone();
        let is_running = self.is_running().await;
        let agent_healthy = self.check_agent_health().await.unwrap_or(false);
        
        // 检查 websockify 端口是否可用 (在 VM 内运行)
        let websockify_running = TcpStream::connect(
            format!("127.0.0.1:{}", config.websocket_port)
        ).is_ok();

        VmStatus {
            running: is_running || websockify_running,  // 如果 websockify 运行，则 VM 在运行
            agent_healthy,
            mcp_healthy: websockify_running,  // 假设 MCP 与 VM 一起运行
            websockify_running,
            vnc_port: config.vnc_port,
            agent_port: config.agent_port,
            vsock_cid: config.vsock_cid,
            mcp_vsock_port: config.mcp_vsock_port,
            websocket_port: config.websocket_port,
            vnc_url: format!("ws://localhost:{}/websockify", config.websocket_port),
            agent_url: format!("http://localhost:{}", config.agent_port),
            agent_id,
        }
    }

    /// Get VSOCK CID for MCP Server
    pub async fn get_vsock_cid(&self) -> u32 {
        let config = self.config.lock().await;
        config.vsock_cid
    }
    
    /// Get VSOCK port for MCP Server
    pub async fn get_mcp_vsock_port(&self) -> u32 {
        let config = self.config.lock().await;
        config.mcp_vsock_port
    }
    
    /// Get MCP connection info (VSOCK)
    pub async fn get_mcp_info(&self) -> (u32, u32) {
        let config = self.config.lock().await;
        (config.vsock_cid, config.mcp_vsock_port)
    }

    /// Get VNC WebSocket URL (for noVNC)
    pub async fn get_vnc_url(&self) -> String {
        let config = self.config.lock().await;
        format!("ws://localhost:{}/websockify", config.websocket_port)
    }

    /// Get Agent API URL
    pub async fn get_agent_url(&self) -> String {
        let config = self.config.lock().await;
        format!("http://localhost:{}", config.agent_port)
    }

    /// 检查端口是否可用
    fn check_port_available(&self, port: u16) -> Result<(), String> {
        match TcpStream::connect(format!("127.0.0.1:{}", port)) {
            Ok(_) => Err(format!("Port {} is already in use", port)),
            Err(_) => Ok(()),
        }
    }

    /// 检测是否是 ARM64 架构
    fn is_arm64() -> bool {
        #[cfg(target_arch = "aarch64")]
        {
            true
        }
        #[cfg(not(target_arch = "aarch64"))]
        {
            false
        }
    }

    /// 获取 QEMU 命令
    fn get_qemu_command(&self) -> String {
        // macOS 上使用 Homebrew 安装的 QEMU 完整路径
        // 从 Finder 启动应用时 PATH 不包含 /opt/homebrew/bin
        if cfg!(target_os = "macos") {
            if Self::is_arm64() {
                // Apple Silicon Mac
                "/opt/homebrew/bin/qemu-system-aarch64".to_string()
            } else {
                // Intel Mac
                "/usr/local/bin/qemu-system-x86_64".to_string()
            }
        } else {
            // Linux 等系统使用系统路径
            if Self::is_arm64() {
                "qemu-system-aarch64".to_string()
            } else {
                "qemu-system-x86_64".to_string()
            }
        }
    }

    /// 获取 cloud-init ISO 路径
    fn get_seed_iso_path(&self) -> PathBuf {
        self.vm_dir.join("iso").join("cloud-init-seed.iso")
    }

    /// 构建 QEMU 参数
    fn build_qemu_args(&self, config: &VmConfig, image_path: &PathBuf) -> Result<Vec<String>, String> {
        // 网络端口转发 (简化：MCP 通过 VSOCK，不需要端口转发)
        // - vnc: VNC 端口 (VM 5900 → 宿主机 5900)
        // - ws: websockify (VM 6080 → 宿主机 6080)
        // - ssh: SSH 访问 (VM 22 → 宿主机 2222)
        let port_forward = format!(
            "hostfwd=tcp::{vnc}-:{vnc},hostfwd=tcp::{ws}-:{ws},hostfwd=tcp::{ssh}-:22",
            vnc = config.vnc_port,
            ws = config.websocket_port,
            ssh = config.ssh_port,
        );

        if Self::is_arm64() {
            // ARM64 (Apple Silicon) 配置
            let firmware_path = self.get_firmware_path();
            let uefi_vars_path = self.get_uefi_vars_path();
            let seed_iso_path = self.get_seed_iso_path();

            if !firmware_path.exists() {
                return Err(format!("UEFI firmware not found: {}", firmware_path.display()));
            }
            if !uefi_vars_path.exists() {
                return Err(format!("UEFI vars not found: {}", uefi_vars_path.display()));
            }

            let mut args = vec![
                "-name".to_string(), "novaic-vm".to_string(),
                "-M".to_string(), "virt,highmem=on".to_string(),
                "-cpu".to_string(), "host".to_string(),
                "-accel".to_string(), "hvf".to_string(),
                "-m".to_string(), config.memory.clone(),
                "-smp".to_string(), config.cpus.to_string(),
                // UEFI 固件
                "-drive".to_string(), format!("if=pflash,format=raw,file={},readonly=on", firmware_path.display()),
                "-drive".to_string(), format!("if=pflash,format=raw,file={}", uefi_vars_path.display()),
                // 系统盘 (virtio)
                "-drive".to_string(), format!("if=none,id=hd0,format=qcow2,file={}", image_path.display()),
                "-device".to_string(), "virtio-blk-pci,drive=hd0,bootindex=1".to_string(),
                // 网络
                "-device".to_string(), "virtio-net-pci,netdev=net0".to_string(),
                "-netdev".to_string(), format!("user,id=net0,{}", port_forward),
                // virtio-serial 用于 MCP 通信 (跨平台，替代 VSOCK)
                "-device".to_string(), "virtio-serial-pci".to_string(),
                "-chardev".to_string(), format!("socket,id=mcp,path=/tmp/novaic-mcp-{}.sock,server=on,wait=off", config.vsock_cid),
                "-device".to_string(), "virtserialport,chardev=mcp,name=mcp".to_string(),
                // 显示
                "-device".to_string(), "virtio-gpu-pci".to_string(),
                // USB 输入
                "-device".to_string(), "usb-ehci".to_string(),
                "-device".to_string(), "usb-kbd".to_string(),
                "-device".to_string(), "usb-mouse".to_string(),
                // 无窗口运行
                "-display".to_string(), "none".to_string(),
            ];

            // 如果存在 cloud-init ISO，添加它
            if seed_iso_path.exists() {
                args.extend(vec![
                    "-device".to_string(), "virtio-scsi-pci,id=scsi0".to_string(),
                    "-drive".to_string(), format!("if=none,id=cd0,format=raw,file={},readonly=on", seed_iso_path.display()),
                    "-device".to_string(), "scsi-cd,drive=cd0,bus=scsi0.0".to_string(),
                ]);
            }

            Ok(args)
        } else {
            // x86_64 配置
            let mut args = vec![
                "-name".to_string(), "novaic-vm".to_string(),
            ];
            
            // 添加硬件加速 (关键！没有加速会非常慢)
            // macOS: hvf, Linux: kvm, Windows: whpx 或 hax
            #[cfg(target_os = "macos")]
            {
                args.extend(vec!["-accel".to_string(), "hvf".to_string()]);
            }
            #[cfg(target_os = "linux")]
            {
                args.extend(vec!["-enable-kvm".to_string()]);
            }
            #[cfg(target_os = "windows")]
            {
                // Windows: 优先尝试 WHPX (Hyper-V), 需要用户开启 Windows Hypervisor Platform
                args.extend(vec!["-accel".to_string(), "whpx".to_string()]);
            }
            
            args.extend(vec![
                "-cpu".to_string(), "host".to_string(),
                "-m".to_string(), config.memory.clone(),
                "-smp".to_string(), config.cpus.to_string(),
                "-hda".to_string(), image_path.to_str().unwrap().to_string(),
                "-boot".to_string(), "c".to_string(),
                "-net".to_string(), "nic".to_string(),
                "-net".to_string(), format!("user,{}", port_forward),
                // virtio-serial 用于 MCP 通信 (跨平台)
                "-device".to_string(), "virtio-serial-pci".to_string(),
                "-chardev".to_string(), format!("socket,id=mcp,path=/tmp/novaic-mcp-{}.sock,server=on,wait=off", config.vsock_cid),
                "-device".to_string(), "virtserialport,chardev=mcp,name=mcp".to_string(),
                "-display".to_string(), "none".to_string(),
            ]);
            
            Ok(args)
        }
    }
}

impl Default for VmManager {
    fn default() -> Self {
        // 默认 VM 目录路径 - 使用项目中的 vm 目录
        // 在开发模式下使用相对路径，生产模式使用 app data 目录
        let vm_dir = if cfg!(debug_assertions) {
            // 开发模式: 使用项目根目录下的 vm 目录
            std::env::current_dir()
                .unwrap_or_else(|_| PathBuf::from("."))
                .parent()
                .and_then(|p| p.parent())
                .map(|p| p.join("vm"))
                .unwrap_or_else(|| PathBuf::from("../../vm"))
        } else {
            // 生产模式: 使用 app data 目录
            dirs::data_dir()
                .unwrap_or_else(|| PathBuf::from("."))
                .join("nb-cc")
                .join("vm")
        };
        
        Self::new(vm_dir)
    }
}

/// VM 状态信息
#[derive(Debug, Clone, serde::Serialize)]
pub struct VmStatus {
    pub running: bool,
    pub agent_healthy: bool,       // 宿主机 Agent
    pub mcp_healthy: bool,         // VM 内 MCP Server (NovAIC Core)
    pub websockify_running: bool,  // VNC WebSocket
    pub vnc_port: u16,
    pub agent_port: u16,
    pub vsock_cid: u32,            // VSOCK CID for MCP
    pub mcp_vsock_port: u32,       // VSOCK port for MCP
    pub websocket_port: u16,
    pub vnc_url: String,
    pub agent_url: String,
    pub agent_id: Option<String>,  // 当前运行的 Agent ID
}
