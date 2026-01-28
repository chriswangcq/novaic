use crate::vm::manager::{VmManager, VmStatus};
use std::sync::Arc;
use std::path::PathBuf;
use tauri::State;
use tokio::sync::Mutex;

/// 全局 VM Manager 状态
pub type VmManagerState = Arc<Mutex<VmManager>>;

/// Start the virtual machine
/// If agent_id is provided, uses the agent's VM directory
#[tauri::command]
pub async fn start_vm(
    vm_manager: State<'_, VmManagerState>,
    agent_id: Option<String>,
) -> Result<String, String> {
    println!("[Command] start_vm called, agent_id: {:?}", agent_id);
    
    let manager = vm_manager.lock().await;
    
    // 检查是否已在运行
    let is_running = manager.is_running().await;
    println!("[Command] is_running: {}", is_running);
    if is_running {
        return Err("VM is already running".to_string());
    }
    
    // 如果提供了 agent_id，设置镜像路径和 agent_id
    if let Some(ref id) = agent_id {
        let agent_disk = manager.vm_dir().join(id).join("disk.qcow2");
        if agent_disk.exists() {
            println!("[Command] Using agent disk: {:?}", agent_disk);
            manager.set_image_path(agent_disk.to_str().map(|s| s.to_string())).await;
            // Set current agent ID so status can be tracked
            manager.set_agent_id(agent_id.clone()).await;
        } else {
            return Err(format!("Agent disk not found: {:?}", agent_disk));
        }
    }
    
    // 启动 VM
    println!("[Command] Calling manager.start()...");
    match manager.start().await {
        Ok(()) => {
            println!("[Command] VM started successfully");
            Ok("VM started successfully".to_string())
        }
        Err(e) => {
            println!("[Command] VM start failed: {}", e);
            Err(e)
        }
    }
}

/// Stop the virtual machine
#[tauri::command]
pub async fn stop_vm(
    vm_manager: State<'_, VmManagerState>,
) -> Result<String, String> {
    println!("[Command] stop_vm called");
    
    let manager = vm_manager.lock().await;
    manager.stop().await?;
    
    // Clear agent ID when stopped
    manager.set_agent_id(None).await;
    
    Ok("VM stopped successfully".to_string())
}

/// Get VM status
#[tauri::command]
pub async fn get_vm_status(
    vm_manager: State<'_, VmManagerState>,
) -> Result<VmStatus, String> {
    let manager = vm_manager.lock().await;
    Ok(manager.get_status().await)
}

/// Restart the virtual machine
#[tauri::command]
pub async fn restart_vm(
    vm_manager: State<'_, VmManagerState>,
) -> Result<String, String> {
    println!("[Command] restart_vm called");
    
    let manager = vm_manager.lock().await;
    
    // 先停止
    if manager.is_running().await {
        manager.stop().await?;
        // 等待完全停止
        tokio::time::sleep(tokio::time::Duration::from_secs(2)).await;
    }
    
    // 再启动
    manager.start().await?;
    
    Ok("VM restarted successfully".to_string())
}

/// Get VNC WebSocket URL
#[tauri::command]
pub async fn get_vnc_url(
    vm_manager: State<'_, VmManagerState>,
) -> Result<String, String> {
    let manager = vm_manager.lock().await;
    Ok(manager.get_vnc_url().await)
}

/// Get Agent API URL
#[tauri::command]
pub async fn get_agent_url(
    vm_manager: State<'_, VmManagerState>,
) -> Result<String, String> {
    let manager = vm_manager.lock().await;
    Ok(manager.get_agent_url().await)
}
