#!/usr/bin/env bash
# Phase 5：部署 novaic-quic-service 到 ECS
# 用法: ./deploy/deploy.sh [SERVER]
# 示例: ./deploy/deploy.sh root@relay.gradievo.com
# 免密：确保 ssh-copy-id 已配置

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
SERVER="${1:-root@relay.gradievo.com}"
SSH_OPTS="${SSH_OPTS:--o StrictHostKeyChecking=accept-new}"

echo "=== 1. 创建远程目录并推送源码 ==="
ssh $SSH_OPTS "$SERVER" 'mkdir -p /opt/novaic/novaic-quic-service'
RSYNC_EXCLUDES="--exclude target --exclude .git"
# 海外服务器不使用国内镜像，排除 .cargo/config.toml
[ -n "$DEPLOY_OVERSEAS" ] && RSYNC_EXCLUDES="$RSYNC_EXCLUDES --exclude .cargo"
rsync -avz -e "ssh $SSH_OPTS" $RSYNC_EXCLUDES \
  "$PROJECT_DIR/" "$SERVER:/opt/novaic/novaic-quic-service/"

echo ""
echo "=== 2. 远程编译 ==="
ssh $SSH_OPTS "$SERVER" "DEPLOY_OVERSEAS=$DEPLOY_OVERSEAS bash -s" << 'REMOTE_BUILD'
set -e
cd /opt/novaic/novaic-quic-service
if ! command -v cargo >/dev/null 2>&1; then
  if [ -n "$DEPLOY_OVERSEAS" ]; then
    echo "安装 Rust（官方源，海外服务器）..."
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
  else
    echo "安装 Rust（使用国内镜像）..."
    export RUSTUP_DIST_SERVER=https://rsproxy.cn
    export RUSTUP_UPDATE_ROOT=https://rsproxy.cn/rustup
    curl --proto '=https' --tlsv1.2 -sSf https://rsproxy.cn/rustup-init.sh | sh -s -- -y
  fi
  . "$HOME/.cargo/env"
fi
cargo build --release
systemctl stop novaic-quic-service 2>/dev/null || true
cp target/release/novaic-quic-service ./novaic-quic-service
REMOTE_BUILD

echo ""
echo "=== 3. 安装 systemd 服务 ==="
scp $SSH_OPTS "$SCRIPT_DIR/novaic-quic-service.service" "$SERVER:/tmp/"
ssh $SSH_OPTS "$SERVER" 'bash -s' << 'REMOTE'
set -e
# 若域名不同，需先修改 /tmp/novaic-quic-service.service 中的 RELAY_TLS_* 路径
cp /tmp/novaic-quic-service.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable novaic-quic-service
systemctl restart novaic-quic-service
systemctl status novaic-quic-service --no-pager
REMOTE

echo ""
echo "=== 4. 配置证书自动续期（若 certbot 证书已存在）==="
ssh $SSH_OPTS "$SERVER" 'bash -s' << 'REMOTE'
if [ -d /etc/letsencrypt/live ]; then
  mkdir -p /etc/letsencrypt/renewal-hooks/deploy
  cat > /etc/letsencrypt/renewal-hooks/deploy/restart-novaic-quic.sh << 'HOOK'
#!/bin/sh
systemctl restart novaic-quic-service 2>/dev/null || true
HOOK
  chmod +x /etc/letsencrypt/renewal-hooks/deploy/restart-novaic-quic.sh
  if systemctl list-unit-files certbot.timer &>/dev/null; then
    systemctl enable certbot.timer 2>/dev/null || true
    systemctl start certbot.timer 2>/dev/null || true
    echo "certbot.timer 已启用"
  elif ! crontab -l 2>/dev/null | grep -q certbot; then
    (crontab -l 2>/dev/null; echo "0 3 * * * certbot renew --quiet") | crontab -
    echo "已加入 crontab 每日 3:00 续期"
  fi
else
  echo "未检测到证书，跳过。首次请运行: ./deploy/setup-certbot.sh"
fi
REMOTE

echo ""
echo "=== 5. 放行防火墙 ==="
ssh $SSH_OPTS "$SERVER" 'bash -s' << 'REMOTE'
if command -v ufw >/dev/null 2>&1; then
  ufw allow 3478/udp 2>/dev/null || true
  ufw allow 443/udp 2>/dev/null || true
  ufw status | grep -E "3478|443" || echo "ufw: check manually"
elif command -v firewall-cmd >/dev/null 2>&1; then
  firewall-cmd --add-port=3478/udp --permanent 2>/dev/null || true
  firewall-cmd --add-port=443/udp --permanent 2>/dev/null || true
  firewall-cmd --reload 2>/dev/null || true
else
  echo "No ufw/firewalld, ensure UDP 3478 and 443 are open (cloud security group)"
fi
REMOTE

echo ""
echo "=== 6. 完成 ==="
echo "STUN: stun.gradievo.com:3478 (UDP)"
echo "Relay: https://relay.gradievo.com/p2p/relay (QUIC 443)"
echo ""
echo "前置条件："
echo "  1. relay.gradievo.com / stun.gradievo.com DNS 已指向 ECS"
echo "  2. certbot 已为 relay.gradievo.com 签发证书"
echo "  3. Gateway RELAY_URL=https://relay.gradievo.com/p2p/relay"
