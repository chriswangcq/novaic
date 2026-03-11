//! 配置 — 从环境变量读取

use std::net::SocketAddr;

/// 服务配置
#[derive(Clone, Debug)]
pub struct Config {
    /// Gateway URL（relay 鉴权时调用）
    pub gateway_url: String,
    /// Relay QUIC 监听端口（生产 443，开发可 19999）
    pub relay_port: u16,
    /// STUN UDP 监听端口（默认 3478，RFC 5389 标准）
    pub stun_port: u16,
    /// Relay TLS 证书路径（PEM）。未设置则用自签名（仅开发）
    pub relay_tls_cert_path: Option<String>,
    /// Relay TLS 私钥路径（PEM）。未设置则用自签名
    pub relay_tls_key_path: Option<String>,
}

impl Config {
    pub fn from_env() -> Self {
        let gateway_url = std::env::var("GATEWAY_URL")
            .unwrap_or_else(|_| "https://api.gradievo.com".to_string());
        let relay_port: u16 = std::env::var("RELAY_PORT")
            .or_else(|_| std::env::var("LISTEN_PORT"))
            .ok()
            .and_then(|s| s.parse().ok())
            .unwrap_or(19999);
        let stun_port: u16 = std::env::var("STUN_PORT")
            .ok()
            .and_then(|s| s.parse().ok())
            .unwrap_or(3478);
        let relay_tls_cert_path = std::env::var("RELAY_TLS_CERT_PATH").ok().filter(|s| !s.trim().is_empty());
        let relay_tls_key_path = std::env::var("RELAY_TLS_KEY_PATH").ok().filter(|s| !s.trim().is_empty());

        Self {
            gateway_url: gateway_url.trim_end_matches('/').to_string(),
            relay_port,
            stun_port,
            relay_tls_cert_path,
            relay_tls_key_path,
        }
    }

    pub fn stun_bind_addr(&self) -> SocketAddr {
        format!("0.0.0.0:{}", self.stun_port)
            .parse()
            .expect("valid stun bind addr")
    }

    pub fn relay_bind_addr(&self) -> SocketAddr {
        format!("0.0.0.0:{}", self.relay_port)
            .parse()
            .expect("valid relay bind addr")
    }
}
