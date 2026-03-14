# Relay 服务器迁移：8.146.233.64 → 47.243.221.45

## 前置条件

1. **新服务器 47.243.221.45 可 SSH**：`ssh -p 52222 root@47.243.221.45` 能登录（SSH 端口 52222）
2. **云安全组**：放行 52222(TCP)、80(TCP)、443(TCP/UDP)、3478(UDP)
3. **SSH 公钥**：`ssh-copy-id -p 52222 root@47.243.221.45` 已配置免密

## 迁移步骤

### 步骤 0：确认新服务器可访问

```bash
ssh -p 52222 root@47.243.221.45 "hostname && uptime"
```

若超时，检查：安全组 52222 端口、新服务器是否已启动、SSH 服务是否运行。

---

### 步骤 1：从旧 relay 复制证书到新 relay

```bash
# 在旧 relay 打包证书
ssh root@8.146.233.64 "tar czf - -C /etc letsencrypt" > /tmp/letsencrypt.tar.gz

# 传到新 relay（SSH 端口 52222）
scp -P 52222 /tmp/letsencrypt.tar.gz root@47.243.221.45:/tmp/

# 在新 relay 解压
ssh -p 52222 root@47.243.221.45 "mkdir -p /etc && tar xzf /tmp/letsencrypt.tar.gz -C /etc && rm /tmp/letsencrypt.tar.gz"
```

---

### 步骤 2：部署 novaic-quic-service

```bash
cd novaic-quic-service
# DEPLOY_OVERSEAS=1 使用官方 Rust 源（海外服务器不用国内镜像）
DEPLOY_OVERSEAS=1 SSH_OPTS="-p 52222 -o StrictHostKeyChecking=accept-new" ./deploy/deploy.sh root@47.243.221.45
```

---

### 步骤 3：部署 nginx + 前端

```bash
# 配置 nginx（relay-frontend）
ssh -p 52222 root@47.243.221.45 "bash -s" < novaic-quic-service/deploy/setup-cnd-frontend-nginx.sh

# 部署前端静态文件（从旧 relay 同步）
rsync -avz -e "ssh -p 52222" root@8.146.233.64:/opt/novaic/static/ root@47.243.221.45:/opt/novaic/static/
```

或重新构建并部署：

```bash
cd novaic-app
VITE_BASE="/resource/frontend/v0.3.0/" npm run build
rsync -avz -e "ssh -p 52222" dist/ root@47.243.221.45:/opt/novaic/static/v0.3.0/
```

---

### 步骤 4：更新 DNS

在域名服务商处将以下记录指向 **47.243.221.45**：

| 类型 | 主机记录 | 记录值 |
|------|----------|--------|
| A | relay | 47.243.221.45 |
| A | stun | 47.243.221.45 |

等待 DNS 生效（通常几分钟）。

---

### 步骤 5：验证

```bash
# STUN
nc -u -v stun.gradievo.com 3478

# Relay HTTPS
curl -sk https://relay.gradievo.com/resource/frontend/v0.3.0/ -o /dev/null -w '%{http_code}\n'

# 前端
curl -sk https://relay.gradievo.com/resource/frontend/v0.3.0/ | head -5
```

---

### 步骤 6：停用旧 relay（可选）

DNS 切换后，旧服务器 8.146.233.64 可关机或保留作备份。

---

## 一键迁移脚本（需先配置 SSH）

已保存为 `scripts/migrate-relay-to-47.sh`，在 SSH 可访问新服务器后执行：

```bash
./scripts/migrate-relay-to-47.sh
```

脚本使用 SSH 端口 **52222**。若需修改，编辑脚本中的 `-p 52222`。
