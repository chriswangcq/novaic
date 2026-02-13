// Prevents additional console window on Windows in release
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod vm;
mod error;
mod commands;
mod http_client;
mod gateway_client;
mod config;

use gateway_client::GatewayClient;

// VM management is now handled by Gateway - Tauri only handles:
// - Gateway process management
// - Cloud image download (optional)
use vm::setup::{check_environment, check_cloud_image, download_cloud_image};
use vm::deploy::deploy_agent;

use std::sync::Arc;
use std::path::PathBuf;
use std::process::{Child, Command, Stdio};
use tokio::sync::Mutex;
use tauri::{
    AppHandle,
    Manager,
    image::Image,
    WindowEvent,
    tray::TrayIconBuilder,
    menu::{Menu, MenuItem},
};

use config::AppConfig;

/// Backend 组件: Gateway - API + DB，不含工具服务（工具服务由 Tools Server 独立进程提供）
struct GatewayProcess {
    process: Option<Child>,
    port: u16,
}

impl GatewayProcess {
    fn new() -> Self {
        Self {
            process: None,
            port: 19999,
        }
    }

    fn base_url(&self) -> String {
        format!("http://127.0.0.1:{}", self.port)
    }
}

/// Backend 组件: Tools Server - 工具服务（与 Gateway 并列）
struct ToolsServerProcess {
    process: Option<Child>,
    port: u16,
}

impl ToolsServerProcess {
    fn new() -> Self {
        Self {
            process: None,
            port: 19998,
        }
    }
}

/// Backend 组件: VmControl - VM 控制服务（Rust 原生，QMP/Guest Agent/VNC 代理）
struct VmControlProcess {
    process: Option<Child>,
    port: u16,
}

impl VmControlProcess {
    fn new() -> Self {
        Self {
            process: None,
            port: 8080,
        }
    }
    
    /// Start VmControl from binary
    fn start(&mut self, app: &AppHandle) -> Result<(), String> {
        if self.process.is_some() {
            println!("[VmControl] Already running");
            return Ok(());
        }
        
        // Get vmcontrol binary path from resources
        let resource_dir = app.path().resource_dir()
            .map_err(|e| format!("Failed to get resource dir: {}", e))?;
        let vmcontrol_path = resource_dir.join("vmcontrol/vmcontrol");
        
        if !vmcontrol_path.exists() {
            return Err(format!("VmControl binary not found at {:?}", vmcontrol_path));
        }
        
        println!("[VmControl] Starting from {:?}", vmcontrol_path);
        println!("[VmControl] Port: {}", self.port);
        
        let child = Command::new(&vmcontrol_path)
            .arg("--port")
            .arg(self.port.to_string())
            .arg("--host")
            .arg("127.0.0.1")
            .env("RUST_LOG", "vmcontrol=info,tower_http=debug")
            .stdout(Stdio::null())
            .stderr(Stdio::null())
            .spawn()
            .map_err(|e| format!("Failed to start VmControl: {}", e))?;
        
        self.process = Some(child);
        println!("[VmControl] Started on port {}", self.port);
        Ok(())
    }
    
    fn stop(&mut self) {
        if let Some(mut process) = self.process.take() {
            let pid = process.id();
            println!("[VmControl] Stopping process (PID: {})...", pid);
            
            #[cfg(unix)]
            unsafe {
                libc::kill(pid as i32, libc::SIGTERM);
            }
            
            std::thread::sleep(std::time::Duration::from_millis(AppConfig::PROCESS_TERM_WAIT_MS));
            
            match process.try_wait() {
                Ok(Some(status)) => {
                    println!("[VmControl] Stopped gracefully with status: {:?}", status);
                    return;
                }
                Ok(None) => {
                    println!("[VmControl] Process still running, sending SIGKILL...");
                    let _ = process.kill();
                    let _ = process.wait();
                    println!("[VmControl] Force killed");
                }
                Err(e) => {
                    println!("[VmControl] Error checking process status: {}", e);
                    let _ = process.kill();
                }
            }
        }
    }
    
    fn is_running(&self) -> bool {
        self.process.is_some()
    }
    
    fn base_url(&self) -> String {
        format!("http://127.0.0.1:{}", self.port)
    }
}

impl Drop for VmControlProcess {
    fn drop(&mut self) {
        self.stop();
    }
}

/// Backend 组件: Queue Service - Task/Saga 队列管理
struct QueueServiceProcess {
    process: Option<Child>,
    port: u16,
}

impl QueueServiceProcess {
    fn new() -> Self {
        Self {
            process: None,
            port: 19997,
        }
    }
}

/// Backend 组件: Service Process - 通用服务进程管理器
/// v4.0: Saga/Task Architecture (Watchdog, Task Worker, Saga Worker, Health)
/// Services only communicate with Gateway (Tools ops proxied through Gateway)
struct ServiceProcess {
    process: Option<Child>,
    service_type: String,  // watchdog, task-worker, saga-worker, health
}

impl ServiceProcess {
    fn new(service_type: &str, _gateway_url: &str) -> Self {
        Self {
            process: None,
            service_type: service_type.to_string(),
        }
    }

    fn stop(&mut self) {
        if let Some(mut process) = self.process.take() {
            let pid = process.id();
            println!("[{}] Stopping process (PID: {})...", self.service_type, pid);
            
            #[cfg(unix)]
            unsafe {
                libc::kill(pid as i32, libc::SIGTERM);
            }
            
            std::thread::sleep(std::time::Duration::from_millis(AppConfig::PROCESS_TERM_WAIT_MS));
            
            match process.try_wait() {
                Ok(Some(status)) => {
                    println!("[{}] Stopped gracefully with status: {:?}", self.service_type, status);
                    return;
                }
                Ok(None) => {
                    println!("[{}] Process still running, sending SIGKILL...", self.service_type);
                    let _ = process.kill();
                    let _ = process.wait();
                    println!("[{}] Force killed", self.service_type);
                }
                Err(e) => {
                    println!("[{}] Error checking process status: {}", self.service_type, e);
                    let _ = process.kill();
                }
            }
        }
    }
}

impl Drop for ServiceProcess {
    fn drop(&mut self) {
        self.stop();
    }
}

impl GatewayProcess {

