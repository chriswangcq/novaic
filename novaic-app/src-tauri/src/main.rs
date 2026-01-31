// Prevents additional console window on Windows in release
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod vm;
mod error;
mod commands;
mod http_client;
mod gateway_client;

use gateway_client::GatewayClient;

// VM management is now handled by Gateway - Tauri only handles:
// - Gateway process management
// - Cloud image download (optional)
use vm::setup::{check_environment, check_cloud_image, download_cloud_image};
use vm::deploy::{deploy_agent, quick_deploy_agent};

use std::sync::Arc;
use std::path::PathBuf;
use std::process::{Child, Command, Stdio};
use tokio::sync::Mutex;
use tauri::{
    AppHandle,
    Manager, 
    WindowEvent,
    tray::TrayIconBuilder,
    menu::{Menu, MenuItem},
};

/// Gateway process manager
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

/// Worker process manager
/// Workers are separate processes that connect to Gateway via SSE
/// and execute tasks (think, tool_call, reply)
struct WorkerProcess {
    process: Option<Child>,
    worker_id: String,
    gateway_url: String,
}

impl WorkerProcess {
    fn new(worker_id: &str, gateway_url: &str) -> Self {
        Self {
            process: None,
            worker_id: worker_id.to_string(),
            gateway_url: gateway_url.to_string(),
        }
    }

    fn start(&mut self, worker_path: &PathBuf, is_binary: bool, gateway_dir: Option<&PathBuf>) -> Result<(), String> {
        if self.process.is_some() {
            println!("[Worker:{}] Already running", self.worker_id);
            return Ok(());
        }

        println!("[Worker:{}] Starting Worker from {:?}", self.worker_id, worker_path);
        println!("[Worker:{}] Gateway URL: {}", self.worker_id, self.gateway_url);
        println!("[Worker:{}] Mode: {}", self.worker_id, if is_binary { "binary" } else { "python" });

        let child = if is_binary {
            // Production mode: run bundled binary
            if !worker_path.exists() {
                return Err(format!("Worker binary not found at {:?}", worker_path));
            }
            
            Command::new(worker_path)
                .arg("--gateway")
                .arg(&self.gateway_url)
                .arg("--worker-id")
                .arg(&self.worker_id)
                .arg("--max-concurrent")
                .arg("10")
                .env("NO_PROXY", "localhost,127.0.0.1,::1")
                .env("no_proxy", "localhost,127.0.0.1,::1")
                .stdout(Stdio::null())
                .stderr(Stdio::null())
                .spawn()
                .map_err(|e| format!("Failed to start Worker binary: {}", e))?
        } else {
            // Development mode: run Python with venv
            let gateway_dir = gateway_dir.ok_or("Gateway dir required for dev mode")?;
            let venv_python = gateway_dir.join("venv/bin/python");
            let python = if venv_python.exists() {
                venv_python.to_string_lossy().to_string()
            } else if cfg!(target_os = "windows") {
                "python".to_string()
            } else {
                "python3".to_string()
            };

            println!("[Worker:{}] Using Python: {}", self.worker_id, python);

            Command::new(&python)
                .arg("-m")
                .arg("worker.worker")
                .arg("--gateway")
                .arg(&self.gateway_url)
                .arg("--worker-id")
                .arg(&self.worker_id)
                .arg("--max-concurrent")
                .arg("10")
                .current_dir(gateway_dir)
                .env("NO_PROXY", "localhost,127.0.0.1,::1")
                .env("no_proxy", "localhost,127.0.0.1,::1")
                .stdout(Stdio::inherit())
                .stderr(Stdio::inherit())
                .spawn()
                .map_err(|e| format!("Failed to start Worker: {}", e))?
        };

        self.process = Some(child);
        println!("[Worker:{}] Started", self.worker_id);
        Ok(())
    }

    fn stop(&mut self) {
        if let Some(mut process) = self.process.take() {
            let pid = process.id();
            println!("[Worker:{}] Stopping process (PID: {})...", self.worker_id, pid);
            
            // Send SIGTERM for graceful shutdown
            #[cfg(unix)]
            unsafe {
                libc::kill(pid as i32, libc::SIGTERM);
            }
            
            // Wait briefly for graceful shutdown
            std::thread::sleep(std::time::Duration::from_millis(500));
            
            // Check if process exited
            match process.try_wait() {
                Ok(Some(status)) => {
                    println!("[Worker:{}] Stopped gracefully with status: {:?}", self.worker_id, status);
                    return;
                }
                Ok(None) => {
                    // Still running, force kill
                    println!("[Worker:{}] Process still running, sending SIGKILL...", self.worker_id);
                    let _ = process.kill();
                    let _ = process.wait();
                    println!("[Worker:{}] Force killed", self.worker_id);
                }
                Err(e) => {
                    println!("[Worker:{}] Error checking process status: {}", self.worker_id, e);
                    let _ = process.kill();
                }
            }
        }
    }

