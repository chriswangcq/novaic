> **文档状态（2026-04）**：本文为过程稿、调研快照或子模块镜像，**非**仓库唯一现行架构来源。权威总览见仓库根 `docs/backend-architecture.md`；与代码/部署对齐的核查见 `docs/architecture-verification-2026-04.md`。

# 在 47.77.178.34 部署 VPN (Xray) 实施指南

## 一、你提供的 vmess 配置解析

你提供的 vmess URI 解码后为**客户端配置**（用于连接 api.deepek.com）：

```json
{
  "v": "2",
  "ps": "api.deepek.com",
  "add": "api.deepek.com",
  "port": "443",
  "id": "fcc5a374-eb6a-49da-aedc-7c3d8c2d3420",
  "aid": "0",
  "net": "ws",
  "type": "none",
  "host": "api.deepek.com",
  "path": "/api/ws",
  "tls": "tls"
}
```

协议：**VMess + WebSocket + TLS**（需要域名 + SSL 证书）

---

## 二、部署方案对比

| 方案 | 是否需要域名 | 安全性 | 推荐度 | 说明 |
|------|-------------|--------|--------|------|
| **VLESS-REALITY** | ❌ 否 | ⭐⭐⭐ | 最推荐 | 无域名、抗检测、速度快 |
| **VMess-TCP** | ❌ 否 | ⭐ | 简单 | IP 直连，**无 TLS 封装**（VMess 仍有协议层加密；勿理解为「明文」） |
| **VMess-WS-TLS** | ✅ 是 | ⭐⭐⭐ | 与参考配置一致 | 需域名 + Let's Encrypt |

---

## 三、推荐方案：233boy Xray 一键脚本

### 前置条件

- 服务器：47.77.178.34
- SSH  root 权限
- 系统：Ubuntu 22.04 / Debian 11+（推荐）

### 步骤 1：SSH 登录服务器

以下 `xray` / `ufw` 均在 **VPS 上**通过上游脚本安装，**非**本 monorepo 内文件。

```bash
ssh root@47.77.178.34
```

### 步骤 2：执行一键安装

```bash
bash <(wget -qO- -o- https://github.com/233boy/Xray/raw/main/install.sh)
```

安装完成后会**自动创建 VLESS-REALITY 配置**，可直接使用。

### 步骤 3：如需 VMess（与参考配置类似）

**无域名 - 添加 VMess-TCP：**
```bash
xray add tcp
```
按提示选择端口（如 443），脚本会生成 vmess 链接。

**有域名 - 添加 VMess-WS-TLS：**
```bash
xray add ws
```
需输入域名（如 vpn.yourdomain.com），并确保 DNS 已解析到 47.77.178.34。

### 步骤 4：查看配置

```bash
xray url
```
复制输出的 vmess/vless 链接到客户端使用。

### 步骤 5：开放防火墙端口

```bash
# 若使用 ufw
ufw allow 443/tcp
ufw allow 80/tcp   # 若用 Let's Encrypt
ufw reload

# 或临时关闭防火墙测试
ufw disable
```

---

## 四、常用管理命令

```bash
xray          # 打开管理面板
xray add      # 添加配置
xray url      # 查看所有配置链接
xray qr       # 生成二维码
xray uninstall  # 卸载
```

---

## 五、客户端配置

安装后使用 `xray url` 获取的链接，在以下客户端中导入：

- **Windows**: v2rayN、Clash
- **macOS**: V2rayU、ClashX
- **iOS**: Shadowrocket、Quantumult X
- **Android**: v2rayNG、Clash

---

## 六、快速执行清单（复制粘贴）

```bash
# 1. SSH 登录
ssh root@47.77.178.34

# 2. 一键安装 Xray
bash <(wget -qO- -o- https://github.com/233boy/Xray/raw/main/install.sh)

# 3. 如需 VMess-TCP（无域名）
xray add tcp

# 4. 查看配置链接
xray url

# 5. 开放端口（如使用 443）
ufw allow 443/tcp && ufw reload
```

---

## 七、注意事项

1. **时间同步**：Xray 要求服务器时间误差 < 90 秒，建议启用 NTP
2. **云厂商安全组**：阿里云/腾讯云等需在控制台开放 443、80 等端口
3. **域名**：VMess-WS-TLS 需要域名，无域名建议用 VLESS-REALITY 或 VMess-TCP

---

## 八、参考链接

- [233boy Xray 脚本 GitHub](https://github.com/233boy/Xray)
- [Xray 搭建详细图文教程](https://github.com/233boy/Xray/wiki/Xray%E6%90%AD%E5%BB%BA%E8%AF%A6%E7%BB%86%E5%9B%BE%E6%96%87%E6%95%99%E7%A8%8B)
