//! RFC 5389 STUN 服务
//!
//! 解析 Binding Request，返回 XOR-MAPPED-ADDRESS。
//! 参考 novaic-gateway/scripts/stun_server.py。

use std::net::SocketAddr;

use tokio::net::UdpSocket;
use tracing::{debug, info};

/// STUN Binding Request type
const STUN_BINDING_REQUEST: u16 = 0x0001;
/// STUN Binding Response type
const STUN_BINDING_RESPONSE: u16 = 0x0101;
/// RFC 5389 Magic Cookie
const MAGIC_COOKIE: [u8; 4] = [0x21, 0x12, 0xA4, 0x42];
/// XOR-MAPPED-ADDRESS attribute type
const XOR_MAPPED_ADDRESS: u16 = 0x0020;

/// 构建 Binding Response（含 XOR-MAPPED-ADDRESS）
fn build_binding_response(transaction_id: &[u8; 12], mapped_addr: SocketAddr) -> Vec<u8> {
    let (ip, port) = match mapped_addr {
        SocketAddr::V4(v4) => (v4.ip().octets(), v4.port()),
        SocketAddr::V6(_) => {
            // 简化：仅支持 IPv4
            return vec![];
        }
    };

    // XOR with magic cookie
    let port_xor = port ^ 0x2112;
    let ip_xor: [u8; 4] = [
        ip[0] ^ MAGIC_COOKIE[0],
        ip[1] ^ MAGIC_COOKIE[1],
        ip[2] ^ MAGIC_COOKIE[2],
        ip[3] ^ MAGIC_COOKIE[3],
    ];

    // XOR-MAPPED-ADDRESS: family(2) + port(2) + ip(4) = 8 bytes
    let mut attr_value = Vec::with_capacity(8);
    attr_value.extend_from_slice(&1u16.to_be_bytes()); // family = IPv4
    attr_value.extend_from_slice(&port_xor.to_be_bytes());
    attr_value.extend_from_slice(&ip_xor);

    let attr_len = attr_value.len();
    let padding = (4 - attr_len % 4) % 4;
    attr_value.extend(std::iter::repeat(0u8).take(padding));

    // Attribute: type(2) + length(2) + value
    let mut attr = Vec::with_capacity(4 + attr_len + padding);
    attr.extend_from_slice(&XOR_MAPPED_ADDRESS.to_be_bytes());
    attr.extend_from_slice(&(attr_len as u16).to_be_bytes());
    attr.extend_from_slice(&attr_value);

    // STUN header: type(2) + length(2) + magic(4) + transaction_id(12)
    let msg_len = attr.len() as u16;
    let mut header = Vec::with_capacity(20);
    header.extend_from_slice(&STUN_BINDING_RESPONSE.to_be_bytes());
    header.extend_from_slice(&msg_len.to_be_bytes());
    header.extend_from_slice(&MAGIC_COOKIE);
    header.extend_from_slice(transaction_id);

    header.extend(attr);
    header
}

/// 运行 STUN 服务，持续处理 UDP 包
pub async fn run_stun_server(socket: UdpSocket) -> anyhow::Result<()> {
    let mut buf = [0u8; 512];
    info!("[STUN] Server listening on {}", socket.local_addr()?);

    loop {
        let (n, peer) = socket.recv_from(&mut buf).await?;
        if n < 20 {
            continue;
        }

        let msg_type = u16::from_be_bytes([buf[0], buf[1]]);
        if msg_type != STUN_BINDING_REQUEST {
            debug!("[STUN] Ignoring non-Binding-Request type=0x{:04x}", msg_type);
            continue;
        }

        let mut trans_id = [0u8; 12];
        trans_id.copy_from_slice(&buf[8..20]);

        let response = build_binding_response(&trans_id, peer);
        if response.is_empty() {
            continue;
        }

        if let Err(e) = socket.send_to(&response, peer).await {
            tracing::warn!("[STUN] Send to {} failed: {}", peer, e);
        } else {
            debug!("[STUN] Response sent to {} (mapped={})", peer, peer);
        }
    }
}
