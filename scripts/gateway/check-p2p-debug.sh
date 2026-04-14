#!/usr/bin/env bash
# 调用 GET /api/p2p/debug 查看最近打洞请求（需 JWT）
# Usage: NOVAIC_JWT="eyJ..." ./scripts/check-p2p-debug.sh
#       或: ./scripts/check-p2p-debug.sh  # 从 novaic-app 的 gateway_url.txt + 需手动传 token
#
# JWT 获取方式：NovAIC 桌面 App 登录后，打开 DevTools → Network，
# 任选一个请求 api.gradievo.com 的请求，复制 Request Headers 里的 Authorization: Bearer xxx

GATEWAY_URL="${NOVAIC_GATEWAY_URL:-https://api.gradievo.com}"
JWT="${NOVAIC_JWT}"

if [[ -z "$JWT" ]]; then
  echo "Usage: NOVAIC_JWT='your-jwt-token' $0"
  echo "  JWT 可从 App 登录后 invoke('get_cloud_token') 获取"
  exit 1
fi

curl -s -H "Authorization: Bearer $JWT" "$GATEWAY_URL/api/p2p/debug" | python3 -m json.tool
