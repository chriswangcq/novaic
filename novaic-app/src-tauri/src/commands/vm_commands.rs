use crate::vm::manager::{VmManager, VmStatus};
use std::sync::Arc;
use tauri::State;
use tokio::sync::Mutex;

/// 全局 VM Manager 状态
pub type VmManagerState = Arc<Mutex<VmManager>>;

/// Start the virtual machine
#[tauri::command]
pub async fn start_vm(
    vm_manager: State<'_, VmManagerState>,
) -> Result<String, String> {
    println!("[Command] start_vm called");
    
    let manager = vm_manager.lock().await;
    
    // 检查是否已在运行
    if manager.is_running().await {
        return Err("VM is already running".to_string());
    }
    
    // 启动 VM
    manager.start().await?;
    
    Ok("VM started successfully".to_string())
}

/// Stop the virtual machine
#[tauri::command]
pub async fn stop_vm(
    vm_manager: State<'_, VmManagerState>,
) -> Result<String, String> {
    println!("[Command] stop_vm called");
    
    let manager = vm_manager.lock().await;
    manager.stop().await?;
    
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
