// Prevents additional console window on Windows in release
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod commands;
mod vm;
mod files;
mod error;
mod app_config;
mod http_client;

use commands::{vm_commands, file_commands, agent_commands, config_commands};
use vm::manager::VmManager;
use std::sync::Arc;
use std::path::PathBuf;
use std::process::{Command, Child, Stdio};
use tokio::sync::Mutex;
use tauri::{
    Manager, 
    WindowEvent,
    tray::TrayIconBuilder,
    menu::{Menu, MenuItem},
};

/// Agent 进程管理
struct AgentProcess {
    child: Option<Child>,
}

impl AgentProcess {
    fn new() -> Self {
        Self { child: None }
    }
    
    fn start(&mut self, agent_dir: &PathBuf) -> Result<(), String> {
        if self.child.is_some() {
            println!("[Agent] Already running");
            return Ok(());
        }
        
        println!("[Agent] Starting Python Agent from {:?}", agent_dir);
        
        // 检查 venv 是否存在（支持 venv 和 .venv 两种命名）
        let venv_python = agent_dir.join("venv/bin/python");
        let dot_venv_python = agent_dir.join(".venv/bin/python");
        let python_cmd = if venv_python.exists() {
            venv_python.to_string_lossy().to_string()
        } else if dot_venv_python.exists() {
            dot_venv_python.to_string_lossy().to_string()
        } else {
            "python3".to_string()
        };
        
        let main_py = agent_dir.join("main.py");
        if !main_py.exists() {
            return Err(format!("Agent main.py not found: {:?}", main_py));
        }
        
        // 启动 Agent 进程
        let child = Command::new(&python_cmd)
            .arg(&main_py)
            .current_dir(agent_dir)
            .env("NBCC_EXECUTOR_URL", "http://127.0.0.1:8080")  // VM Executor (MCP Server)
            .env("NBCC_PORT", "9000")  // Agent 端口
            .env("NBCC_HOST", "127.0.0.1")
            .stdout(Stdio::inherit())
            .stderr(Stdio::inherit())
            .spawn()
            .map_err(|e| format!("Failed to start Agent: {}", e))?;
        
        println!("[Agent] Started with PID: {}", child.id());
        self.child = Some(child);
        Ok(())
    }
    
    fn stop(&mut self) {
        if let Some(mut child) = self.child.take() {
            println!("[Agent] Stopping Agent (PID: {})", child.id());
            let _ = child.kill();
            let _ = child.wait();
            println!("[Agent] Agent stopped");
        }
    }
}

impl Drop for AgentProcess {
    fn drop(&mut self) {
        self.stop();
    }
}

