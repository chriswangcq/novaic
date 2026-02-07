use axum::{
    extract::Path,
    http::StatusCode,
    Json,
};
use crate::api::types::{
    ApiError, NavigateRequest, ClickRequest, TypeRequest, BrowserResponse,
};
use crate::qemu::GuestAgentClient;
use base64::{engine::general_purpose, Engine as _};

/// Helper function to execute playwright command
async fn execute_playwright_command(
    vm_id: &str,
    command: &str,
    args: Option<serde_json::Value>,
) -> Result<BrowserResponse, (StatusCode, Json<ApiError>)> {
    let socket_path = format!("/tmp/novaic/novaic-ga-{}.sock", vm_id);
    let mut client = GuestAgentClient::connect(&socket_path).await.map_err(|e| {
        (
            StatusCode::SERVICE_UNAVAILABLE,
            Json(ApiError {
                error: format!("Guest Agent not available: {}", e),
            }),
        )
    })?;

    // Build command arguments for playwright_helper.py
    let mut cmd_args = vec![command.to_string()];
    if let Some(args_val) = args {
        // Escape the JSON string for shell
        let json_str = args_val.to_string().replace("\"", "\\\"");
        cmd_args.push(format!("\"{}\"", json_str));
    }

    // Build command string with DISPLAY=:0 to show browser on real X11 desktop
    // This allows users to see the browser window through VNC, making AI actions visible
    // :0 is the main X11 display where the desktop environment runs
    // Use venv Python to ensure playwright module is available
    let playwright_cmd = format!(
        "DISPLAY=:0 PLAYWRIGHT_BROWSERS_PATH=/opt/novaic/.cache /opt/novaic/venv/bin/python3 /opt/novaic/scripts/playwright_helper.py {}",
        cmd_args.join(" ")
    );

    // Execute playwright helper script via shell on the real X11 desktop
    let status = client
        .exec_sync("/bin/sh", vec!["-c".to_string(), playwright_cmd])
        .await
        .map_err(|e| {
            (
                StatusCode::INTERNAL_SERVER_ERROR,
                Json(ApiError {
                    error: format!("Failed to execute browser command: {}", e),
                }),
            )
        })?;

    // Check exit code
    if let Some(exit_code) = status.exit_code {
        if exit_code != 0 {
            let stderr = status.stderr.and_then(|s| {
                general_purpose::STANDARD
                    .decode(&s)
                    .ok()
                    .and_then(|bytes| String::from_utf8(bytes).ok())
            }).unwrap_or_else(|| "Unknown error".to_string());
            
            return Err((
                StatusCode::INTERNAL_SERVER_ERROR,
                Json(ApiError {
                    error: format!("Browser command failed with exit code {}: {}", exit_code, stderr),
                }),
            ));
        }
    }

    // Parse stdout as JSON
    if let Some(stdout) = status.stdout {
        let output_bytes = general_purpose::STANDARD
            .decode(&stdout)
            .map_err(|e| {
                (
                    StatusCode::INTERNAL_SERVER_ERROR,
                    Json(ApiError {
                        error: format!("Failed to decode output: {}", e),
                    }),
                )
            })?;

        let output = String::from_utf8(output_bytes).map_err(|e| {
            (
                StatusCode::INTERNAL_SERVER_ERROR,
                Json(ApiError {
                    error: format!("Failed to parse output as UTF-8: {}", e),
                }),
            )
        })?;

        let result: BrowserResponse = serde_json::from_str(&output).map_err(|e| {
            (
                StatusCode::INTERNAL_SERVER_ERROR,
                Json(ApiError {
                    error: format!("Failed to parse browser response: {}", e),
                }),
            )
        })?;

        // Check if response contains error
        if let Some(err) = &result.error {
            return Err((
                StatusCode::BAD_REQUEST,
                Json(ApiError {
                    error: err.clone(),
                }),
            ));
        }

        Ok(result)
    } else {
        Err((
            StatusCode::INTERNAL_SERVER_ERROR,
            Json(ApiError {
                error: "No output from browser command".to_string(),
            }),
        ))
    }
}

/// POST /api/vms/:id/browser/navigate
/// Navigate browser to URL
pub async fn navigate(
    Path(vm_id): Path<String>,
    Json(req): Json<NavigateRequest>,
) -> Result<Json<BrowserResponse>, (StatusCode, Json<ApiError>)> {
    let args = serde_json::json!({
        "url": req.url
    });

    let result = execute_playwright_command(&vm_id, "navigate", Some(args)).await?;
    Ok(Json(result))
}

/// POST /api/vms/:id/browser/click
/// Click on element
pub async fn click(
    Path(vm_id): Path<String>,
    Json(req): Json<ClickRequest>,
) -> Result<Json<BrowserResponse>, (StatusCode, Json<ApiError>)> {
    let args = serde_json::json!({
        "selector": req.selector
    });

    let result = execute_playwright_command(&vm_id, "click", Some(args)).await?;
    Ok(Json(result))
}

/// POST /api/vms/:id/browser/type
/// Type text into element
pub async fn type_text(
    Path(vm_id): Path<String>,
    Json(req): Json<TypeRequest>,
) -> Result<Json<BrowserResponse>, (StatusCode, Json<ApiError>)> {
    let args = serde_json::json!({
        "selector": req.selector,
        "text": req.text
    });

    let result = execute_playwright_command(&vm_id, "type", Some(args)).await?;
    Ok(Json(result))
}

/// GET /api/vms/:id/browser/content
/// Get page HTML content
pub async fn get_content(
    Path(vm_id): Path<String>,
) -> Result<Json<BrowserResponse>, (StatusCode, Json<ApiError>)> {
    let result = execute_playwright_command(&vm_id, "content", None).await?;
    Ok(Json(result))
}

/// POST /api/vms/:id/browser/screenshot
/// Take screenshot of current page
pub async fn screenshot(
    Path(vm_id): Path<String>,
) -> Result<Json<BrowserResponse>, (StatusCode, Json<ApiError>)> {
    let result = execute_playwright_command(&vm_id, "screenshot", None).await?;
    Ok(Json(result))
}