    /// Start Gateway using unified novaic-backend binary
    /// v2.11: Uses `novaic-backend gateway` command
    fn start(&mut self, gateway_path: &PathBuf, is_binary: bool, data_dir: &PathBuf, resource_dir: Option<&PathBuf>) -> Result<(), String> {
        if self.process.is_some() {
            println!("[Gateway] Already running");
            return Ok(());
        }

        println!("[Gateway] Starting Gateway from {:?}", gateway_path);
        println!("[Gateway] Port: {}", self.port);
        println!("[Gateway] Data dir: {:?}", data_dir);
        println!("[Gateway] Mode: {}", if is_binary { "binary" } else { "python" });

        let data_dir_str = data_dir.to_string_lossy().to_string();
        
        // Get resource_dir string, or empty if not provided
        let provided_resource_dir = resource_dir.map(|p| p.to_string_lossy().to_string()).unwrap_or_default();
        
        // For binary mode, infer resource_dir from gateway_path if not provided or empty
        // gateway_path is at: resource_dir/novaic-backend/novaic-backend
        let resource_dir_str = if is_binary && provided_resource_dir.is_empty() {
            if let Some(parent) = gateway_path.parent() {
                if let Some(grandparent) = parent.parent() {
                    println!("[Gateway] Inferred resource_dir from binary path: {:?}", grandparent);
                    grandparent.to_string_lossy().to_string()
                } else {
                    println!("[Gateway] Warning: Could not infer resource_dir (no grandparent)");
                    String::new()
                }
            } else {
                println!("[Gateway] Warning: Could not infer resource_dir (no parent)");
                String::new()
            }
        } else {
            provided_resource_dir
        };
        println!("[Gateway] Using resource_dir: {}", resource_dir_str);

        let child = if is_binary {
            // Production mode: run unified novaic-backend binary
            // v2.11: Uses `novaic-backend gateway --port PORT --data-dir PATH`
            if !gateway_path.exists() {
                return Err(format!("Backend binary not found at {:?}", gateway_path));
            }
            
            Command::new(gateway_path)
                .arg("gateway")  // Subcommand
                .arg("--port")
                .arg(self.port.to_string())
                .arg("--data-dir")
                .arg(&data_dir_str)
                .env("NOVAIC_RESOURCE_DIR", &resource_dir_str)
                .env("NOVAIC_TOOLS_SERVER_URL", "http://127.0.0.1:19998")
                .env("NO_PROXY", "localhost,127.0.0.1,::1")
                .env("no_proxy", "localhost,127.0.0.1,::1")
                // Use null to discard output - prevents pipe buffer from filling up
                .stdout(Stdio::null())
                .stderr(Stdio::null())
                .spawn()
                .map_err(|e| format!("Failed to start Gateway binary: {}", e))?
        } else {
            // Development mode: run Python via novaic_main.py
            let gateway_dir = gateway_path;
            let venv_python = gateway_dir.join("venv/bin/python");
            let python = if venv_python.exists() {
                venv_python.to_string_lossy().to_string()
            } else if cfg!(target_os = "windows") {
                "python".to_string()
            } else {
                "python3".to_string()
            };

            let novaic_main = gateway_dir.join("novaic_main.py");
            if !novaic_main.exists() {
                return Err(format!("novaic_main.py not found at {:?}", novaic_main));
            }

            println!("[Gateway] Using Python: {}", python);

            // v2.11: Use unified novaic_main.py entry point
            Command::new(&python)
                .arg(&novaic_main)
                .arg("gateway")
                .arg("--port")
                .arg(self.port.to_string())
                .arg("--data-dir")
                .arg(&data_dir_str)
                .current_dir(gateway_dir)
                .env("NOVAIC_RESOURCE_DIR", &resource_dir_str)
                .env("NOVAIC_TOOLS_SERVER_URL", "http://127.0.0.1:19998")
                .env("NO_PROXY", "localhost,127.0.0.1,::1")
                .env("no_proxy", "localhost,127.0.0.1,::1")
                // Dev mode: inherit console so we can see logs directly
                .stdout(Stdio::inherit())
                .stderr(Stdio::inherit())
                .spawn()
                .map_err(|e| format!("Failed to start Gateway: {}", e))?
        };

        self.process = Some(child);
        println!("[Gateway] Started on port {}", self.port);
        Ok(())
    }

    fn stop(&mut self) {
        if let Some(mut process) = self.process.take() {
            let pid = process.id();
            println!("[Gateway] Stopping process (PID: {})...", pid);
            
            // Step 1: Stop all VMs via Gateway API with quick mode
            // quick=true: shorter timeouts, graceful=false: skip SSH poweroff
            // This makes exit much faster (3-5s instead of 20+s)
            println!("[Gateway] Stopping all VMs via API (quick mode)...");
            let stop_url = format!("{}/api/vm/stop-all?quick=true&graceful=false", self.base_url());
            match reqwest::blocking::Client::builder()
                .timeout(std::time::Duration::from_secs(AppConfig::GATEWAY_STOP_TIMEOUT_SECS))
                .build()
            {
                Ok(client) => {
                    match client.post(&stop_url).send() {
                        Ok(resp) => {
                            if resp.status().is_success() {
                                println!("[Gateway] All VMs stopped successfully");
                            } else {
                                println!("[Gateway] VM stop API returned: {}", resp.status());
                            }
                        }
                        Err(e) => {
                            println!("[Gateway] VM stop API failed (may already be stopping): {}", e);
                        }
                    }
                }
                Err(e) => {
                    println!("[Gateway] Failed to create HTTP client: {}", e);
                }
            }
            
            // Step 2: Send SIGTERM for graceful Gateway shutdown
            #[cfg(unix)]
            unsafe {
                libc::kill(pid as i32, libc::SIGTERM);
            }
            #[cfg(unix)]
            println!("[Gateway] SIGTERM sent to PID {}", pid);
            
            // Wait briefly for graceful shutdown
            std::thread::sleep(std::time::Duration::from_secs(1));
            
            // Check if process exited
            match process.try_wait() {
                Ok(Some(status)) => {
                    println!("[Gateway] Stopped gracefully with status: {:?}", status);
                    return;
                }
                Ok(None) => {
                    // Still running, force kill
                    println!("[Gateway] Process still running, sending SIGKILL...");
                    let _ = process.kill();
                    let _ = process.wait(); // Wait for cleanup
                    println!("[Gateway] Force killed");
                }
                Err(e) => {
                    println!("[Gateway] Error checking process status: {}", e);
                    let _ = process.kill();
                }
            }
        }
    }

    fn is_running(&mut self) -> bool {
        if let Some(ref mut process) = self.process {
            match process.try_wait() {
                Ok(Some(_)) => {
                    // Process has exited
                    self.process = None;
                    false
                }
                Ok(None) => true,
                Err(_) => false,
            }
        } else {
            false
        }
    }
}

impl Drop for GatewayProcess {
    fn drop(&mut self) {
        self.stop();
    }
}

