use serde::{Deserialize, Serialize};
use tauri::Emitter;

// Use 127.0.0.1 instead of localhost to avoid IPv6 connection issues
const AGENT_BASE_URL: &str = "http://127.0.0.1:9000";

#[derive(Debug, Serialize, Deserialize)]
pub struct InitResponse {
    pub status: String,
    pub message: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct HealthResponse {
    pub status: String,
    pub agent_initialized: bool,
    pub version: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct ChatResponse {
    pub results: Vec<ChatResult>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct ChatResult {
    #[serde(rename = "type")]
    pub result_type: String,
    pub data: serde_json::Value,
}

/// Initialize the agent with user token
#[tauri::command]
pub async fn init_agent(token: String, cloud_api_base: Option<String>) -> Result<InitResponse, String> {
    // 使用本地服务客户端（不走代理）
    let client = crate::http_client::local_client()
        .timeout(std::time::Duration::from_secs(30))
        .pool_max_idle_per_host(0)
        .build()
        .map_err(|e| format!("Failed to create HTTP client: {}", e))?;
    
    let api_base = cloud_api_base.unwrap_or_else(|| "https://api.nb-cc.com".to_string());
    
    let response = client
        .post(format!("{}/api/init", AGENT_BASE_URL))
        .json(&serde_json::json!({
            "user_token": token,
            "cloud_api_base": api_base
        }))
        .send()
        .await
        .map_err(|e| format!("Failed to connect to agent: {}", e))?;
    
    if !response.status().is_success() {
        return Err(format!("Agent returned error: {}", response.status()));
    }
    
    response
        .json::<InitResponse>()
        .await
        .map_err(|e| format!("Failed to parse response: {}", e))
}

/// Initialize the agent using locally stored app config (keeps API key out of frontend JS)
/// Uses curl command as a workaround for reqwest connection issues in Tauri
#[tauri::command]
pub async fn init_agent_with_app_config(app: tauri::AppHandle) -> Result<InitResponse, String> {
    use tokio::process::Command;
    use crate::app_config::ProviderType;
    
    let cfg = crate::app_config::read_config(&app).await?;

    // Find the first API key with credentials configured
    // Prefer OpenAI/OpenAI-compatible for backward compatibility
    let api_key_entry = cfg.api_keys.iter()
        .find(|k| {
            matches!(k.provider, ProviderType::Openai | ProviderType::OpenaiCompatible) 
            && k.api_key.as_ref().map(|s| !s.trim().is_empty()).unwrap_or(false)
        })
        .or_else(|| cfg.api_keys.iter().find(|k| {
            k.api_key.as_ref().map(|s| !s.trim().is_empty()).unwrap_or(false)
        }))
        .ok_or_else(|| "No API key configured. Open Settings and add one first.".to_string())?;

    let api_key = api_key_entry.api_key.clone().unwrap();
    let provider = format!("{:?}", api_key_entry.provider).to_lowercase();
    
    // Determine API base
    let api_base = api_key_entry.api_base.clone()
        .or_else(|| api_key_entry.provider.default_base_url().map(String::from))
        .unwrap_or_else(|| "https://api.openai.com/v1".to_string());

    // Build init request based on provider type
    let mut init_data = serde_json::json!({
        "provider": provider,
        "model": cfg.default_model,
        "max_tokens": cfg.max_tokens,
        "max_iterations": cfg.max_iterations,
        "visible_shell": cfg.visible_shell
    });

    // Add provider-specific config
    match api_key_entry.provider {
        ProviderType::Openai | ProviderType::OpenaiCompatible => {
            init_data["openai"] = serde_json::json!({
                "enabled": true,
                "api_key": api_key,
                "api_base": api_base,
                "override_base_url": api_key_entry.api_base.is_some()
            });
        }
        ProviderType::Anthropic => {
            init_data["anthropic"] = serde_json::json!({
                "api_key": api_key,
                "api_base": api_key_entry.api_base
            });
        }
        ProviderType::Google => {
            init_data["google"] = serde_json::json!({
                "api_key": api_key,
                "api_base": api_key_entry.api_base
            });
        }
        ProviderType::Azure => {
            init_data["azure"] = serde_json::json!({
                "enabled": true,
                "api_key": api_key,
                "api_base": api_key_entry.api_base,
                "deployment_name": api_key_entry.deployment_name,
                "api_version": api_key_entry.api_version.as_deref().unwrap_or("2024-02-01")
            });
        }
    }

    let json_body = init_data.to_string();
    println!("[Agent] Initializing agent via curl to {}/api/init with provider: {}", AGENT_BASE_URL, provider);

    // Use curl command to make the request (works reliably)
    let output = Command::new("curl")
        .args([
            "-s",                           // Silent mode
            "-m", "30",                     // 30 second timeout
            "-X", "POST",
            &format!("{}/api/init", AGENT_BASE_URL),
            "-H", "Content-Type: application/json",
            "-d", &json_body,
        ])
        .output()
        .await
        .map_err(|e| format!("Failed to execute curl: {}", e))?;

    if !output.status.success() {
        let stderr = String::from_utf8_lossy(&output.stderr);
        println!("[Agent] curl error: {}", stderr);
        return Err(format!("curl failed: {}", stderr));
    }

    let body = String::from_utf8_lossy(&output.stdout);
    println!("[Agent] Init response: {}", body);

    serde_json::from_str::<InitResponse>(&body)
        .map_err(|e| format!("Failed to parse response: {} - body: {}", e, body))
}

/// Send a message to the agent
/// Uses curl command as a workaround for reqwest connection issues in Tauri
#[tauri::command]
pub async fn send_message(message: String) -> Result<ChatResponse, String> {
    use tokio::process::Command;
    
    println!("[Agent] Sending message via curl to {}/api/chat", AGENT_BASE_URL);
    
    // Escape the message for JSON (handle backslash, quotes, newlines, tabs, etc.)
    let escaped_message = message
        .replace('\\', "\\\\")
        .replace('"', "\\\"")
        .replace('\n', "\\n")
        .replace('\r', "\\r")
        .replace('\t', "\\t");
    let json_body = format!(r#"{{"message":"{}"}}"#, escaped_message);
    
    // Use curl command to make the request (works reliably)
    let output = Command::new("curl")
        .args([
            "-s",                           // Silent mode
            "-m", "300",                    // 5 minute timeout
            "-X", "POST",
            &format!("{}/api/chat", AGENT_BASE_URL),
            "-H", "Content-Type: application/json",
            "-d", &json_body,
        ])
        .output()
        .await
        .map_err(|e| format!("Failed to execute curl: {}", e))?;
    
    if !output.status.success() {
        let stderr = String::from_utf8_lossy(&output.stderr);
        println!("[Agent] curl error: {}", stderr);
        return Err(format!("curl failed: {}", stderr));
    }
    
    let body = String::from_utf8_lossy(&output.stdout);
    println!("[Agent] Response received: {} bytes", body.len());
    
    serde_json::from_str::<ChatResponse>(&body)
        .map_err(|e| format!("Failed to parse response: {} - body: {}", e, body))
}

/// Get agent health status
#[tauri::command]
pub async fn get_health() -> Result<HealthResponse, String> {
    // 使用本地服务客户端（不走代理）
    let client = crate::http_client::local_client()
        .timeout(std::time::Duration::from_secs(10))
        .pool_max_idle_per_host(0)
        .build()
        .map_err(|e| format!("Failed to create HTTP client: {}", e))?;
    
    let response = client
        .get(format!("{}/api/health", AGENT_BASE_URL))
        .send()
        .await
        .map_err(|e| format!("Failed to check health: {}", e))?;
    
    if !response.status().is_success() {
        return Err(format!("Agent returned error: {}", response.status()));
    }
    
    response
        .json::<HealthResponse>()
        .await
        .map_err(|e| format!("Failed to parse response: {}", e))
}

/// Send a message to the agent with streaming response via Tauri events
/// Uses curl with unbuffered output to handle SSE stream
#[tauri::command]
pub async fn send_message_stream(
    app: tauri::AppHandle,
    message: String,
    model: Option<String>,
    mode: Option<String>
) -> Result<(), String> {
    use tokio::process::Command;
    use tokio::io::{AsyncBufReadExt, BufReader};
    
    println!("[Agent] Starting streaming message via curl to {}/api/chat/stream", AGENT_BASE_URL);
    println!("[Agent] Model: {:?}, Mode: {:?}", model, mode);
    
    // Escape the message for JSON (handle backslash, quotes, newlines, tabs, etc.)
    let escaped_message = message
        .replace('\\', "\\\\")
        .replace('"', "\\\"")
        .replace('\n', "\\n")
        .replace('\r', "\\r")
        .replace('\t', "\\t");
    
    // Build JSON body with optional model and mode
    let model_field = model.as_ref().map(|m| format!(r#","model":"{}""#, m)).unwrap_or_default();
    let mode_field = mode.as_ref().map(|m| format!(r#","mode":"{}""#, m)).unwrap_or_default();
    let json_body = format!(r#"{{"message":"{}"{}{}}}"#, escaped_message, model_field, mode_field);
    
    // Use curl with unbuffered output (-N) to stream SSE events
    let mut child = Command::new("curl")
        .args([
            "-s",                           // Silent mode
            "-N",                           // No buffer (stream immediately)
            "-m", "300",                    // 5 minute timeout
            "-X", "POST",
            &format!("{}/api/chat/stream", AGENT_BASE_URL),
            "-H", "Content-Type: application/json",
            "-d", &json_body,
        ])
        .stdout(std::process::Stdio::piped())
        .stderr(std::process::Stdio::piped())
        .spawn()
        .map_err(|e| format!("Failed to execute curl: {}", e))?;
    
    let stdout = child.stdout.take()
        .ok_or_else(|| "Failed to get stdout".to_string())?;
    
    let mut reader = BufReader::new(stdout).lines();
    
    // Read SSE events line by line and emit to frontend
    while let Ok(Some(line)) = reader.next_line().await {
        if line.starts_with("data: ") {
            let json_str = &line[6..]; // Remove "data: " prefix
            println!("[Agent] SSE event: {}", json_str);
            
            // Parse and emit the event to frontend
            if let Ok(event) = serde_json::from_str::<serde_json::Value>(json_str) {
                app.emit("chat-event", event)
                    .map_err(|e| format!("Failed to emit event: {}", e))?;
            }
        }
    }
    
    // Wait for curl to finish
    let status = child.wait().await
        .map_err(|e| format!("Failed to wait for curl: {}", e))?;
    
    if !status.success() {
        println!("[Agent] curl exited with error: {:?}", status);
    }
    
    // Emit completion event
    app.emit("chat-complete", ())
        .map_err(|e| format!("Failed to emit complete: {}", e))?;
    
    println!("[Agent] Streaming complete");
    Ok(())
}

