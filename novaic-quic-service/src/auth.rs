//! 鉴权 — 调用 Gateway 校验 JWT 与 device 归属

use tracing::{debug, warn};

/// 调用 Gateway validate-device 接口，校验 JWT 并验证 device_id 归属
pub async fn validate_jwt_and_device(
    gateway_url: &str,
    jwt: &str,
    device_id: &str,
) -> anyhow::Result<String> {
    let encoded = urlencoding::encode(device_id);
    // 使用 /api/p2p/validate-device：/internal/ 仅允许 127.0.0.1，relay 为外部服务无法访问
    let url = format!("{}/api/p2p/validate-device?device_id={}", gateway_url, encoded);
    let client = reqwest::Client::builder()
        .timeout(std::time::Duration::from_secs(10))
        .build()?;

    let resp = client
        .get(&url)
        .header("Authorization", format!("Bearer {}", jwt))
        .send()
        .await?;

    if !resp.status().is_success() {
        anyhow::bail!("JWT validation failed: status {}", resp.status());
    }

    let user_id = resp
        .headers()
        .get("X-User-ID")
        .or_else(|| resp.headers().get("x-user-id"))
        .and_then(|v| v.to_str().ok())
        .map(|s| s.to_string());

    match user_id {
        Some(id) if !id.is_empty() => {
            debug!("[Auth] JWT+device valid, user_id={} device_id={}", id, device_id);
            Ok(id)
        }
        _ => {
            warn!("[Auth] Gateway validate-device returned no X-User-ID");
            anyhow::bail!("JWT valid but no user_id in response")
        }
    }
}

/// 仅校验 JWT（无 device 时用，如部分场景）
pub async fn validate_jwt(gateway_url: &str, jwt: &str) -> anyhow::Result<String> {
    let url = format!("{}/internal/auth/validate", gateway_url);
    let client = reqwest::Client::builder()
        .timeout(std::time::Duration::from_secs(10))
        .build()?;

    let resp = client
        .get(&url)
        .header("Authorization", format!("Bearer {}", jwt))
        .send()
        .await?;

    if !resp.status().is_success() {
        anyhow::bail!("JWT validation failed: status {}", resp.status());
    }

    let user_id = resp
        .headers()
        .get("X-User-ID")
        .or_else(|| resp.headers().get("x-user-id"))
        .and_then(|v| v.to_str().ok())
        .map(|s| s.to_string());

    match user_id {
        Some(id) if !id.is_empty() => Ok(id),
        _ => anyhow::bail!("JWT valid but no user_id in response"),
    }
}
