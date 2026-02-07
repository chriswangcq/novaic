use axum::{
    extract::{Path, Json as AxumJson},
    http::StatusCode,
};
use crate::api::types::ApiError;
use crate::qemu::GuestAgentClient;
use base64::{engine::general_purpose, Engine as _};
use serde_json::Value as JsonValue;

/// Generic VMUSE proxy - forwards all requests to VM's HTTP server
/// This supports all VMUSE tools: Browser, Desktop, Shell, Files, Windows, Context
pub async fn vmuse_proxy(
    Path((vm_id, tool, operation)): Path<(String, String, String)>,
    AxumJson(payload): AxumJson<JsonValue>,
) -> Result<AxumJson<JsonValue>, (StatusCode, AxumJson<ApiError>)> {
    let socket_path = format!("/tmp/novaic/novaic-ga-{}.sock", vm_id);
    let mut client = GuestAgentClient::connect(&socket_path).await.map_err(|e| {
        (
            StatusCode::SERVICE_UNAVAILABLE,
            AxumJson(ApiError {
                error: format!("Guest Agent not available: {}", e),
            }),
        )
    })?;

    // Build VM server API URL based on tool and operation
    // Examples:
    // - /api/browser/navigate
    // - /api/desktop/mouse
    // - /api/shell/command
    // - /api/file/read
    let vm_api_path = format!("/api/{}/{}", tool, operation);
    let url = format!("http://localhost:8080{}", vm_api_path);
    
    // Prepare JSON payload - escape single quotes for shell
    let json_data = payload.to_string().replace("'", "'\\''");
    
    let curl_cmd = format!(
        "curl -s -X POST '{}' -H 'Content-Type: application/json' -d '{}'",
        url, json_data
    );

    // Execute curl via Guest Agent
    let status = client
        .exec_sync("/bin/sh", vec!["-c".to_string(), curl_cmd])
        .await
        .map_err(|e| {
            (
                StatusCode::INTERNAL_SERVER_ERROR,
                AxumJson(ApiError {
                    error: format!("Failed to execute curl command: {}", e),
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
                AxumJson(ApiError {
                    error: format!("VMUSE command failed (exit {}): {}", exit_code, stderr),
                }),
            ));
        }
    }

    // Parse stdout (JSON response from VM server)
    if let Some(stdout) = status.stdout {
        let output_bytes = general_purpose::STANDARD
            .decode(&stdout)
            .map_err(|e| {
                (
                    StatusCode::INTERNAL_SERVER_ERROR,
                    AxumJson(ApiError {
                        error: format!("Failed to decode output: {}", e),
                    }),
                )
            })?;

        let output = String::from_utf8(output_bytes).map_err(|e| {
            (
                StatusCode::INTERNAL_SERVER_ERROR,
                AxumJson(ApiError {
                    error: format!("Failed to parse output as UTF-8: {}", e),
                }),
            )
        })?;

        let vm_response: JsonValue = serde_json::from_str(&output).map_err(|e| {
            (
                StatusCode::INTERNAL_SERVER_ERROR,
                AxumJson(ApiError {
                    error: format!("Failed to parse VM server response: {} (output: {})", e, output),
                }),
            )
        })?;
        
        // Check status field in response
        let status_str = vm_response.get("status")
            .and_then(|v| v.as_str())
            .unwrap_or("unknown");
        
        if status_str == "success" {
            Ok(AxumJson(vm_response))
        } else {
            let error_msg = vm_response.get("error")
                .and_then(|v| v.as_str())
                .unwrap_or("Unknown error")
                .to_string();
            
            Err((
                StatusCode::INTERNAL_SERVER_ERROR,
                AxumJson(ApiError {
                    error: error_msg,
                }),
            ))
        }
    } else {
        Err((
            StatusCode::INTERNAL_SERVER_ERROR,
            AxumJson(ApiError {
                error: "No output from VM server".to_string(),
            }),
        ))
    }
}
