// Prevents additional console window on Windows in release
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod vm;
mod error;
mod commands;
mod http_client;
mod gateway_client;

use gateway_client::GatewayClient;

use vm::manager::VmManager;
use vm::setup::{check_cloud_image, download_cloud_image, setup_vm, get_ssh_pubkey, generate_ssh_key};
use vm::deploy::{deploy_agent, quick_deploy_agent};
use commands::vm_commands::{start_vm, stop_vm, get_vm_status, restart_vm, get_vnc_url, get_agent_url};

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
            port: 9000,
        }
    }

    fn base_url(&self) -> String {
        format!("http://127.0.0.1:{}", self.port)
    }

    fn start(&mut self, gateway_path: &PathBuf, is_binary: bool) -> Result<(), String> {
        if self.process.is_some() {
            println!("[Gateway] Already running");
            return Ok(());
        }

        println!("[Gateway] Starting Gateway from {:?}", gateway_path);
        println!("[Gateway] Port: {}", self.port);
        println!("[Gateway] Mode: {}", if is_binary { "binary" } else { "python" });

        let child = if is_binary {
            // Production mode: run bundled binary
            if !gateway_path.exists() {
                return Err(format!("Gateway binary not found at {:?}", gateway_path));
            }
            
            Command::new(gateway_path)
                .env("NOVAIC_PORT", self.port.to_string())
                .env("NOVAIC_HOST", "127.0.0.1")
                .env("NO_PROXY", "localhost,127.0.0.1,::1")
                .env("no_proxy", "localhost,127.0.0.1,::1")
                .stdout(Stdio::piped())
                .stderr(Stdio::piped())
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
                .env("NO_PROXY", "localhost,127.0.0.1,::1")
                .env("no_proxy", "localhost,127.0.0.1,::1")
                .stdout(Stdio::piped())
                .stderr(Stdio::piped())
                .spawn()
                .map_err(|e| format!("Failed to start Gateway: {}", e))?
        };

        self.process = Some(child);
        println!("[Gateway] Started on port {}", self.port);
        Ok(())
    }

    fn stop(&mut self) {
        if let Some(mut process) = self.process.take() {
            println!("[Gateway] Stopping...");
            let _ = process.kill();
            // 不阻塞等待，避免退出时卡死
            // 使用 try_wait 检查是否已退出，但不阻塞
            match process.try_wait() {
                Ok(Some(_)) => println!("[Gateway] Stopped immediately"),
                _ => println!("[Gateway] Kill signal sent, not waiting"),
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

/// Get Gateway path and whether it's a binary
/// Returns (path, is_binary)
fn get_gateway_info(app: &AppHandle) -> (PathBuf, bool) {
    // Try to use bundled binary first (production mode)
    if let Ok(resource_dir) = app.path().resource_dir() {
        let binary_path = resource_dir.join("resources/novaic-gateway");
        println!("[Gateway] Checking bundled binary at: {:?}", binary_path);
        if binary_path.exists() {
            println!("[Gateway] Found bundled binary, using production mode");
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

/// Tauri command: Start Gateway
#[tauri::command]
async fn start_gateway(
    gateway: tauri::State<'_, GatewayState>,
    app: AppHandle,
) -> Result<String, String> {
    let (gateway_path, is_binary) = get_gateway_info(&app);
    let mut gw = gateway.lock().await;
    gw.start(&gateway_path, is_binary)?;
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
                            println!("[App] Quit from tray, stopping services...");
                            std::process::exit(0);
                        }
                        _ => {}
                    }
                })
                .build(app)?;
            
            // VM directory path - use app data directory
            let vm_dir = app.path().app_data_dir()
                .unwrap_or_else(|_| PathBuf::from("."))
                .join("vms");
            
            println!("[App] VM directory: {:?}", vm_dir);
            
            // Initialize VM Manager (but don't auto-start VM)
            let vm_manager = Arc::new(Mutex::new(VmManager::new(vm_dir.clone())));
            app.manage(vm_manager.clone());
            
            // Initialize Gateway Manager
            let gateway = Arc::new(Mutex::new(GatewayProcess::new()));
            app.manage(gateway.clone());
            
            // Auto-start Gateway only
            let (gateway_path, is_binary) = get_gateway_info(app.handle());
            println!("[Gateway] Gateway path: {:?}", gateway_path);
            println!("[Gateway] Is binary: {}", is_binary);
            
            let gateway_for_start = gateway.clone();
            tauri::async_runtime::spawn(async move {
                let mut gw = gateway_for_start.lock().await;
                match gw.start(&gateway_path, is_binary) {
                    Ok(_) => println!("[Gateway] Auto-started successfully"),
                    Err(e) => println!("[Gateway] Failed to auto-start: {}", e),
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
            // VM commands
            start_vm,
            stop_vm,
            get_vm_status,
            restart_vm,
            get_vnc_url,
            get_agent_url,
            // VM Setup commands
            check_cloud_image,
            download_cloud_image,
            setup_vm,
            get_ssh_pubkey,
            generate_ssh_key,
            // VM Deploy commands
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
                    
                    // Stop Gateway
                    if let Some(gateway) = app_handle.try_state::<GatewayState>() {
                        let gateway_clone = gateway.inner().clone();
                        tauri::async_runtime::block_on(async {
                            let mut gw = gateway_clone.lock().await;
                            gw.stop();
                        });
                    }
                    
                    // Stop QEMU
                    println!("[VM] Stopping QEMU VM...");
                    let _ = Command::new("pkill")
                        .args(["-f", "qemu-system"])
                        .output();
                    println!("[VM] QEMU VM stop command sent");
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
