# novaic-quic-service

STUN (RFC 5389) + QUIC Relay for NovAIC P2P.

## 部署（Phase 5）

```bash
# 一键部署到 ECS（免密 SSH）
./deploy/deploy.sh root@relay.gradievo.com
```

详见 `docs/PHASE5-DEPLOYMENT.md`。

## 环境变量

| 变量 | 默认 | 说明 |
|------|------|------|
| `GATEWAY_URL` | `https://api.gradievo.com` | Gateway 地址，relay 鉴权时调用 |
| `RELAY_PORT` | `19999` | Relay QUIC 监听端口（生产用 443）|
| `STUN_PORT` | `3478` | STUN 监听端口 |
| `RELAY_TLS_CERT_PATH` | - | 生产 TLS 证书 PEM 路径 |
| `RELAY_TLS_KEY_PATH` | - | 生产 TLS 私钥 PEM 路径 |

未设置 `RELAY_TLS_*` 时使用自签名证书（仅开发）。

## 运行

```bash
# 开发（自签名）
cargo run

# 生产（需证书）
RELAY_PORT=443 RELAY_TLS_CERT_PATH=/path/to/fullchain.pem RELAY_TLS_KEY_PATH=/path/to/privkey.pem cargo run
```

## 协议

- **STUN**: RFC 5389 Binding Request/Response，XOR-MAPPED-ADDRESS
- **Relay**: 首 stream JSON 握手（RegisterPc / ConnectRequest），后续 stream 双向转发