impl ToolsServerProcess {
    /// Start MCP Gateway using unified novaic-backend binary
    fn start(&mut self, backend_path: &PathBuf, is_binary: bool, data_dir: &PathBuf, resource_dir: Option<&PathBuf>) -> Result<(), String> {
        if self.process.is_some() {
            println!("[Tools Server] Already running");
            return Ok(());
        }

        let data_dir_str = data_dir.to_string_lossy().to_string();
        
        // Get resource_dir string, or empty if not provided
        let provided_resource_dir = resource_dir.map(|p| p.to_string_lossy().to_string()).unwrap_or_default();
        
        // For binary mode, infer resource_dir from backend_path if not provided or empty
        // backend_path is at: resource_dir/novaic-backend/novaic-backend
        let resource_dir_str = if is_binary && provided_resource_dir.is_empty() {
            if let Some(parent) = backend_path.parent() {
                if let Some(grandparent) = parent.parent() {
                    println!("[Tools Server] Inferred resource_dir from binary path: {:?}", grandparent);
                    grandparent.to_string_lossy().to_string()
                } else {
                    println!("[Tools Server] Warning: Could not infer resource_dir (no grandparent)");
                    String::new()
                }
            } else {
                println!("[Tools Server] Warning: Could not infer resource_dir (no parent)");
                String::new()
            }
        } else {
            provided_resource_dir
        };
        println!("[Tools Server] Using resource_dir: {}", resource_dir_str);

        let child = if is_binary {
            if !backend_path.exists() {
                return Err(format!("Backend binary not found at {:?}", backend_path));
            }
            Command::new(backend_path)
                .arg("tools-server")
                .arg("--port")
                .arg(self.port.to_string())
                .arg("--data-dir")
                .arg(&data_dir_str)
                .env("NOVAIC_RESOURCE_DIR", &resource_dir_str)
                .env("NOVAIC_GATEWAY_URL", format!("http://127.0.0.1:19999"))
                .env("NO_PROXY", "localhost,127.0.0.1,::1")
                .env("no_proxy", "localhost,127.0.0.1,::1")
                .stdout(Stdio::null())
                .stderr(Stdio::null())
                .spawn()
                .map_err(|e| format!("Failed to start Tools Server binary: {}", e))?
        } else {
            // Dev mode: backend_path is the novaic-backend directory (has main.py, novaic_main.py)
            let gateway_dir = backend_path;
            let venv_python = gateway_dir.join("venv/bin/python");
            let python = if venv_python.exists() {
                venv_python.to_string_lossy().to_string()
            } else if cfg!(target_os = "windows") {
                "python".to_string()
            } else {
                "python3".to_string()
            };
            // Run from gateway dir so python -m novaic_main works (novaic_main.py in novaic-backend)
            Command::new(&python)
                .arg("-m")
                .arg("novaic_main")
                .arg("tools-server")
                .arg("--port")
                .arg(self.port.to_string())
                .arg("--data-dir")
                .arg(&data_dir_str)
                .current_dir(&gateway_dir)
                .env("NOVAIC_TOOLS_PORT", self.port.to_string())
                .env("NOVAIC_GATEWAY_URL", "http://127.0.0.1:19999")
                .env("NOVAIC_DATA_DIR", &data_dir_str)
                .env("NO_PROXY", "localhost,127.0.0.1,::1")
                .env("no_proxy", "localhost,127.0.0.1,::1")
                .stdout(Stdio::inherit())
                .stderr(Stdio::inherit())
                .spawn()
                .map_err(|e| format!("Failed to start Tools Server: {}", e))?
        };

        self.process = Some(child);
        println!("[Tools Server] Started on port {}", self.port);
        Ok(())
    }

    fn stop(&mut self) {
        if let Some(mut process) = self.process.take() {
            let pid = process.id();
            println!("[Tools Server] Stopping process (PID: {})...", pid);
            #[cfg(unix)]
            unsafe { libc::kill(pid as i32, libc::SIGTERM); }
            std::thread::sleep(std::time::Duration::from_millis(AppConfig::PROCESS_TERM_WAIT_MS));
            match process.try_wait() {
                Ok(Some(_)) => {}
                Ok(None) => { let _ = process.kill(); let _ = process.wait(); }
                Err(_) => { let _ = process.kill(); }
            }
            println!("[Tools Server] Stopped");
        }
    }
}

impl Drop for ToolsServerProcess {
    fn drop(&mut self) {
        self.stop();
    }
}

impl QueueServiceProcess {
    /// Start Queue Service using unified novaic-backend binary
    fn start(&mut self, backend_path: &PathBuf, is_binary: bool, data_dir: &PathBuf, resource_dir: Option<&PathBuf>) -> Result<(), String> {
        if self.process.is_some() {
            println!("[Queue Service] Already running");
            return Ok(());
        }

        let data_dir_str = data_dir.to_string_lossy().to_string();
        
        // Get resource_dir string, or empty if not provided
        let provided_resource_dir = resource_dir.map(|p| p.to_string_lossy().to_string()).unwrap_or_default();
        
        // For binary mode, infer resource_dir from backend_path if not provided or empty
        // backend_path is at: resource_dir/novaic-backend/novaic-backend
        let resource_dir_str = if is_binary && provided_resource_dir.is_empty() {
            if let Some(parent) = backend_path.parent() {
                if let Some(grandparent) = parent.parent() {
                    println!("[Queue Service] Inferred resource_dir from binary path: {:?}", grandparent);
                    grandparent.to_string_lossy().to_string()
                } else {
                    println!("[Queue Service] Warning: Could not infer resource_dir (no grandparent)");
                    String::new()
                }
            } else {
                println!("[Queue Service] Warning: Could not infer resource_dir (no parent)");
                String::new()
            }
        } else {
            provided_resource_dir
        };
        println!("[Queue Service] Using resource_dir: {}", resource_dir_str);

        let child = if is_binary {
            if !backend_path.exists() {
                return Err(format!("Backend binary not found at {:?}", backend_path));
            }
            Command::new(backend_path)
                .arg("queue-service")
                .arg("--port")
                .arg(self.port.to_string())
                .arg("--data-dir")
                .arg(&data_dir_str)
                .env("NOVAIC_RESOURCE_DIR", &resource_dir_str)
                .env("NOVAIC_GATEWAY_URL", format!("http://127.0.0.1:19999"))
                .env("NO_PROXY", "localhost,127.0.0.1,::1")
                .env("no_proxy", "localhost,127.0.0.1,::1")
                .stdout(Stdio::null())
                .stderr(Stdio::null())
                .spawn()
                .map_err(|e| format!("Failed to start Queue Service binary: {}", e))?
        } else {
            // Dev mode: backend_path is the novaic-backend directory (has main.py, novaic_main.py)
            let gateway_dir = backend_path;
            let venv_python = gateway_dir.join("venv/bin/python");
            let python = if venv_python.exists() {
                venv_python.to_string_lossy().to_string()
            } else if cfg!(target_os = "windows") {
                "python".to_string()
            } else {
                "python3".to_string()
            };
            // Run from gateway dir so python -m novaic_main works (novaic_main.py in novaic-backend)
            Command::new(&python)
                .arg("-m")
                .arg("novaic_main")
                .arg("queue-service")
                .arg("--port")
                .arg(self.port.to_string())
                .arg("--data-dir")
                .arg(&data_dir_str)
                .current_dir(&gateway_dir)
                .env("NOVAIC_QUEUE_PORT", self.port.to_string())
                .env("NOVAIC_GATEWAY_URL", "http://127.0.0.1:19999")
                .env("NOVAIC_DATA_DIR", &data_dir_str)
                .env("NO_PROXY", "localhost,127.0.0.1,::1")
                .env("no_proxy", "localhost,127.0.0.1,::1")
                .stdout(Stdio::inherit())
                .stderr(Stdio::inherit())
                .spawn()
                .map_err(|e| format!("Failed to start Queue Service: {}", e))?
        };

        self.process = Some(child);
        println!("[Queue Service] Started on port {}", self.port);
        Ok(())
    }

