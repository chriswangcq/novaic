use std::path::PathBuf;
use std::process::{Child, Command, Stdio};
use tokio::sync::Mutex;
use tokio::time::{sleep, Duration};
use std::net::TcpStream;

/// VM 配置
#[derive(Clone)]
pub struct VmConfig {
    pub memory: String,      // 内存大小, e.g., "4G"
    pub cpus: u32,           // CPU 核心数
    pub vnc_port: u16,       // VNC 端口 (VM 内部使用，通过 QEMU 转发)
    pub agent_port: u16,     // Agent API 端口 (宿主机)
    pub executor_port: u16,  // Executor API 端口 (VM 内)
    pub websocket_port: u16, // WebSocket 端口 (VM 内的 websockify 提供)
    pub ssh_port: u16,       // SSH 端口
}

impl Default for VmConfig {
    fn default() -> Self {
        Self {
            memory: "4096".to_string(),
            cpus: 4,
            vnc_port: 5900,      // 宿主机 VNC 端口 (映射到 VM 的 5901)
            agent_port: 8080,    // Agent API 端口 (宿主机)
            executor_port: 8081, // MCP Server 端口 (映射到 VM 的 8080)
            websocket_port: 6080,// WebSocket 端口 (VNC over WebSocket)
            ssh_port: 2222,      // SSH 端口
        }
    }
}

/// VM Manager - handles QEMU virtual machine lifecycle
/// websockify 运行在 VM 内部，通过 QEMU 端口转发访问
pub struct VmManager {
    qemu_process: Mutex<Option<Child>>,
    vm_dir: PathBuf,        // VM 目录 (包含镜像、固件等)
    config: VmConfig,
}

impl VmManager {
    pub fn new(vm_dir: PathBuf) -> Self {
        Self {
            qemu_process: Mutex::new(None),
            vm_dir,
            config: VmConfig::default(),
        }
    }

    pub fn with_config(mut self, config: VmConfig) -> Self {
        self.config = config;
        self
    }

