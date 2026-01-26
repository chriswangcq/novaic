use serde::{Deserialize, Serialize};
use std::path::PathBuf;
use tauri::Manager;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AppConfigV1 {
    pub version: u32,
    pub llm_api_base: String,
    pub llm_api_key: Option<String>,
    pub llm_model: String,
    pub llm_max_tokens: Option<u32>,
    /// API style: "chat_completions" (OpenAI) or "responses" (Doubao)
    #[serde(default = "default_api_style")]
    pub api_style: String,
    /// Enable prefix caching (Doubao only)
    #[serde(default = "default_true")]
    pub enable_prefix_caching: bool,
    /// Enable thinking mode (Doubao only)
    #[serde(default)]
    pub enable_thinking: bool,
    /// Maximum iterations for agent loop (default: 20)
    #[serde(default = "default_max_iterations")]
    pub max_iterations: u32,
    /// Show shell execution in GUI terminal (default: false)
    #[serde(default)]
    pub visible_shell: bool,
}

fn default_max_iterations() -> u32 {
    20
}

fn default_api_style() -> String {
    "chat_completions".to_string()
}

fn default_true() -> bool {
    true
}

impl Default for AppConfigV1 {
    fn default() -> Self {
        Self {
            version: 1,
            llm_api_base: "https://api.nuwaapi.com".to_string(),
            llm_api_key: None,
            llm_model: "gpt-5".to_string(),
            llm_max_tokens: Some(4096),
            api_style: "chat_completions".to_string(),
            enable_prefix_caching: true,
            enable_thinking: false,
            max_iterations: 20,
            visible_shell: false,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AppConfigPublic {
    pub version: u32,
    pub llm_api_base: String,
    pub has_llm_api_key: bool,
    pub llm_model: String,
    pub llm_max_tokens: Option<u32>,
    pub api_style: String,
    pub enable_prefix_caching: bool,
    pub enable_thinking: bool,
    pub max_iterations: u32,
    pub visible_shell: bool,
}

impl From<&AppConfigV1> for AppConfigPublic {
    fn from(cfg: &AppConfigV1) -> Self {
        Self {
            version: cfg.version,
            llm_api_base: cfg.llm_api_base.clone(),
            has_llm_api_key: cfg.llm_api_key.as_ref().map(|s| !s.trim().is_empty()).unwrap_or(false),
            llm_model: cfg.llm_model.clone(),
            llm_max_tokens: cfg.llm_max_tokens,
            api_style: cfg.api_style.clone(),
            enable_prefix_caching: cfg.enable_prefix_caching,
            enable_thinking: cfg.enable_thinking,
            max_iterations: cfg.max_iterations,
            visible_shell: cfg.visible_shell,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AppConfigUpdate {
    pub llm_api_base: String,
    /// If provided and non-empty, will overwrite stored key.
    /// If provided as empty string, will clear stored key.
    /// If omitted (None), will keep existing key.
    pub llm_api_key: Option<String>,
    pub llm_model: String,
    pub llm_max_tokens: Option<u32>,
    pub api_style: Option<String>,
    pub enable_prefix_caching: Option<bool>,
    pub enable_thinking: Option<bool>,
    pub max_iterations: Option<u32>,
    pub visible_shell: Option<bool>,
}

pub fn config_file_path(app: &tauri::AppHandle) -> Result<PathBuf, String> {
    let base_dir = app
        .path()
        .app_data_dir()
        .map_err(|e| format!("Failed to get app_data_dir: {e}"))?;

    Ok(base_dir.join("appConfig.json"))
}

pub async fn read_config(app: &tauri::AppHandle) -> Result<AppConfigV1, String> {
    let path = config_file_path(app)?;

    match tokio::fs::read_to_string(&path).await {
        Ok(content) => serde_json::from_str::<AppConfigV1>(&content)
            .map_err(|e| format!("Failed to parse config JSON: {e}")),
        Err(e) if e.kind() == std::io::ErrorKind::NotFound => Ok(AppConfigV1::default()),
        Err(e) => Err(format!("Failed to read config file: {e}")),
    }
}

pub async fn write_config(app: &tauri::AppHandle, cfg: &AppConfigV1) -> Result<(), String> {
    let path = config_file_path(app)?;

    if let Some(parent) = path.parent() {
        tokio::fs::create_dir_all(parent)
            .await
            .map_err(|e| format!("Failed to create config directory: {e}"))?;
    }

    let json = serde_json::to_string_pretty(cfg).map_err(|e| format!("Failed to serialize config: {e}"))?;
    tokio::fs::write(&path, json)
        .await
        .map_err(|e| format!("Failed to write config file: {e}"))?;

    // Best-effort: restrict permissions on unix-like systems.
    #[cfg(unix)]
    {
        use std::os::unix::fs::PermissionsExt;
        let perms = std::fs::Permissions::from_mode(0o600);
        let _ = std::fs::set_permissions(&path, perms);
    }

    Ok(())
}