    fn is_running(&mut self) -> bool {
        if let Some(ref mut process) = self.process {
            match process.try_wait() {
                Ok(Some(_)) => {
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

impl Drop for WorkerProcess {
    fn drop(&mut self) {
        self.stop();
    }
}

impl GatewayProcess {

    fn start(&mut self, gateway_path: &PathBuf, is_binary: bool, data_dir: &PathBuf, resource_dir: Option<&PathBuf>) -> Result<(), String> {
        if self.process.is_some() {
            println!("[Gateway] Already running");
            return Ok(());
        }

        println!("[Gateway] Starting Gateway from {:?}", gateway_path);
        println!("[Gateway] Port: {}", self.port);
        println!("[Gateway] Data dir: {:?}", data_dir);
        println!("[Gateway] Resource dir: {:?}", resource_dir);
        println!("[Gateway] Mode: {}", if is_binary { "binary" } else { "python" });

        let data_dir_str = data_dir.to_string_lossy().to_string();
        let resource_dir_str = resource_dir.map(|p| p.to_string_lossy().to_string()).unwrap_or_default();

        let child = if is_binary {
            // Production mode: run bundled binary
            if !gateway_path.exists() {
                return Err(format!("Gateway binary not found at {:?}", gateway_path));
            }
            
            Command::new(gateway_path)
                .env("NOVAIC_PORT", self.port.to_string())
                .env("NOVAIC_HOST", "127.0.0.1")
                .env("NOVAIC_DATA_DIR", &data_dir_str)
                .env("NOVAIC_RESOURCE_DIR", &resource_dir_str)
                .env("NO_PROXY", "localhost,127.0.0.1,::1")
                .env("no_proxy", "localhost,127.0.0.1,::1")
                // Use null to discard output - prevents pipe buffer from filling up
                .stdout(Stdio::null())
                .stderr(Stdio::null())
                .spawn()
                .map_err(|e| format!("Failed to start Gateway binary: {}", e))?
        } else {
            // Development mode: run Python with venv
            let gateway_dir = gateway_path;
            let venv_python = gateway_dir.join("venv/bin/python");
            let python = if venv_python.exists() {
                venv_python.to_string_lossy().to_string()
            } else if cfg!(target_os = "windows") {
                "python".to_string()
            } else {
                "python3".to_string()
            };

            let main_py = gateway_dir.join("main.py");
            if !main_py.exists() {
                return Err(format!("Gateway main.py not found at {:?}", main_py));
            }

            println!("[Gateway] Using Python: {}", python);

            Command::new(&python)
                .arg(&main_py)
                .current_dir(gateway_dir)
                .env("NOVAIC_PORT", self.port.to_string())
                .env("NOVAIC_HOST", "127.0.0.1")
                .env("NOVAIC_DATA_DIR", &data_dir_str)
                .env("NOVAIC_RESOURCE_DIR", &resource_dir_str)
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
                .timeout(std::time::Duration::from_secs(10))  // Short timeout for quick mode
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

type GatewayState = Arc<Mutex<GatewayProcess>>;
type WorkerState = Arc<Mutex<WorkerProcess>>;

/// Get Gateway path and whether it's a binary
/// Returns (path, is_binary)
fn get_gateway_info(app: &AppHandle) -> (PathBuf, bool) {
    // Try to use bundled binary first (production mode)
    // onedir mode: binary is at novaic-gateway/novaic-gateway (relative to resource_dir)
    if let Ok(resource_dir) = app.path().resource_dir() {
        // Check onedir structure first (novaic-gateway/novaic-gateway)
        let onedir_path = resource_dir.join("novaic-gateway/novaic-gateway");
        println!("[Gateway] Checking onedir binary at: {:?}", onedir_path);
        if onedir_path.exists() {
            println!("[Gateway] Found onedir binary, using production mode");
            return (onedir_path, true);
        }
        
        // Fallback: check single file (legacy onefile mode)
        let binary_path = resource_dir.join("novaic-gateway");
        println!("[Gateway] Checking single file binary at: {:?}", binary_path);
        if binary_path.is_file() {
            println!("[Gateway] Found single file binary, using production mode");
            return (binary_path, true);
        }
        println!("[Gateway] Bundled binary not found");
    } else {
        println!("[Gateway] Could not get resource_dir");
    }
    
    // Fallback to development mode - check relative to executable
    // In dev mode, executable is at: novaic-app/src-tauri/target/release/novaic
    // Gateway source is at: novaic-gateway (4 levels up from executable)
    if let Ok(exe_path) = std::env::current_exe() {
        if let Some(exe_dir) = exe_path.parent() {
            // exe_dir = .../novaic-app/src-tauri/target/release/
            // Go up 4 levels to project root, then into novaic-gateway
            let dev_path = exe_dir
                .join("../../../..")  // Go to project root (novaic/)
                .join("novaic-gateway");
            
            if dev_path.exists() && dev_path.join("main.py").exists() {
                let canonical = dev_path.canonicalize().unwrap_or(dev_path);
                println!("[Gateway] Using development source: {:?}", canonical);
                return (canonical, false);
            }
            println!("[Gateway] Dev path not found: {:?}", dev_path);
        }
    }
    
    println!("[Gateway] ERROR: No gateway found! Please ensure novaic-gateway is bundled with the app.");
    (PathBuf::from("/tmp/novaic-gateway-not-found"), false)
}

/// Get Worker path and whether it's a binary
/// Returns (path, is_binary, gateway_dir_for_dev)
fn get_worker_info(app: &AppHandle) -> (PathBuf, bool, Option<PathBuf>) {
    // Try to use bundled binary first (production mode)
    if let Ok(resource_dir) = app.path().resource_dir() {
        // Check onedir structure (novaic-worker/novaic-worker)
        let onedir_path = resource_dir.join("novaic-worker/novaic-worker");
        println!("[Worker] Checking onedir binary at: {:?}", onedir_path);
        if onedir_path.exists() {
            println!("[Worker] Found onedir binary, using production mode");
            return (onedir_path, true, None);
        }
        
        // Fallback: check single file
        let binary_path = resource_dir.join("novaic-worker");
        println!("[Worker] Checking single file binary at: {:?}", binary_path);
        if binary_path.is_file() {
            println!("[Worker] Found single file binary, using production mode");
            return (binary_path, true, None);
        }
        println!("[Worker] Bundled binary not found");
    }
    
    // Fallback to development mode - use gateway dir for Python module
    if let Ok(exe_path) = std::env::current_exe() {
        if let Some(exe_dir) = exe_path.parent() {
            let dev_path = exe_dir
                .join("../../../..")
                .join("novaic-gateway");
            
            if dev_path.exists() && dev_path.join("worker/worker.py").exists() {
                let canonical = dev_path.canonicalize().unwrap_or(dev_path.clone());
                println!("[Worker] Using development mode, gateway dir: {:?}", canonical);
                return (canonical.clone(), false, Some(canonical));
            }
            println!("[Worker] Dev path not found: {:?}", dev_path);
        }
    }
    
    println!("[Worker] ERROR: No worker found!");
    (PathBuf::from("/tmp/novaic-worker-not-found"), false, None)
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
    let gw = gateway.lock().await;
    let client = GatewayClient::new(gw.base_url());
    client.get(&path).await
}

/// Tauri command: Gateway API POST request
#[tauri::command]
async fn gateway_post(
    gateway: tauri::State<'_, GatewayState>,
    path: String,
    body: Option<serde_json::Value>,
) -> Result<serde_json::Value, String> {
    let gw = gateway.lock().await;
    let client = GatewayClient::new(gw.base_url());
    client.post(&path, body).await
}

/// Tauri command: Gateway API PATCH request
#[tauri::command]
async fn gateway_patch(
    gateway: tauri::State<'_, GatewayState>,
    path: String,
    body: Option<serde_json::Value>,
) -> Result<serde_json::Value, String> {
    let gw = gateway.lock().await;
    let client = GatewayClient::new(gw.base_url());
    client.patch(&path, body).await
}

/// Tauri command: Gateway API DELETE request
#[tauri::command]
async fn gateway_delete(
    gateway: tauri::State<'_, GatewayState>,
    path: String,
) -> Result<serde_json::Value, String> {
    let gw = gateway.lock().await;
    let client = GatewayClient::new(gw.base_url());
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
            
            // Create tray icon
            let _tray = TrayIconBuilder::with_id("main-tray")
                .icon(app.default_window_icon().unwrap().clone())
                .menu(&menu)
                .show_menu_on_left_click(true)
                .tooltip("NovAIC")
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
            
            // Initialize Gateway Manager (VM management is now handled by Gateway)
            let gateway = Arc::new(Mutex::new(GatewayProcess::new()));
            app.manage(gateway.clone());
            
            // Initialize Worker Manager
            let gateway_url = {
                let gw = tauri::async_runtime::block_on(async { gateway.lock().await });
                gw.base_url()
            };
            let worker = Arc::new(Mutex::new(WorkerProcess::new("worker-1", &gateway_url)));
            app.manage(worker.clone());
            
            // Auto-start Gateway and Worker
            let (gateway_path, is_binary) = get_gateway_info(app.handle());
            let (worker_path, worker_is_binary, gateway_dir_for_worker) = get_worker_info(app.handle());
            let resource_dir = app.path().resource_dir().ok();
            
            println!("[Gateway] Gateway path: {:?}", gateway_path);
            println!("[Gateway] Resource dir: {:?}", resource_dir);
            println!("[Gateway] Is binary: {}", is_binary);
            println!("[Worker] Worker path: {:?}", worker_path);
            println!("[Worker] Is binary: {}", worker_is_binary);
            
            let gateway_for_start = gateway.clone();
            let worker_for_start = worker.clone();
            let data_dir_for_gateway = data_dir.clone();
            
            tauri::async_runtime::spawn(async move {
                // Start Gateway first
                {
                    let mut gw = gateway_for_start.lock().await;
                    match gw.start(&gateway_path, is_binary, &data_dir_for_gateway, resource_dir.as_ref()) {
                        Ok(_) => println!("[Gateway] Auto-started successfully"),
                        Err(e) => {
                            println!("[Gateway] Failed to auto-start: {}", e);
                            return;
                        }
                    }
                }
                
                // Wait for Gateway to be ready (health check)
                println!("[Worker] Waiting for Gateway to be ready...");
                let client = reqwest::Client::new();
                let health_url = format!("{}/api/health", gateway_url);
                
                for i in 0..30 {  // Wait up to 30 seconds
                    tokio::time::sleep(tokio::time::Duration::from_secs(1)).await;
                    
                    match client.get(&health_url).send().await {
                        Ok(resp) if resp.status().is_success() => {
                            println!("[Worker] Gateway is ready after {}s", i + 1);
                            break;
                        }
                        _ => {
                            if i == 29 {
                                println!("[Worker] Gateway not ready after 30s, starting Worker anyway");
                            }
                        }
                    }
                }
                
                // Start Worker (only in production mode, dev mode Gateway handles it via ProcessManager)
                if worker_is_binary {
                    let mut wk = worker_for_start.lock().await;
                    match wk.start(&worker_path, worker_is_binary, gateway_dir_for_worker.as_ref()) {
                        Ok(_) => println!("[Worker] Auto-started successfully"),
                        Err(e) => println!("[Worker] Failed to auto-start: {}", e),
                    }
                } else {
                    // In dev mode, ProcessManager in Gateway will spawn workers
                    // But we can also start one here for redundancy
                    let mut wk = worker_for_start.lock().await;
                    match wk.start(&worker_path, worker_is_binary, gateway_dir_for_worker.as_ref()) {
                        Ok(_) => println!("[Worker] Auto-started successfully (dev mode)"),
                        Err(e) => println!("[Worker] Failed to auto-start (dev mode): {}", e),
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
            // VM Deploy commands (SSH deploy to VM)
            deploy_agent,
            quick_deploy_agent,
            // Gateway commands
            start_gateway,
            stop_gateway,
            get_gateway_status,
            get_gateway_url,
            // Gateway API proxy
            gateway_get,
            gateway_post,
            gateway_patch,
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
                    
                    // Stop Worker first (it depends on Gateway)
                    if let Some(worker) = app_handle.try_state::<WorkerState>() {
                        let worker_clone = worker.inner().clone();
                        tauri::async_runtime::block_on(async {
                            let mut wk = worker_clone.lock().await;
                            wk.stop();
                        });
                    }
                    
                    // Stop Gateway (which will also stop all VMs)
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
