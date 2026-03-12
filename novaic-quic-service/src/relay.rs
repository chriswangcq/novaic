//! Relay — 连接配对与 stream 转发

use std::collections::HashMap;
use std::sync::Arc;
use std::time::{Duration, Instant};

use quinn::{Connection, RecvStream, SendStream};
use tokio::sync::RwLock;
use tracing::{info, warn};

use crate::auth;
use crate::config::Config;
use crate::protocol::{ConnectRequest, ConnectResponse, RegisterPc};

/// PC 注册条目：连接 + 注册时间（用于 TTL 清理）
struct PcEntry {
    conn: Connection,
    registered_at: Instant,
}

/// session_id -> PcEntry（等待手机配对，超时自动清理）
type PcRegistry = Arc<RwLock<HashMap<String, PcEntry>>>;

/// session 过期时间：PC 注册后若无手机连接则视为过期
const SESSION_TTL: Duration = Duration::from_secs(10);

/// 从 PEM 文件加载 TLS 证书（生产环境，如 Let's Encrypt）
fn load_server_crypto_from_files(
    cert_path: &str,
    key_path: &str,
) -> anyhow::Result<rustls::ServerConfig> {
    use rustls_pemfile::{certs, private_key};
    use std::io::BufReader;

    let cert_file = std::fs::File::open(cert_path)
        .map_err(|e| anyhow::anyhow!("Failed to open cert {}: {}", cert_path, e))?;
    let certs: Vec<_> = certs(&mut BufReader::new(cert_file))
        .collect::<Result<Vec<_>, _>>()
        .map_err(|e| anyhow::anyhow!("Failed to parse cert: {}", e))?
        .into_iter()
        .map(rustls::pki_types::CertificateDer::from)
        .collect();

    let key_file = std::fs::File::open(key_path)
        .map_err(|e| anyhow::anyhow!("Failed to open key {}: {}", key_path, e))?;
    let key = private_key(&mut BufReader::new(key_file))
        .map_err(|e| anyhow::anyhow!("Failed to parse key: {}", e))?
        .ok_or_else(|| anyhow::anyhow!("No private key found in {}", key_path))?;

    let config = rustls::ServerConfig::builder()
        .with_no_client_auth()
        .with_single_cert(certs, key.into())
        .map_err(|e| anyhow::anyhow!("ServerConfig build failed: {}", e))?;

    Ok(config)
}

/// 生成自签名 TLS 证书（relay 服务端用，仅开发）
fn make_server_crypto_self_signed() -> anyhow::Result<rustls::ServerConfig> {
    let cert = rcgen::generate_simple_self_signed(vec!["relay.local".into()])?;
    let cert_der = cert.cert.der().to_vec();
    let key_der = cert.key_pair.serialize_der();

    let certs = vec![rustls::pki_types::CertificateDer::from(cert_der)];
    let key = rustls::pki_types::PrivateKeyDer::try_from(key_der)
        .map_err(|e| anyhow::anyhow!("Invalid key: {}", e))?;

    let config = rustls::ServerConfig::builder()
        .with_no_client_auth()
        .with_single_cert(certs, key)?;

    Ok(config)
}

/// 启动 Relay QUIC 服务
pub async fn run_relay_server(config: &Config) -> anyhow::Result<()> {
    let crypto = if let (Some(ref cert), Some(ref key)) =
        (&config.relay_tls_cert_path, &config.relay_tls_key_path)
    {
        tracing::info!("[Relay] Loading TLS from {} / {}", cert, key);
        load_server_crypto_from_files(cert, key)?
    } else {
        tracing::warn!("[Relay] No RELAY_TLS_CERT_PATH/KEY_PATH, using self-signed (dev only)");
        make_server_crypto_self_signed()?
    };
    let server_config = quinn::ServerConfig::with_crypto(Arc::new(
        quinn::crypto::rustls::QuicServerConfig::try_from(crypto)?,
    ));

    let socket = std::net::UdpSocket::bind(config.relay_bind_addr())?;
    socket.set_nonblocking(true)?;

    let endpoint = quinn::Endpoint::new(
        quinn::EndpointConfig::default(),
        Some(server_config),
        socket,
        Arc::new(quinn::TokioRuntime),
    )?;

    info!("[Relay] Listening on {}", config.relay_bind_addr());

    let pc_registry: PcRegistry = Arc::new(RwLock::new(HashMap::new()));

    loop {
        let incoming = match endpoint.accept().await {
            Some(i) => i,
            None => break,
        };

        let conn = match incoming.await {
            Ok(c) => c,
            Err(e) => {
                warn!("[Relay] Connection failed: {}", e);
                continue;
            }
        };

        let gw = config.gateway_url.clone();
        let reg = Arc::clone(&pc_registry);
        tokio::spawn(async move {
            if let Err(e) = handle_connection(conn, &gw, reg).await {
                warn!("[Relay] Handler error: {}", e);
            }
        });
    }

    Ok(())
}

