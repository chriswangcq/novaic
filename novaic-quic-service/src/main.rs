//! novaic-quic-service — STUN (RFC 5389) + QUIC Relay

use std::sync::Arc;

use novaic_quic_service::{run_relay_server, run_stun_server, Config};
use tokio::net::UdpSocket;
use tracing::{info, warn};

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    rustls::crypto::ring::default_provider()
        .install_default()
        .expect("Failed to install rustls crypto provider");

    tracing_subscriber::fmt()
        .with_env_filter(tracing_subscriber::EnvFilter::from_default_env())
        .init();

    let config = Arc::new(Config::from_env());

    // STUN: 独立 UDP 端口 3478
    let stun_socket = UdpSocket::bind(config.stun_bind_addr()).await?;
    tokio::spawn(async move {
        if let Err(e) = run_stun_server(stun_socket).await {
            warn!("[STUN] Server error: {}", e);
        }
    });

    info!("[Main] STUN started on {}", config.stun_bind_addr());

    // Relay: QUIC 端口
    run_relay_server(&config).await?;

    Ok(())
}