    /// 获取镜像路径
    fn get_image_path(&self) -> PathBuf {
        // 优先使用 ubuntu-linux2mcp.qcow2，如果不存在则使用 nb-cc-vm.qcow2
        let ubuntu_image = self.vm_dir.join("images").join("ubuntu-linux2mcp.qcow2");
        if ubuntu_image.exists() {
            ubuntu_image
        } else {
            self.vm_dir.join("images").join("nb-cc-vm.qcow2")
        }
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
        let image_path = self.get_image_path();
        
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

        // 检查 Executor 端口（8081）是否被占用 - 用于检测 VM 是否在运行
        // Agent 现在在宿主机运行，不再用于检测 VM 状态
        if TcpStream::connect("127.0.0.1:8081").is_ok() {
            println!("[VM] VM already running (detected via Executor port 8081), skipping start");
            // 等待 websockify 就绪
            self.wait_for_websockify().await?;
            return Ok(());
        }
        
        // 确保端口可用
        self.check_port_available(self.config.vnc_port)?;
        self.check_port_available(self.config.websocket_port)?;

        // 根据操作系统和架构选择 QEMU 命令和参数
        let qemu_cmd = self.get_qemu_command();
        let qemu_args = self.build_qemu_args()?;

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
        let start = std::time::Instant::now();
        println!("[VM] Waiting for websockify service (port {})...", self.config.websocket_port);
        
        let max_attempts = 30;
        for attempt in 1..=max_attempts {
            if TcpStream::connect(format!("127.0.0.1:{}", self.config.websocket_port)).is_ok() {
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

    /// 等待 Executor 服务可用（在 VM 内运行）
    async fn wait_for_executor(&self) -> Result<(), String> {
        let start = std::time::Instant::now();
        println!("[VM] Waiting for Executor service (port {})...", self.config.executor_port);
        
        // VM 启动后，给 systemd 服务一些时间启动
        sleep(Duration::from_secs(3)).await;
        
        let max_attempts = 90;  // 最多等待 180 秒（3分钟）
        let mut tcp_ready = false;
        
        for attempt in 1..=max_attempts {
            // 先检查 TCP 端口是否可连接
            if !tcp_ready {
                if TcpStream::connect(format!("127.0.0.1:{}", self.config.executor_port)).is_ok() {
                    tcp_ready = true;
                    println!("[VM] Executor TCP port ready after {:.1}s", start.elapsed().as_secs_f32());
                }
            }
            
            // TCP 就绪后检查 HTTP 健康状态
            if tcp_ready {
                match self.check_executor_health().await {
                    Ok(true) => {
                        println!("[VM] Executor healthy after {:.1}s (attempt {})", start.elapsed().as_secs_f32(), attempt);
                        return Ok(());
                    }
                    _ => {}
                }
            }
            
            if attempt % 10 == 0 {
                println!("[VM] Still waiting for Executor... {:.1}s (attempt {}, tcp={})", 
                    start.elapsed().as_secs_f32(), attempt, tcp_ready);
            }
            
            if attempt < max_attempts {
                sleep(Duration::from_secs(2)).await;
            }
        }

        // Executor 未能启动，但 VM 可能仍在运行
        println!("[VM] Warning: Executor not responding after {:.1}s", start.elapsed().as_secs_f32());
        Ok(())
    }

    /// 检查 MCP Server 健康状态 (NovAIC Core)
    async fn check_executor_health(&self) -> Result<bool, String> {
        // 使用 /health 端点检查
        let url = format!("http://127.0.0.1:{}/health", self.config.executor_port);
        
        let client = reqwest::Client::builder()
            .timeout(Duration::from_secs(10))  // 增加超时时间
            .connect_timeout(Duration::from_secs(5))  // 连接超时
            .build()
            .map_err(|e| e.to_string())?;

        match client.get(&url).send().await {
            Ok(response) => {
                if response.status().is_success() {
                    // 验证响应内容
                    if let Ok(text) = response.text().await {
                        return Ok(text.contains("healthy"));
                    }
                }
                Ok(false)
            },
            Err(_) => Ok(false),
        }
    }
    
    /// 检查宿主机 Agent 健康状态（用于状态查询）
    async fn check_agent_health(&self) -> Result<bool, String> {
        let url = format!("http://127.0.0.1:{}/api/health", self.config.agent_port);
        
        let client = reqwest::Client::builder()
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

        // 检查 Agent 端口是否可连接
        TcpStream::connect(format!("127.0.0.1:{}", self.config.agent_port)).is_ok()
    }

    /// Get VM status
    pub async fn get_status(&self) -> VmStatus {
        let is_running = self.is_running().await;
        let agent_healthy = self.check_agent_health().await.unwrap_or(false);
        let mcp_healthy = self.check_executor_health().await.unwrap_or(false);
        
        // 检查 websockify 端口是否可用 (在 VM 内运行)
        let websockify_running = TcpStream::connect(
            format!("127.0.0.1:{}", self.config.websocket_port)
        ).is_ok();

        VmStatus {
            running: is_running || mcp_healthy,  // 如果 MCP 健康，则 VM 在运行
            agent_healthy,
            mcp_healthy,
            websockify_running,
            vnc_port: self.config.vnc_port,
            agent_port: self.config.agent_port,
            mcp_port: self.config.executor_port,
            websocket_port: self.config.websocket_port,
            vnc_url: self.get_vnc_url(),
            agent_url: self.get_agent_url(),
            mcp_url: self.get_mcp_url(),
        }
    }

    /// Get MCP Server URL
    pub fn get_mcp_url(&self) -> String {
        format!("http://localhost:{}", self.config.executor_port)
    }

    /// Get VNC WebSocket URL (for noVNC)
    pub fn get_vnc_url(&self) -> String {
        format!("ws://localhost:{}/websockify", self.config.websocket_port)
    }

    /// Get Agent API URL
    pub fn get_agent_url(&self) -> String {
        format!("http://localhost:{}", self.config.agent_port)
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
        if Self::is_arm64() {
            "qemu-system-aarch64".to_string()
        } else {
            "qemu-system-x86_64".to_string()
        }
    }

    /// 获取 cloud-init ISO 路径
    fn get_seed_iso_path(&self) -> PathBuf {
        self.vm_dir.join("iso").join("cloud-init-seed.iso")
    }

    /// 构建 QEMU 参数
    fn build_qemu_args(&self) -> Result<Vec<String>, String> {
        let image_path = self.get_image_path();
        
        // 网络端口转发
        // - vnc: VNC 端口 (VM 内 5901 -> 宿主机 5900)
        // - mcp: MCP Server (VM 内 8080 -> 宿主机 8081)
        // - ws: websockify (VM 内 6080 -> 宿主机 6080)
        // - ssh: SSH 访问 (VM 内 22 -> 宿主机 2222)
        let port_forward = format!(
            "hostfwd=tcp::{vnc}-:5901,hostfwd=tcp::{mcp}-:8080,hostfwd=tcp::{ws}-:6080,hostfwd=tcp::{ssh}-:22",
            vnc = self.config.vnc_port,
            mcp = self.config.executor_port,  // MCP Server 端口
            ws = self.config.websocket_port,
            ssh = self.config.ssh_port,
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
                "-m".to_string(), self.config.memory.clone(),
                "-smp".to_string(), self.config.cpus.to_string(),
                // UEFI 固件
                "-drive".to_string(), format!("if=pflash,format=raw,file={},readonly=on", firmware_path.display()),
                "-drive".to_string(), format!("if=pflash,format=raw,file={}", uefi_vars_path.display()),
                // 系统盘 (virtio)
                "-drive".to_string(), format!("if=none,id=hd0,format=qcow2,file={}", image_path.display()),
                "-device".to_string(), "virtio-blk-pci,drive=hd0,bootindex=1".to_string(),
                // 网络
                "-device".to_string(), "virtio-net-pci,netdev=net0".to_string(),
                "-netdev".to_string(), format!("user,id=net0,{}", port_forward),
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
            Ok(vec![
                "-name".to_string(), "novaic-vm".to_string(),
                "-m".to_string(), self.config.memory.clone(),
                "-smp".to_string(), self.config.cpus.to_string(),
                "-hda".to_string(), image_path.to_str().unwrap().to_string(),
                "-boot".to_string(), "c".to_string(),
                "-net".to_string(), "nic".to_string(),
                "-net".to_string(), format!("user,{}", port_forward),
                "-display".to_string(), "none".to_string(),
            ])
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
    pub mcp_port: u16,             // MCP Server 端口
    pub websocket_port: u16,
    pub vnc_url: String,
    pub agent_url: String,
    pub mcp_url: String,           // MCP Server URL
}