fn main() {
    // 设置 NO_PROXY 环境变量，让本地地址不走系统代理
    // reqwest 和其他 HTTP 库会自动读取这个环境变量
    std::env::set_var("NO_PROXY", "localhost,127.0.0.1,::1,10.0.0.0/8,172.16.0.0/12,192.168.0.0/16");
    std::env::set_var("no_proxy", "localhost,127.0.0.1,::1,10.0.0.0/8,172.16.0.0/12,192.168.0.0/16");
    
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_fs::init())
        .plugin(tauri_plugin_process::init())
        .setup(|app| {
            println!("NB-CC starting...");
            
            // 创建托盘菜单 - macOS 上左键点击托盘图标会显示此菜单
            let show_item = MenuItem::with_id(app, "show", "显示窗口", true, None::<&str>)?;
            let quit_item = MenuItem::with_id(app, "quit", "退出", true, None::<&str>)?;
            let menu = Menu::with_items(app, &[&show_item, &quit_item])?;
            
            // 创建托盘图标
            // macOS: 左键点击显示菜单，通过菜单操作窗口
            let tray = TrayIconBuilder::with_id("main-tray")
                .icon(app.default_window_icon().unwrap().clone())
                .menu(&menu)
                .menu_on_left_click(true)  // macOS 标准行为：左键显示菜单
                .tooltip("NB-CC - 点击显示菜单")
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
                            // Agent 会在 Drop 时自动停止
                            let _ = Command::new("pkill")
                                .args(["-f", "qemu-system"])
                                .output();
                            std::process::exit(0);
                        }
                        _ => {}
                    }
                })
                .build(app)?;
            
            // 存储托盘引用到 app state 防止被 drop
            app.manage(tray);
            
            // 确定 VM 目录路径 (packages/novaic-vm 目录)
            let vm_dir = if cfg!(debug_assertions) {
                // 开发模式: 使用 packages/novaic-vm 目录
                // CARGO_MANIFEST_DIR = packages/novaic-app/src-tauri
                // 需要向上到 packages 目录，然后进入 novaic-vm
                let manifest_dir = PathBuf::from(env!("CARGO_MANIFEST_DIR"));
                let vm_path = manifest_dir
                    .parent()  // packages/novaic-app
                    .and_then(|p| p.parent())  // packages
                    .map(|p| p.join("novaic-vm"))
                    .unwrap_or_else(|| PathBuf::from("../novaic-vm"));
                println!("Development mode - VM directory: {:?}", vm_path);
                vm_path
            } else {
                // 生产模式: 使用 app data 目录
                let app_dir = app.path().app_data_dir()
                    .unwrap_or_else(|_| PathBuf::from("."));
                let vm_path = app_dir.join("runtime");
                std::fs::create_dir_all(&vm_path).ok();
                println!("Production mode - VM directory: {:?}", vm_path);
                vm_path
            };
            
            println!("VM directory: {:?}", vm_dir);
            
            // 初始化 VM Manager 并注入到 app state
            let vm_manager = Arc::new(Mutex::new(VmManager::new(vm_dir.clone())));
            app.manage(vm_manager.clone());
            
            // 初始化 Agent 进程管理
            let agent_process = Arc::new(std::sync::Mutex::new(AgentProcess::new()));
            app.manage(agent_process.clone());
            
            // 确定 Agent 目录
            let agent_dir = if cfg!(debug_assertions) {
                // CARGO_MANIFEST_DIR = packages/novaic-app/src-tauri
                // Agent 在 packages/novaic-agent
                let manifest_dir = PathBuf::from(env!("CARGO_MANIFEST_DIR"));
                manifest_dir.parent().and_then(|p| p.parent())  // packages
                    .map(|p| p.join("novaic-agent"))
                    .unwrap_or_else(|| PathBuf::from("../../novaic-agent"))
            } else {
                vm_dir.parent().map(|p| p.join("novaic-agent")).unwrap_or_else(|| PathBuf::from("novaic-agent"))
            };
            
            // 启动 Python Agent (宿主机)
            println!("[Agent] Starting Python Agent on host...");
            {
                let mut agent = agent_process.lock().unwrap();
                match agent.start(&agent_dir) {
                    Ok(_) => println!("[Agent] Python Agent started on host"),
                    Err(e) => println!("[Agent] Failed to start Agent: {}", e),
                }
            }
            
            // 自动启动 QEMU VM (在后台异步执行)
            println!("[VM] Auto-starting QEMU VM...");
            let vm_manager_for_start = vm_manager.clone();
            tauri::async_runtime::spawn(async move {
                let manager = vm_manager_for_start.lock().await;
                match manager.start().await {
                    Ok(_) => println!("[VM] QEMU VM started successfully"),
                    Err(e) => println!("[VM] Failed to start QEMU VM: {}", e),
                }
            });
            
            Ok(())
        })
        .on_window_event(|window, event| {
            // macOS 标准交互：点击红色 X 只隐藏窗口，不退出 App
            #[cfg(target_os = "macos")]
            if let WindowEvent::CloseRequested { api, .. } = event {
                // 阻止默认的关闭行为
                api.prevent_close();
                // 隐藏窗口
                let _ = window.hide();
                println!("[App] Window hidden (macOS style)");
            }
        })
        .invoke_handler(tauri::generate_handler![
            // VM commands
            vm_commands::start_vm,
            vm_commands::stop_vm,
            vm_commands::get_vm_status,
            vm_commands::restart_vm,
            vm_commands::get_vnc_url,
            vm_commands::get_agent_url,
            // Agent commands
            agent_commands::init_agent,
            agent_commands::init_agent_with_app_config,
            agent_commands::send_message,
            agent_commands::send_message_stream,
            agent_commands::get_health,
            // Config commands
            config_commands::get_app_config,
            config_commands::update_common_settings,
            config_commands::add_api_key,
            config_commands::update_api_key,
            config_commands::delete_api_key,
            config_commands::toggle_model,
            config_commands::set_default_model,
            config_commands::fetch_models_for_key,
            config_commands::save_models_for_key,
            config_commands::test_api_key_connection,
            config_commands::test_llm_connection,
            // File commands
            file_commands::upload_file,
            file_commands::download_file,
            file_commands::list_vm_files,
        ])
        .build(tauri::generate_context!())
        .expect("error while building tauri application")
        .run(|app_handle, event| {
            match event {
                // Cmd+Q 或真正退出时停止 QEMU 和 Agent
                tauri::RunEvent::Exit => {
                    println!("[App] Exiting, stopping services...");
                    
                    // 停止 Agent
                    if let Some(agent_process) = app_handle.try_state::<Arc<std::sync::Mutex<AgentProcess>>>() {
                        let mut agent = agent_process.lock().unwrap();
                        agent.stop();
                    }
                    
                    // 停止 QEMU
                    println!("[VM] Stopping QEMU VM...");
                    let _ = Command::new("pkill")
                        .args(["-f", "qemu-system"])
                        .output();
                    println!("[VM] QEMU VM stop command sent");
                }
                // macOS: 点击 Dock 图标重新打开窗口 (Tauri 2.0 支持!)
                tauri::RunEvent::Reopen { has_visible_windows, .. } => {
                    if !has_visible_windows {
                        if let Some(window) = app_handle.get_webview_window("main") {
                            let _ = window.show();
                            let _ = window.set_focus();
                            println!("[App] Window shown (Dock click - Reopen)");
                        }
                    }
                }
                _ => {}
            }
        });
}