    fn stop(&mut self) {
        if let Some(mut process) = self.process.take() {
            let pid = process.id();
            println!("[Queue Service] Stopping process (PID: {})...", pid);
            #[cfg(unix)]
            unsafe { libc::kill(pid as i32, libc::SIGTERM); }
            std::thread::sleep(std::time::Duration::from_millis(AppConfig::PROCESS_TERM_WAIT_MS));
            match process.try_wait() {
                Ok(Some(_)) => {}
                Ok(None) => { let _ = process.kill(); let _ = process.wait(); }
                Err(_) => { let _ = process.kill(); }
            }
            println!("[Queue Service] Stopped");
        }
    }
}

impl Drop for QueueServiceProcess {
    fn drop(&mut self) {
        self.stop();
    }
}

type GatewayState = Arc<Mutex<GatewayProcess>>;
type ToolsServerState = Arc<Mutex<ToolsServerProcess>>;
type VmControlState = Arc<Mutex<VmControlProcess>>;
// v4.0: Four services (Watchdog, Task Worker, Saga Worker, Health)
type WatchdogState = Arc<Mutex<ServiceProcess>>;
type TaskWorkerState = Arc<Mutex<ServiceProcess>>;
type SagaWorkerState = Arc<Mutex<ServiceProcess>>;
type HealthState = Arc<Mutex<ServiceProcess>>;
type SchedulerState = Arc<Mutex<ServiceProcess>>;

/// Kill any zombie novaic-backend processes before starting new ones
/// This prevents issues from leftover processes after crashes or improper shutdowns
fn kill_zombie_processes() {
    println!("[Cleanup] Cleaning up zombie backend processes...");
    
    #[cfg(unix)]
    {
        use std::process::Command;
        
        // Step 1: Kill processes by name patterns
        let patterns = [
            // Binary mode
            "novaic-backend",
            // Dev mode - all worker scripts
            "main_gateway.py",
            "main_tools.py",
            "main_watchdog.py",
            "main_task.py",
            "main_saga.py",
            "main_health.py",
            "main_scheduler.py",
            "queue_service",         // Queue service module
            "novaic_main.py",        // Legacy unified entry
        ];
        
        let mut killed_count = 0;
        for pattern in patterns {
            // Use pkill to kill processes matching the pattern
            let result = Command::new("pkill")
                .arg("-9")
                .arg("-f")
                .arg(pattern)
                .output();
            
            if let Ok(output) = result {
                if output.status.success() {
                    killed_count += 1;
                    println!("[Cleanup] Killed processes matching '{}'", pattern);
                }
            }
        }
        
        // Step 2: Kill processes occupying our ports (in case of orphaned processes)
        let ports = [19999, 19998, 19997];  // Gateway, Tools Server, Queue Service
        for port in ports {
            // Find process using the port via lsof
            let lsof_result = Command::new("lsof")
                .args(["-ti", &format!(":{}", port)])
                .output();
            
            if let Ok(output) = lsof_result {
                let pids = String::from_utf8_lossy(&output.stdout);
                for pid_str in pids.trim().lines() {
                    if let Ok(pid) = pid_str.trim().parse::<i32>() {
                        // Kill the process
                        unsafe {
                            if libc::kill(pid, libc::SIGKILL) == 0 {
                                println!("[Cleanup] Killed PID {} occupying port {}", pid, port);
                                killed_count += 1;
                            }
                        }
                    }
                }
            }
        }
        
        if killed_count > 0 {
            // Give processes time to fully terminate
            std::thread::sleep(std::time::Duration::from_millis(AppConfig::PROCESS_TERM_WAIT_MS));
            println!("[Cleanup] Cleaned up {} zombie process(es)", killed_count);
        } else {
            println!("[Cleanup] No zombie processes found");
        }
    }
    
    #[cfg(windows)]
    {
        use std::process::Command;
        
        // On Windows, use taskkill for the binary
        let _ = Command::new("taskkill")
            .args(["/F", "/IM", "novaic-backend.exe"])
            .output();
        
        // Also try to kill Python processes running our scripts
        let python_patterns = [
            "main_gateway.py",
            "main_tools.py", 
            "main_watchdog.py",
            "main_task.py",
            "main_saga.py",
            "main_health.py",
            "main_scheduler.py",
        ];
        
        for pattern in python_patterns {
            // Use wmic to find and kill Python processes with our scripts
            let _ = Command::new("wmic")
                .args(["process", "where", &format!("CommandLine like '%{}%'", pattern), "delete"])
                .output();
        }
        
        std::thread::sleep(std::time::Duration::from_millis(500));
        println!("[Cleanup] Done cleaning up zombie processes");
    }
}