async fn handle_connection(
    conn: Connection,
    gateway_url: &str,
    pc_registry: PcRegistry,
) -> anyhow::Result<()> {
    // 客户端用 open_bi() 发起 stream，服务端需用 accept_bi() 接受，不能用 open_bi()
    let (mut send, mut recv) = conn.accept_bi().await?;

    // 读取首行 JSON（RegisterPc 或 ConnectRequest），15s 超时防挂起
    let mut line = String::new();
    let mut buf = [0u8; 1];
    loop {
        tokio::time::timeout(Duration::from_secs(15), recv.read_exact(&mut buf))
            .await
            .map_err(|_| anyhow::anyhow!("Handshake read timeout"))??;
        if buf[0] == b'\n' {
            break;
        }
        line.push(buf[0] as char);
        if line.len() > 8192 {
            anyhow::bail!("Handshake too long");
        }
    }

    let trimmed = line.trim();
    if trimmed.is_empty() {
        send_response(&mut send, &ConnectResponse::failure("Empty handshake")).await?;
        return Ok(());
    }

    // 尝试解析为 RegisterPc
    if let Ok(req) = serde_json::from_str::<RegisterPc>(trimmed) {
        if auth::validate_jwt_and_device(gateway_url, &req.jwt, &req.device_id)
            .await
            .is_err()
        {
            send_response(&mut send, &ConnectResponse::failure("Invalid JWT")).await?;
            return Ok(());
        }
        // 校验 session：双方必须持 relay-request 创建的 session_id 建联，无效则快速失败
        if auth::validate_relay_session(
            gateway_url,
            &req.jwt,
            &req.session_id,
            &req.device_id,
        )
        .await
        .is_err()
        {
            send_response(&mut send, &ConnectResponse::failure("invalid or expired session")).await?;
            return Ok(());
        }
        {
            let mut reg = pc_registry.write().await;
            reg.retain(|_, e| e.registered_at.elapsed() <= SESSION_TTL);
            reg.insert(
                req.session_id.clone(),
                PcEntry {
                    conn,
                    registered_at: Instant::now(),
                },
            );
        }
        send_response(&mut send, &ConnectResponse::success()).await?;
        info!("[Relay] PC registered session={}", &req.session_id[..8.min(req.session_id.len())]);
        return Ok(());
    }

    // 尝试解析为 ConnectRequest
    if let Ok(req) = serde_json::from_str::<ConnectRequest>(trimmed) {
        if auth::validate_jwt_and_device(gateway_url, &req.jwt, &req.target_device_id)
            .await
            .is_err()
        {
            send_response(&mut send, &ConnectResponse::failure("Invalid JWT")).await?;
            return Ok(());
        }

        // 校验 session：relay-request 创建且未过期，无效则快速失败，避免无谓等待
        if auth::validate_relay_session(
            gateway_url,
            &req.jwt,
            &req.session_id,
            &req.target_device_id,
        )
        .await
        .is_err()
        {
            send_response(&mut send, &ConnectResponse::failure("invalid or expired session")).await?;
            return Ok(());
        }

        // 长等待：PC 可能尚未 RegisterPc（推送有延迟），轮询等待最多 10s
        const WAIT_FOR_PC_TIMEOUT: Duration = Duration::from_secs(10);
        const POLL_INTERVAL: Duration = Duration::from_millis(300);

        let pc_conn = {
            let deadline = Instant::now() + WAIT_FOR_PC_TIMEOUT;
            loop {
                if let Some(entry) = pc_registry.write().await.remove(&req.session_id) {
                    if entry.registered_at.elapsed() <= SESSION_TTL {
                        break Some(entry.conn);
                    }
                    send_response(&mut send, &ConnectResponse::failure("Session expired (TTL exceeded)")).await?;
                    return Ok(());
                }
                if Instant::now() >= deadline {
                    send_response(&mut send, &ConnectResponse::failure("PC offline or session expired")).await?;
                    return Ok(());
                }
                tokio::time::sleep(POLL_INTERVAL).await;
            }
        }
        .expect("loop breaks with Some");

        send_response(&mut send, &ConnectResponse::success()).await?;
        info!("[Relay] Paired session={}", &req.session_id[..8.min(req.session_id.len())]);

        // 转发后续 streams：手机 ↔ PC
        forward_streams(conn, pc_conn).await?;
    } else {
        send_response(&mut send, &ConnectResponse::failure("Invalid handshake")).await?;
    }

    Ok(())
}

async fn send_response(send: &mut SendStream, resp: &ConnectResponse) -> anyhow::Result<()> {
    let json = serde_json::to_string(resp)?;
    send.write_all(json.as_bytes()).await?;
    send.write_all(b"\n").await?;
    send.finish()?;
    Ok(())
}

/// 双向转发：手机 conn 与 PC conn 之间的所有 bidi streams
async fn forward_streams(mobile: Connection, pc: Connection) -> anyhow::Result<()> {
    loop {
        tokio::select! {
            Ok((ms, mr)) = mobile.accept_bi() => {
                let (ps, pr) = pc.open_bi().await?;
                tokio::spawn(forward_bidi(ms, mr, ps, pr));
            }
            Ok((ps, pr)) = pc.accept_bi() => {
                let (ms, mr) = mobile.open_bi().await?;
                tokio::spawn(forward_bidi(ps, pr, ms, mr));
            }
            else => break,
        }
    }
    Ok(())
}

async fn forward_bidi(
    mut a_send: SendStream,
    mut a_recv: RecvStream,
    mut b_send: SendStream,
    mut b_recv: RecvStream,
) {
    let a_to_b = async {
        let mut buf = vec![0u8; 65536];
        loop {
            match a_recv.read(&mut buf).await {
                Ok(Some(n)) if n > 0 => b_send.write_all(&buf[..n]).await?,
                Ok(Some(0)) | Ok(None) => break,
                Ok(_) => {}
                Err(_) => break,
            }
        }
        let _ = b_send.finish();
        Ok::<(), anyhow::Error>(())
    };
    let b_to_a = async {
        let mut buf = vec![0u8; 65536];
        loop {
            match b_recv.read(&mut buf).await {
                Ok(Some(n)) if n > 0 => a_send.write_all(&buf[..n]).await?,
                Ok(Some(0)) | Ok(None) => break,
                Ok(_) => {}
                Err(_) => break,
            }
        }
        let _ = a_send.finish();
        Ok::<(), anyhow::Error>(())
    };
    tokio::select! {
        _ = a_to_b => {}
        _ = b_to_a => {}
    }
}
