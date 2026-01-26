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
    
    let cfg = crate::app_config::read_config(&app).await?;

    let api_key = cfg
        .llm_api_key
        .as_ref()
        .map(|s| s.trim().to_string())
        .filter(|s| !s.is_empty())
        .ok_or_else(|| "LLM API key not configured. Open Settings and set it first.".to_string())?;

    let api_base = cfg.llm_api_base.trim().to_string();
    let model = cfg.llm_model.trim().to_string();
    let max_tokens = cfg.llm_max_tokens;

    // Build JSON body - escape special characters
    let json_body = serde_json::json!({
        "api_key": api_key,
        "api_base": api_base,
        "model": model,
        "api_style": cfg.api_style,
        "enable_prefix_caching": cfg.enable_prefix_caching,
        "enable_thinking": cfg.enable_thinking,
        "max_tokens": max_tokens,
        "max_iterations": cfg.max_iterations,
        "visible_shell": cfg.visible_shell
    }).to_string();

    println!("[Agent] Initializing agent via curl to {}/api/init", AGENT_BASE_URL);

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
    message: String
) -> Result<(), String> {
    use tokio::process::Command;
    use tokio::io::{AsyncBufReadExt, BufReader};
    
    println!("[Agent] Starting streaming message via curl to {}/api/chat/stream", AGENT_BASE_URL);
    
    // Escape the message for JSON (handle backslash, quotes, newlines, tabs, etc.)
    let escaped_message = message
        .replace('\\', "\\\\")
        .replace('"', "\\\"")
        .replace('\n', "\\n")
        .replace('\r', "\\r")
        .replace('\t', "\\t");
    let json_body = format!(r#"{{"message":"{}"}}"#, escaped_message);
    
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

