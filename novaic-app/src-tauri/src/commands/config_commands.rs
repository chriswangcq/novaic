use crate::app_config::{self, AppConfigPublic, AppConfigUpdate, AppConfigV1};
use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize, Deserialize)]
pub struct TestConnectionResult {
    pub ok: bool,
    pub message: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct FetchModelsResult {
    pub ok: bool,
    pub models: Vec<String>,
    pub message: String,
}

#[derive(Debug, Deserialize)]
struct ModelInfo {
    id: String,
}

#[derive(Debug, Deserialize)]
struct ModelsResponse {
    data: Vec<ModelInfo>,
}

#[tauri::command]
pub async fn get_app_config(app: tauri::AppHandle) -> Result<AppConfigPublic, String> {
    let cfg = app_config::read_config(&app).await?;
    Ok(AppConfigPublic::from(&cfg))
}

#[tauri::command]
pub async fn set_app_config(app: tauri::AppHandle, update: AppConfigUpdate) -> Result<AppConfigPublic, String> {
    // Basic validation
    if update.llm_api_base.trim().is_empty() {
        return Err("llm_api_base is required".to_string());
    }
    if update.llm_model.trim().is_empty() {
        return Err("llm_model is required".to_string());
    }

    let mut cfg: AppConfigV1 = app_config::read_config(&app).await?;

    cfg.llm_api_base = update.llm_api_base.trim().to_string();
    cfg.llm_model = update.llm_model.trim().to_string();
    cfg.llm_max_tokens = update.llm_max_tokens;

    if let Some(key) = update.llm_api_key {
        if key.trim().is_empty() {
            cfg.llm_api_key = None;
        } else {
            cfg.llm_api_key = Some(key.trim().to_string());
        }
    }

    // Update API style settings
    if let Some(style) = update.api_style {
        cfg.api_style = style;
    }
    if let Some(caching) = update.enable_prefix_caching {
        cfg.enable_prefix_caching = caching;
    }
    if let Some(thinking) = update.enable_thinking {
        cfg.enable_thinking = thinking;
    }
    if let Some(max_iter) = update.max_iterations {
        cfg.max_iterations = max_iter.max(1).min(100); // Clamp between 1-100
    }
    if let Some(visible) = update.visible_shell {
        cfg.visible_shell = visible;
    }

    app_config::write_config(&app, &cfg).await?;
    Ok(AppConfigPublic::from(&cfg))
}

#[tauri::command]
pub async fn test_llm_connection(app: tauri::AppHandle) -> Result<TestConnectionResult, String> {
    let cfg = app_config::read_config(&app).await?;

    let api_key = cfg
        .llm_api_key
        .as_ref()
        .map(|s| s.trim().to_string())
        .filter(|s| !s.is_empty())
        .ok_or_else(|| "LLM API key not configured. Please set it in Settings.".to_string())?;

    let api_base = cfg.llm_api_base.trim().trim_end_matches('/').to_string();
    let url = format!("{}/models", api_base);

    let client = reqwest::Client::new();
    let resp = client
        .get(&url)
        .header("Authorization", format!("Bearer {}", api_key))
        .send()
        .await
        .map_err(|e| format!("Connection failed: {}", e))?;

    if resp.status().is_success() {
        Ok(TestConnectionResult {
            ok: true,
            message: "Connection OK".to_string(),
        })
    } else {
        let status = resp.status();
        let body = resp.text().await.unwrap_or_default();
        Ok(TestConnectionResult {
            ok: false,
            message: format!("LLM API returned {}: {}", status, body),
        })
    }
}

/// Fetch available models from the LLM API using a temporary API base and key.
/// This allows fetching models before saving the configuration.
#[tauri::command]
pub async fn fetch_models(api_base: String, api_key: String) -> Result<FetchModelsResult, String> {
    if api_base.trim().is_empty() {
        return Ok(FetchModelsResult {
            ok: false,
            models: vec![],
            message: "API Base URL is required".to_string(),
        });
    }

    if api_key.trim().is_empty() {
        return Ok(FetchModelsResult {
            ok: false,
            models: vec![],
            message: "API Key is required".to_string(),
        });
    }

    let api_base = api_base.trim().trim_end_matches('/').to_string();
    let url = format!("{}/models", api_base);

    let client = reqwest::Client::new();
    let resp = client
        .get(&url)
        .header("Authorization", format!("Bearer {}", api_key.trim()))
        .send()
        .await
        .map_err(|e| format!("Connection failed: {}", e))?;

    if resp.status().is_success() {
        let body = resp.text().await.unwrap_or_default();
        match serde_json::from_str::<ModelsResponse>(&body) {
            Ok(models_resp) => {
                let models: Vec<String> = models_resp.data.into_iter().map(|m| m.id).collect();
                Ok(FetchModelsResult {
                    ok: true,
                    models,
                    message: "Models fetched successfully".to_string(),
                })
            }
            Err(e) => Ok(FetchModelsResult {
                ok: false,
                models: vec![],
                message: format!("Failed to parse models response: {}", e),
            }),
        }
    } else {
        let status = resp.status();
        let body = resp.text().await.unwrap_or_default();
        Ok(FetchModelsResult {
            ok: false,
            models: vec![],
            message: format!("LLM API returned {}: {}", status, body),
        })
    }
}