/// Get unified backend path and whether it's a binary
/// Returns (path, is_binary, gateway_dir_for_dev)
/// 
/// v2.11: Uses unified novaic-backend binary for all modes (gateway, master, worker)
/// v2.12: Supports both onefile mode (novaic-backend) and onedir mode (novaic-backend/novaic-backend)
fn get_backend_info(app: &AppHandle) -> (PathBuf, bool, Option<PathBuf>) {
    // Try to use bundled binary first (production mode)
    if let Ok(resource_dir) = app.path().resource_dir() {
        // Check onefile mode first: binary is directly at novaic-backend (relative to resource_dir)
        let onefile_path = resource_dir.join("novaic-backend");
        println!("[Backend] Checking onefile binary at: {:?}", onefile_path);
        if onefile_path.exists() && onefile_path.is_file() {
            println!("[Backend] Found onefile binary, using production mode");
            return (onefile_path, true, None);
        }
        
        // Check onedir mode: binary is at novaic-backend/novaic-backend (relative to resource_dir)
        let onedir_path = resource_dir.join("novaic-backend/novaic-backend");
        println!("[Backend] Checking onedir binary at: {:?}", onedir_path);
        if onedir_path.exists() {
            println!("[Backend] Found onedir binary, using production mode");
            return (onedir_path, true, None);
        }
        
        println!("[Backend] Bundled binary not found");
    } else {
        println!("[Backend] Could not get resource_dir");
    }
    
    // Fallback to development mode - check relative to executable
    // In dev mode, executable is at: novaic-app/src-tauri/target/release/novaic
    // Backend source is at: novaic-backend (4 levels up from executable)
    if let Ok(exe_path) = std::env::current_exe() {
        if let Some(exe_dir) = exe_path.parent() {
            // exe_dir = .../novaic-app/src-tauri/target/release/
            // Go up 4 levels to project root, then into novaic-backend
            let dev_path = exe_dir
                .join("../../../..")  // Go to project root (novaic/)
                .join("novaic-backend");
            
            if dev_path.exists() && dev_path.join("main.py").exists() {
                let canonical = dev_path.canonicalize().unwrap_or(dev_path);
                println!("[Backend] Using development source: {:?}", canonical);
                return (canonical.clone(), false, Some(canonical));
            }
            println!("[Backend] Dev path not found: {:?}", dev_path);
        }
    }
    
    println!("[Backend] ERROR: No backend found! Please ensure novaic-backend is bundled with the app.");
    (PathBuf::from("/tmp/novaic-backend-not-found"), false, None)
}

// Legacy compatibility wrappers (kept for minimal code changes)
fn get_gateway_info(app: &AppHandle) -> (PathBuf, bool) {
    let (path, is_binary, _) = get_backend_info(app);
    (path, is_binary)
}


/// Tauri command: Start Gateway
#[tauri::command]
async fn start_gateway(
    gateway: tauri::State<'_, GatewayState>,
    app: AppHandle,
) -> Result<String, String> {
    let (gateway_path, is_binary) = get_gateway_info(&app);
    let data_dir = app.path().app_data_dir()
        .map_err(|e| format!("Failed to get app data dir: {}", e))?;
    let resource_dir = app.path().resource_dir().ok();
    let mut gw = gateway.lock().await;
    gw.start(&gateway_path, is_binary, &data_dir, resource_dir.as_ref())?;
    Ok(format!("Gateway started on port {}", gw.port))
}

/// Tauri command: Stop Gateway
#[tauri::command]
async fn stop_gateway(
    gateway: tauri::State<'_, GatewayState>,
) -> Result<String, String> {
    let mut gw = gateway.lock().await;
    gw.stop();
    Ok("Gateway stopped".to_string())
}

/// Tauri command: Get Gateway status
#[tauri::command]
async fn get_gateway_status(
    gateway: tauri::State<'_, GatewayState>,
) -> Result<bool, String> {
    let mut gw = gateway.lock().await;
    Ok(gw.is_running())
}

/// Tauri command: Get Gateway URL
#[tauri::command]
async fn get_gateway_url(
    gateway: tauri::State<'_, GatewayState>,
) -> Result<String, String> {
    let gw = gateway.lock().await;
    Ok(gw.base_url())
}

/// Tauri command: Gateway API GET request
#[tauri::command]
async fn gateway_get(
    gateway: tauri::State<'_, GatewayState>,
    path: String,
) -> Result<serde_json::Value, String> {
    let base_url = { gateway.lock().await.base_url() };
    let client = GatewayClient::new(base_url);
    client.get(&path).await
}

/// Tauri command: Gateway API POST request
#[tauri::command]
async fn gateway_post(
    gateway: tauri::State<'_, GatewayState>,
    path: String,
    body: Option<serde_json::Value>,
) -> Result<serde_json::Value, String> {
    let base_url = { gateway.lock().await.base_url() };
    let client = GatewayClient::new(base_url);
    client.post(&path, body).await
}

/// Tauri command: Gateway API PATCH request
#[tauri::command]
async fn gateway_patch(
    gateway: tauri::State<'_, GatewayState>,
    path: String,
    body: Option<serde_json::Value>,
) -> Result<serde_json::Value, String> {
    let base_url = { gateway.lock().await.base_url() };
    let client = GatewayClient::new(base_url);
    client.patch(&path, body).await
}

/// Tauri command: Gateway API PUT request
#[tauri::command]
async fn gateway_put(
    gateway: tauri::State<'_, GatewayState>,
    path: String,
    body: Option<serde_json::Value>,
) -> Result<serde_json::Value, String> {
    let base_url = { gateway.lock().await.base_url() };
    let client = GatewayClient::new(base_url);
    client.put(&path, body).await
}

/// Tauri command: Gateway API DELETE request
#[tauri::command]
async fn gateway_delete(
    gateway: tauri::State<'_, GatewayState>,
    path: String,
) -> Result<serde_json::Value, String> {
    let base_url = { gateway.lock().await.base_url() };
    let client = GatewayClient::new(base_url);
    client.delete(&path).await
}

/// Tauri command: Check Gateway health
#[tauri::command]
async fn gateway_health(
    gateway: tauri::State<'_, GatewayState>,
) -> Result<bool, String> {
    let gw = gateway.lock().await;
    let client = GatewayClient::new(gw.base_url());
    client.health_check().await
}

