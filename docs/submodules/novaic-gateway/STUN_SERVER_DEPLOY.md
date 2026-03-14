# 自建 STUN 服务器部署

当 `stun.l.google.com` 被墙或 UDP 受限时，可部署自建 STUN 到 `api.gradievo.com`。

## 1. 服务器部署

### 方式 A：systemd 服务（推荐）

```bash
# 创建服务文件
sudo tee /etc/systemd/system/novaic-stun.service << 'EOF'
[Unit]
Description=NovAIC STUN Server (RFC 5389)
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/novaic/services/novaic-gateway
ExecStart=/usr/bin/python3 scripts/stun_server.py --host 0.0.0.0 --port 3478
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable novaic-stun
sudo systemctl start novaic-stun
sudo systemctl status novaic-stun
```

### 方式 B：nohup 后台

```bash
cd /opt/novaic/services/novaic-gateway
nohup python3 scripts/stun_server.py --host 0.0.0.0 --port 3478 >> /opt/novaic/data/logs/stun.log 2>&1 &
```

### 防火墙

```bash
# 放行 UDP 3478
sudo ufw allow 3478/udp
sudo ufw reload
# 或 iptables
sudo iptables -A INPUT -p udp --dport 3478 -j ACCEPT
```

## 2. 客户端配置

**默认已使用** api.gradievo.com:443，无需配置。覆盖为 Google 时：

```bash
export NOVAIC_STUN_SERVER=stun.l.google.com:19302
```

## 3. 验证

```bash
python3 novaic-app/scripts/test-stun.py 45678
# 应输出: OK: external address = x.x.x.x:45678
```

## 4. 端口说明

| 端口 | 用途 |
|------|------|
| 443 | STUN UDP（与 HTTPS 共存） |
| 19998 | P2P QUIC（客户端本地，与 STUN 绑定端口一致） |

客户端 STUN 会绑定 `local_port`（即 P2P_PORT 19998），确保 NAT 映射与 QUIC 一致。
