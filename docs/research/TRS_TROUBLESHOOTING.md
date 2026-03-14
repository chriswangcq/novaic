# TRS 执行结果不显示 - 排查指南

## 现象

Execution Log 中工具（如 notebook_list）执行成功，但「执行结果」区域为空。

## 可能原因

### 1. result_id 未写入（Tools Server 推送 TRS 失败）

**链路**：Tools Server 执行工具 → `push_tool_result_to_trs()` → TRS `/api/create` → 返回 result_id

**排查**：
```bash
# 服务器上检查 Tools Server 日志
ssh root@api.gradievo.com 'grep -E "TRS|result_id|Push failed" /opt/novaic/data/logs/tools-$(date +%Y%m%d).log | tail -20'

# 确认 TOOL_RESULT_SERVICE_URL 已配置
# Tools Server 启动需带: --tool-result-service-url http://127.0.0.1:19994
```

**常见原因**：
- `TOOL_RESULT_SERVICE_URL` 未配置或错误
- TRS (19994) 未运行
- TRS `/api/create` 返回非 200

### 2. result_id 已写入但 getTrsFull 失败（前端拉取 TRS 失败）

**链路**：前端 `getTrsFull(resultId)` → `gateway_get(/api/trs/{id}/full)` → Gateway proxy_trs → TRS `/api/{id}/full`

**排查**：
- 打开浏览器开发者工具 (F12) → Network，筛选 `trs` 或 `full`
- 查看请求状态码：401/403/404/503 等
- 修复后，前端会显示「加载失败: <错误信息>」（已加错误展示）

**常见原因**：
- 401：JWT 过期或未携带
- 403：Agent 归属校验失败（agent.user_id ≠ 当前用户）
- 404：TRS 中无该 result_id（可能已过期清理）
- 502：TRS 返回 5xx、归属校验异常或代理转发失败（前端会解析并显示 detail）
- 503：Gateway 无法连接 TRS

### 3. TRS 返回空内容

**排查**：`normalized` 中 text、files_created、display_files 均为空

**可能**：工具返回格式未被 `_parse_tool_result` 正确解析，导致推送时内容为空。

## 快速验证命令（服务器）

```bash
# 1. TRS 健康
curl -s http://127.0.0.1:19994/api/health

# 2. 手动创建一条 result 测试
RESULT=$(curl -s -X POST http://127.0.0.1:19994/api/create \
  -H "Content-Type: application/json" \
  -d '{"agent_id":"test-agent","tool_name":"test","text":"hello"}' | jq -r '.result_id')
echo "result_id=$RESULT"

# 3. 拉取 full（需替换为真实 result_id）
curl -s "http://127.0.0.1:19994/api/${RESULT}/full"
```

## 前端改动（便于排查）

`ExecutionLog.tsx` 中 `InlineTrsResult` 已增加错误展示：当 `getTrsFull` 失败时显示「加载失败: <错误信息>」，便于定位是网络/权限还是 TRS 问题。
