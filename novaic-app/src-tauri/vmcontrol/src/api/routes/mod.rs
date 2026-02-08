pub mod vm;
pub mod health;
pub mod input;
pub mod screen;
pub mod guest;
pub mod vnc;
pub mod browser;
pub mod vmuse;

use axum::{Router, routing::{get, post}};
use std::sync::Arc;
use tokio::sync::RwLock;
use std::collections::HashMap;

/// Application state shared across all routes
pub type AppState = Arc<RwLock<HashMap<String, vm::VmManager>>>;

/// Create the main API router with all routes
pub fn create_router(state: AppState) -> Router {
    Router::new()
        .route("/health", get(health::health_check))
        .route("/api/vms", get(vm::list_vms).post(vm::register_vm))
        .route("/api/vms/:id", get(vm::get_vm))
        .route("/api/vms/:id/pause", post(vm::pause_vm))
        .route("/api/vms/:id/resume", post(vm::resume_vm))
        .route("/api/vms/:id/shutdown", post(vm::shutdown_vm))
        .route("/api/vms/shutdown-all", post(vm::shutdown_all_vms))
        // Screenshot and input endpoints
        .route("/api/vms/:id/screenshot", post(screen::screenshot))
        .route("/api/vms/:id/input/keyboard", post(input::keyboard_input))
        .route("/api/vms/:id/input/mouse", post(input::mouse_input))
        // Guest Agent endpoints
        .route("/api/vms/:id/guest/exec", post(guest::exec_command))
        .route("/api/vms/:id/guest/file", get(guest::read_file).post(guest::write_file))
        // Browser control endpoints
        .route("/api/vms/:id/browser/navigate", post(browser::navigate))
        .route("/api/vms/:id/browser/click", post(browser::click))
        .route("/api/vms/:id/browser/type", post(browser::type_text))
        .route("/api/vms/:id/browser/content", get(browser::get_content))
        .route("/api/vms/:id/browser/screenshot", post(browser::screenshot))
        // VMUSE Generic Proxy - supports all tools (browser, desktop, shell, files, etc.)
        .route("/api/vms/:id/vmuse/:tool/:operation", post(vmuse::vmuse_proxy))
        // VNC WebSocket endpoint
        .route("/api/vms/:id/vnc", get(vnc::vnc_websocket))
        .with_state(state)
}
