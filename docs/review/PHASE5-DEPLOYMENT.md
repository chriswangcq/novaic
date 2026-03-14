# Phase 5 部署指南

> novaic-quic-service 部署到 ECS（stun.gradievo.com + relay.gradievo.com）

---

## 一、前置条件

1. **ECS 已就绪**：域名 stun.gradievo.com、relay.gradievo.com 已解析到 ECS 公网 IP
2. **免密 SSH**：`ssh root@relay.gradievo.com` 可免密登录
3. **TLS 证书**：relay.gradievo.com 需有效证书（Let's Encrypt 等）

---

## 二、快速部署

```bash
# 1. 申请证书（若尚未申请）
ssh root@relay.gradievo.com "bash -s relay.gradievo.com" < novaic-quic-service/deploy/setup-certbot.sh

# 2. 一键部署
./novaic-quic-service/deploy/deploy.sh root@relay.gradievo.com
```

---

## 三、端口与配置

| 服务 | 域名 | 端口 | 协议 |
|------|------|------|------|
| STUN | stun.gradievo.com | 3478 | UDP |
| Relay | relay.gradievo.com | 443 | QUIC (UDP) |

### 环境变量

| 变量 | 说明 | 默认 |
|------|------|------|
| GATEWAY_URL | Gateway 地址（鉴权） | https://api.gradievo.com |
| RELAY_PORT | Relay 监听端口 | 19999（生产建议 443）|
| STUN_PORT | STUN 监听端口 | 3478 |
| RELAY_TLS_CERT_PATH | TLS 证书 PEM 路径 | 无则自签名 |
| RELAY_TLS_KEY_PATH | TLS 私钥 PEM 路径 | 无则自签名 |

---

## 四、Gateway 配置（Phase 4 Relay 兜底）

确保 Gateway 部署时设置 `RELAY_URL`（relay-request 返回给手机）：

```bash
RELAY_URL=https://relay.gradievo.com/p2p/relay
```

未设置时使用默认值 `https://relay.gradievo.com/p2p/relay`。

---

## 五、验证

```bash
# STUN 测试（本地）
NOVAIC_STUN_SERVER=stun.gradievo.com:3478 cargo run -p novaic-app -- ...  # 或使用 p2p 测试脚本

# Relay 由客户端自动使用（relay-request 返回的 relay_url）
```

---

## 六、故障排查

| 现象 | 可能原因 |
|------|----------|
| Relay 连接失败 | 检查 RELAY_TLS_CERT_PATH/KEY_PATH、防火墙 443/udp |
| STUN 无响应 | 检查防火墙 3478/udp、云安全组 |
| 鉴权失败 | 检查 GATEWAY_URL、Gateway validate-device 接口 |