fn main() {
    // Set NO_PROXY to avoid proxy issues with local services
    std::env::set_var("NO_PROXY", "localhost,127.0.0.1,::1,10.0.0.0/8,172.16.0.0/12,192.168.0.0/16");
    std::env::set_var("no_proxy", "localhost,127.0.0.1,::1,10.0.0.0/8,172.16.0.0/12,192.168.0.0/16");
    
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_fs::init())
        .plugin(tauri_plugin_process::init())
        .setup(|app| {
            println!("NovAIC starting...");
            
            // Create tray menu
            let show_item = MenuItem::with_id(app, "show", "显示窗口", true, None::<&str>)?;
            let quit_item = MenuItem::with_id(app, "quit", "退出", true, None::<&str>)?;
            let menu = Menu::with_items(app, &[&show_item, &quit_item])?;
            
            // Create tray icon: use dedicated tray icon; on macOS set as template for B&W menu bar style
            let tray_icon: Image = tauri::include_image!("icons/tray-icon.png");
            let mut tray_builder = TrayIconBuilder::with_id("main-tray")
                .icon(tray_icon)
                .menu(&menu)
                .show_menu_on_left_click(true)
                .tooltip("NovAIC");
            #[cfg(target_os = "macos")]
            {
                tray_builder = tray_builder.icon_as_template(true);
            }
            let _tray = tray_builder
                .on_menu_event(|app, event| {
                    println!("[Tray] Menu event: {:?}", event.id.as_ref());
                    match event.id.as_ref() {
                        "show" => {
                            if let Some(window) = app.get_webview_window("main") {
                                let _ = window.show();
                                let _ = window.set_focus();
                                println!("[App] Window shown (tray menu)");
                            }
                        }
                        "quit" => {
                            println!("[App] Quit from tray, triggering app exit...");
                            // Use app.exit() to trigger proper cleanup via RunEvent::Exit
                            app.exit(0);
                        }
                        _ => {}
                    }
                })
                .build(app)?;
            
            // App data directory - use for all data storage
            let data_dir = app.path().app_data_dir()
                .unwrap_or_else(|_| PathBuf::from("."));
            
            println!("[App] Data directory: {:?}", data_dir);
            
            // Backend 五组件（Gateway、MCP Gateway、Watchdog、Task Worker、Saga Worker、Health）均由 Tauri 统一拉起
            // v4.0: Saga/Task Architecture
            
            // Backend 组件: Gateway（API + DB）
            let gateway = Arc::new(Mutex::new(GatewayProcess::new()));
            app.manage(gateway.clone());
            
            // Backend 组件: VmControl（VM 控制服务，Rust 原生）
            let vmcontrol = Arc::new(Mutex::new(VmControlProcess::new()));
            app.manage(vmcontrol.clone());
            
            // Backend 组件: Tools Server（与 Gateway 并列）
            let tools_server = Arc::new(Mutex::new(ToolsServerProcess::new()));
            app.manage(tools_server.clone());
            
            // Backend 组件: Queue Service（Task/Saga 队列管理）
            let queue_service = Arc::new(Mutex::new(QueueServiceProcess::new()));
            app.manage(queue_service.clone());
            
            // 获取 Gateway URL (所有服务只与 Gateway 通信)
            let gateway_url = {
                let gw = tauri::async_runtime::block_on(async { gateway.lock().await });
                gw.base_url()
            };
            
            // v4.0: Four service processes (all communicate only with Gateway)
            // Watchdog: 监控 sending 消息，触发 MessageProcess Saga
            let watchdog = Arc::new(Mutex::new(
                ServiceProcess::new("watchdog", &gateway_url)
            ));
            app.manage(watchdog.clone());
            
            // Task Worker: 通用任务执行器
            let task_worker = Arc::new(Mutex::new(
                ServiceProcess::new("task-worker", &gateway_url)
            ));
            app.manage(task_worker.clone());
            
            // Saga Worker: Saga 流程编排
            let saga_worker = Arc::new(Mutex::new(
                ServiceProcess::new("saga-worker", &gateway_url)
            ));
            app.manage(saga_worker.clone());
            
            // Health: 监控并回收超时任务/Saga
            let health = Arc::new(Mutex::new(
                ServiceProcess::new("health", &gateway_url)
            ));
            app.manage(health.clone());
            
            // Scheduler: 定时唤醒 sleeping agents (1 个)
            let scheduler = Arc::new(Mutex::new(
                ServiceProcess::new("scheduler", &gateway_url)
            ));
            app.manage(scheduler.clone());
            
            // Tauri 统一拉起 Backend 六组件
            let (backend_path, is_binary) = get_gateway_info(app.handle());
            let (_, _, gateway_dir) = get_backend_info(app.handle());
            let resource_dir = app.path().resource_dir().ok();
            
            println!("[Backend] Backend path: {:?}", backend_path);
            println!("[Backend] Backend path exists: {}", backend_path.exists());
            println!("[Backend] Resource dir: {:?}", resource_dir);
            if let Some(ref rd) = resource_dir {
                println!("[Backend] Resource dir exists: {}", rd.exists());
                println!("[Backend] Resource dir str: '{}'", rd.to_string_lossy());
                // Check for novaic-mcp-vmuse
                let vmuse_path = rd.join("novaic-mcp-vmuse");
                println!("[Backend] novaic-mcp-vmuse path: {:?}", vmuse_path);
                println!("[Backend] novaic-mcp-vmuse exists: {}", vmuse_path.exists());
            }
            println!("[Backend] Is binary: {}", is_binary);
            
            let gateway_for_start = gateway.clone();
            let vmcontrol_for_start = vmcontrol.clone();
            let tools_server_for_start = tools_server.clone();
            let queue_service_for_start = queue_service.clone();
            let data_dir_for_gateway = data_dir.clone();
            let backend_path_clone = backend_path.clone();
            let gateway_dir_clone = gateway_dir.clone();
            let app_handle_for_vmcontrol = app.handle().clone();
            
            tauri::async_runtime::spawn(async move {
                // Kill any zombie backend processes before starting
                kill_zombie_processes();
                
                // 1. Backend 组件: Gateway
                {
                    let mut gw = gateway_for_start.lock().await;
                    match gw.start(&backend_path, is_binary, &data_dir_for_gateway, resource_dir.as_ref()) {
                        Ok(_) => println!("[Gateway] Auto-started successfully"),
                        Err(e) => {
                            println!("[Gateway] Failed to auto-start: {}", e);
                            return;
                        }
                    }
                }
                
                // 2. Backend 组件: VmControl（VM 控制服务）
                {
                    let mut vc = vmcontrol_for_start.lock().await;
                    match vc.start(&app_handle_for_vmcontrol) {
                        Ok(_) => println!("[VmControl] Auto-started successfully"),
                        Err(e) => {
                            println!("[VmControl] Failed to auto-start: {}", e);
                            // VmControl 失败不影响其他服务继续启动
                        }
                    }
                }
                
                // 3. Backend 组件: Tools Server
                {
                    let mut ts = tools_server_for_start.lock().await;
                    match ts.start(&backend_path, is_binary, &data_dir_for_gateway, resource_dir.as_ref()) {
                        Ok(_) => println!("[Tools Server] Auto-started successfully"),
                        Err(e) => {
                            println!("[Tools Server] Failed to auto-start: {}", e);
                        }
                    }
                }
                
                // 4. Backend 组件: Queue Service（Task/Saga 队列管理）
                {
                    let mut qs = queue_service_for_start.lock().await;
                    match qs.start(&backend_path, is_binary, &data_dir_for_gateway, resource_dir.as_ref()) {
                        Ok(_) => println!("[Queue Service] Auto-started successfully"),
                        Err(e) => {
                            println!("[Queue Service] Failed to auto-start: {}", e);
                        }
                    }
                }
                
                // 5. 等 Gateway 就绪（health check）
                println!("[Services] Waiting for Gateway to be ready...");
                let client = reqwest::Client::new();
                let health_url = format!("{}/api/health", gateway_url);
                
                for i in 0..30 {
                    tokio::time::sleep(tokio::time::Duration::from_secs(1)).await;
                    
                    match client.get(&health_url).send().await {
                        Ok(resp) if resp.status().is_success() => {
                            println!("[Services] Gateway is ready after {}s", i + 1);
                            break;
                        }
                        _ => {
                            if i == 29 {
                                println!("[Services] Gateway not ready after 30s, starting services anyway");
                            }
                        }
                    }
                }
                
                // 5b. 等 Tools Server 就绪（health check）
                println!("[Services] Waiting for Tools Server to be ready...");
                let ts_health_url = "http://127.0.0.1:19998/api/health";
                
                for i in 0..15 {
                    tokio::time::sleep(tokio::time::Duration::from_secs(1)).await;
                    
                    match client.get(ts_health_url).send().await {
                        Ok(resp) if resp.status().is_success() => {
                            println!("[Services] Tools Server is ready after {}s", i + 1);
                            break;
                        }
                        _ => {
                            if i == 14 {
                                println!("[Services] Tools Server not ready after 15s, starting workers anyway");
                            }
                        }
                    }
                }
                
                // 6-9. 直接启动 Worker 服务（和 Gateway 一样简单）
                // v4.1: Saga/Task Architecture - multiple workers for parallelism
                // 配置：可通过 AppConfig 调整 Worker 数量
                let num_task_workers = AppConfig::NUM_TASK_WORKERS;
                let num_saga_workers = AppConfig::NUM_SAGA_WORKERS;
                
                if is_binary {
                    let gateway_url = "http://127.0.0.1:19999";
                    let queue_service_url = "http://127.0.0.1:19997";
                    
                    // Watchdog: 监控 sending 消息，触发 MessageProcess Saga (1 个)
                    match Command::new(&backend_path_clone)
                        .arg("watchdog")
                        .arg("--gateway-url")
                        .arg(gateway_url)
                        .arg("--queue-service-url")
                        .arg(queue_service_url)
                        .stdout(Stdio::null())
                        .stderr(Stdio::null())
                        .spawn()
                    {
                        Ok(_) => println!("[Watchdog] Started"),
                        Err(e) => println!("[Watchdog] Failed: {}", e),
                    }
                    
                    // Task Workers: 通用任务执行器
                    for i in 1..=num_task_workers {
                        match Command::new(&backend_path_clone)
                            .arg("task-worker")
                            .arg("--gateway-url")
                            .arg(gateway_url)
                            .arg("--queue-service-url")
                            .arg(queue_service_url)
                            .stdout(Stdio::null())
                            .stderr(Stdio::null())
                            .spawn()
                        {
                            Ok(_) => println!("[Task Worker #{}] Started", i),
                            Err(e) => println!("[Task Worker #{}] Failed: {}", i, e),
                        }
                    }
                    
                    // Saga Workers: Saga 流程编排
                    for i in 1..=num_saga_workers {
                        match Command::new(&backend_path_clone)
                            .arg("saga-worker")
                            .arg("--gateway-url")
                            .arg(gateway_url)
                            .arg("--queue-service-url")
                            .arg(queue_service_url)
                            .stdout(Stdio::null())
                            .stderr(Stdio::null())
                            .spawn()
                        {
                            Ok(_) => println!("[Saga Worker #{}] Started", i),
                            Err(e) => println!("[Saga Worker #{}] Failed: {}", i, e),
                        }
                    }
                    
                    // Health: 监控并回收超时任务/Saga (1 个)
                    match Command::new(&backend_path_clone)
                        .arg("health")
                        .arg("--gateway-url")
                        .arg(gateway_url)
                        .arg("--queue-service-url")
                        .arg(queue_service_url)
                        .stdout(Stdio::null())
                        .stderr(Stdio::null())
                        .spawn()
                    {
                        Ok(_) => println!("[Health] Started"),
                        Err(e) => println!("[Health] Failed: {}", e),
                    }
                    
                    // Scheduler: 定时唤醒调度器 (1 个)
                    match Command::new(&backend_path_clone)
                        .arg("scheduler")
                        .arg("--gateway-url")
                        .arg(gateway_url)
                        .stdout(Stdio::null())
                        .stderr(Stdio::null())
                        .spawn()
                    {
                        Ok(_) => println!("[Scheduler] Started"),
                        Err(e) => println!("[Scheduler] Failed: {}", e),
                    }
                } else {
                    // 开发模式：直接启动 Python 脚本 (多个 workers)
                    let gateway_dir = gateway_dir_clone.expect("Gateway dir required for dev mode");
                    let venv_python = gateway_dir.join(".venv/bin/python");
                    let python = if venv_python.exists() {
                        venv_python.to_string_lossy().to_string()
                    } else {
                        "python3".to_string()
                    };
                    
                    let gateway_url = "http://127.0.0.1:19999";
                    let queue_service_url = "http://127.0.0.1:19997";
                    
                    // Watchdog (1 个)
                    match Command::new(&python)
                        .arg("main_watchdog.py")
                        .arg("--gateway-url")
                        .arg(gateway_url)
                        .arg("--queue-service-url")
                        .arg(queue_service_url)
                        .current_dir(&gateway_dir)
                        .stdout(Stdio::inherit())
                        .stderr(Stdio::inherit())
                        .spawn()
                    {
                        Ok(_) => println!("[Watchdog] Started (dev mode)"),
                        Err(e) => println!("[Watchdog] Failed: {}", e),
                    }
                    
                    // Task Workers
                    for i in 1..=num_task_workers {
                        match Command::new(&python)
                            .arg("main_task.py")
                            .arg("--gateway-url")
                            .arg(gateway_url)
                            .arg("--queue-service-url")
                            .arg(queue_service_url)
                            .current_dir(&gateway_dir)
                            .stdout(Stdio::inherit())
                            .stderr(Stdio::inherit())
                            .spawn()
                        {
                            Ok(_) => println!("[Task Worker #{}] Started (dev mode)", i),
                            Err(e) => println!("[Task Worker #{}] Failed: {}", i, e),
                        }
                    }
                    
                    // Saga Workers
                    for i in 1..=num_saga_workers {
                        match Command::new(&python)
                            .arg("main_saga.py")
                            .arg("--gateway-url")
                            .arg(gateway_url)
                            .arg("--queue-service-url")
                            .arg(queue_service_url)
                            .current_dir(&gateway_dir)
                            .stdout(Stdio::inherit())
                            .stderr(Stdio::inherit())
                            .spawn()
                        {
                            Ok(_) => println!("[Saga Worker #{}] Started (dev mode)", i),
                            Err(e) => println!("[Saga Worker #{}] Failed: {}", i, e),
                        }
                    }
                    
                    // Health (1 个)
                    match Command::new(&python)
                        .arg("main_health.py")
                        .arg("--queue-service-url")
                        .arg(queue_service_url)
                        .current_dir(&gateway_dir)
                        .stdout(Stdio::inherit())
                        .stderr(Stdio::inherit())
                        .spawn()
                    {
                        Ok(_) => println!("[Health] Started (dev mode)"),
                        Err(e) => println!("[Health] Failed: {}", e),
                    }
                    
                    // Scheduler (1 个)
                    match Command::new(&python)
                        .arg("main_scheduler.py")
                        .arg("--gateway-url")
                        .arg(gateway_url)
                        .current_dir(&gateway_dir)
                        .stdout(Stdio::inherit())
                        .stderr(Stdio::inherit())
                        .spawn()
                    {
                        Ok(_) => println!("[Scheduler] Started (dev mode)"),
                        Err(e) => println!("[Scheduler] Failed: {}", e),
                    }
                }
            });
            
            // Note: VM is NOT auto-started anymore
            // VM will be started when user creates an agent through the onboarding flow
            // or when selecting an existing agent
            
            Ok(())
        })
        .on_window_event(|window, event| {
            // macOS: Hide window on close instead of quitting
            #[cfg(target_os = "macos")]
            if let WindowEvent::CloseRequested { api, .. } = event {
                api.prevent_close();
                let _ = window.hide();
                println!("[App] Window hidden (macOS style)");
            }
        })
        .invoke_handler(tauri::generate_handler![
            // VM Setup commands (image download only - VM lifecycle handled by Gateway)
            check_environment,
            check_cloud_image,
            download_cloud_image,
            // VM Deploy commands (wait for VM initialization)
            deploy_agent,
            // Gateway commands
            start_gateway,
            stop_gateway,
            get_gateway_status,
            get_gateway_url,
            // Gateway API proxy
            gateway_get,
            gateway_post,
            gateway_patch,
            gateway_put,
            gateway_delete,
            gateway_health,
        ])
        .build(tauri::generate_context!())
        .expect("error while building tauri application")
        .run(|app_handle, event| {
            match event {
                // Stop services on exit
                tauri::RunEvent::Exit => {
                    println!("[App] Exiting, stopping services...");
                    
                    // Stop service processes (reverse order)
                    // Scheduler
                    if let Some(scheduler) = app_handle.try_state::<SchedulerState>() {
                        let svc_clone = scheduler.inner().clone();
                        tauri::async_runtime::block_on(async {
                            let mut svc = svc_clone.lock().await;
                            svc.stop();
                        });
                    }
                    
                    // Health
                    if let Some(health) = app_handle.try_state::<HealthState>() {
                        let svc_clone = health.inner().clone();
                        tauri::async_runtime::block_on(async {
                            let mut svc = svc_clone.lock().await;
                            svc.stop();
                        });
                    }
                    
                    // Saga Worker
                    if let Some(saga_worker) = app_handle.try_state::<SagaWorkerState>() {
                        let svc_clone = saga_worker.inner().clone();
                        tauri::async_runtime::block_on(async {
                            let mut svc = svc_clone.lock().await;
                            svc.stop();
                        });
                    }
                    
                    // Task Worker
                    if let Some(task_worker) = app_handle.try_state::<TaskWorkerState>() {
                        let svc_clone = task_worker.inner().clone();
                        tauri::async_runtime::block_on(async {
                            let mut svc = svc_clone.lock().await;
                            svc.stop();
                        });
                    }
                    
                    // Watchdog
                    if let Some(watchdog) = app_handle.try_state::<WatchdogState>() {
                        let svc_clone = watchdog.inner().clone();
                        tauri::async_runtime::block_on(async {
                            let mut svc = svc_clone.lock().await;
                            svc.stop();
                        });
                    }
                    
                    // Stop Backend 组件: Tools Server
                    if let Some(tools_server) = app_handle.try_state::<ToolsServerState>() {
                        let ts_clone = tools_server.inner().clone();
                        tauri::async_runtime::block_on(async {
                            let mut ts = ts_clone.lock().await;
                            ts.stop();
                        });
                    }
                    
                    // Step 1: 先通过 vmcontrol 发送 shutdown 信号给所有 VM
                    // 这会发送 QMP system_powerdown 命令，让 VM 优雅关闭
                    if let Some(vmcontrol) = app_handle.try_state::<VmControlState>() {
                        let vc_clone = vmcontrol.inner().clone();
                        let shutdown_result = tauri::async_runtime::block_on(async {
                            let vc = vc_clone.lock().await;
                            if vc.is_running() {
                                Some(vc.base_url())
                            } else {
                                None
                            }
                        });
                        
                        if let Some(base_url) = shutdown_result {
                            println!("[App] Sending shutdown signal to all VMs...");
                            let shutdown_url = format!("{}/api/vms/shutdown-all", base_url);
                            if let Ok(client) = reqwest::blocking::Client::builder()
                                .timeout(std::time::Duration::from_secs(5))
                                .build()
                            {
                                match client.post(&shutdown_url).send() {
                                    Ok(resp) => {
                                        if resp.status().is_success() {
                                            println!("[App] VM shutdown signals sent successfully");
                                        } else {
                                            println!("[App] VM shutdown-all returned: {}", resp.status());
                                        }
                                    }
                                    Err(e) => {
                                        println!("[App] VM shutdown-all failed: {}", e);
                                    }
                                }
                            }
                        }
                    }
                    
                    // Step 2: Stop Backend 组件: VmControl
                    if let Some(vmcontrol) = app_handle.try_state::<VmControlState>() {
                        let vc_clone = vmcontrol.inner().clone();
                        tauri::async_runtime::block_on(async {
                            let mut vc = vc_clone.lock().await;
                            vc.stop();
                        });
                    }
                    
                    // Step 3: Stop Backend 组件: Gateway（并停所有 VM 进程）
                    if let Some(gateway) = app_handle.try_state::<GatewayState>() {
                        let gateway_clone = gateway.inner().clone();
                        tauri::async_runtime::block_on(async {
                            let mut gw = gateway_clone.lock().await;
                            gw.stop();
                        });
                    }
                }
                // macOS: Reopen window on Dock click
                tauri::RunEvent::Reopen { has_visible_windows, .. } => {
                    if !has_visible_windows {
                        if let Some(window) = app_handle.get_webview_window("main") {
                            let _ = window.show();
                            let _ = window.set_focus();
                            println!("[App] Window shown (Dock click)");
                        }
                    }
                }
                _ => {}
            }
        });
}
