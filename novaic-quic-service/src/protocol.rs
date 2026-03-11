//! Relay 协议 — RegisterPc / ConnectRequest / ConnectResponse

use serde::{Deserialize, Serialize};

/// PC 侧：连接 relay 时发送
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub struct RegisterPc {
    pub device_id: String,
    pub jwt: String,
    pub session_id: String,
}

/// 手机侧：连接 relay 时发送
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub struct ConnectRequest {
    pub target_device_id: String,
    pub jwt: String,
    pub session_id: String,
}

/// Relay 响应
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub struct ConnectResponse {
    pub ok: bool,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub error: Option<String>,
}

impl ConnectResponse {
    pub fn success() -> Self {
        Self { ok: true, error: None }
    }

    pub fn failure(msg: impl Into<String>) -> Self {
        Self {
            ok: false,
            error: Some(msg.into()),
        }
    }
}
