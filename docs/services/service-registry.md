# Service Registry

Service Registry 是 NovAIC 的中心化服务注册与发现服务，当前在 API host Docker Compose 中运行。prod 默认监听 `127.0.0.1:19991`，staging 默认监听 `127.0.0.1:29991`。

它是 registry-only 运行时发现源。`services.json` 仍负责服务身份、预期端口、健康检查路径和 Compose 名称这些 manifest/bootstrap 元数据，但调用方运行时不再从 `services.json` fallback 出服务 URL。

环境隔离由 namespace 完成，服务名保持稳定：prod 和 staging 都注册为 `gateway`、`business`、`queue_service` 等同一组服务名，查询时必须带 namespace。

## Runtime State

生产环境使用 Postgres，DSN 文件为：

```text
/opt/novaic/postgres/secrets/novaic_registry_dsn
```

默认表名：

```text
service_registry_instances
```

实例状态包含：

- `namespace`
- `service_name`
- `instance_id`
- `url`
- `health_path`
- `status`
- `ttl_seconds`
- `registered_at`
- `last_seen_at`
- `metadata`

Postgres 主键是 `(namespace, service_name, instance_id)`，发现索引包含 `(namespace, service_name, status, last_seen_at DESC)`。`metadata.environment` 只用于观测，不能用于隔离。

## HTTP API

| 路径 | 方法 | 说明 |
|------|------|------|
| `/health` | GET | 健康检查 |
| `/ready` | GET | 就绪检查 |
| `/v1/registry/namespaces/{namespace}/instances` | POST | 注册或更新服务实例 |
| `/v1/registry/namespaces/{namespace}/instances/{service_name}/{instance_id}/heartbeat` | POST | 心跳与状态更新 |
| `/v1/registry/namespaces/{namespace}/instances/{service_name}/{instance_id}` | DELETE | deregister 实例 |
| `/v1/registry/namespaces/{namespace}/services/{service_name}/instances` | GET | 列出同 namespace 实例 |
| `/v1/registry/namespaces/{namespace}/services/{service_name}/discover` | GET | 返回同 namespace fresh healthy 实例 |
| `/v1/registry/namespaces/{namespace}/services/{service_name}/prune-stale` | POST | 清理同 namespace 过期实例 |

## Discovery Contract

运行时发现合同：

1. `common.service_runtime` 启动子进程并等待本地健康检查通过。
2. 服务定时 heartbeat 更新 `last_seen_at` 和状态。
3. 服务退出、收到停止信号或进入 draining 时调用 deregister。
4. 调用方启动前通过 `common.service_runtime --namespace <namespace> --require-service service=--flag` 查询同 namespace fresh healthy 实例，并把解析出的 URL 注入子进程参数。
5. Registry 不可用、无实例或实例过期时，调用方显式失败；不做 runtime fallback。

Nginx 只做 ingress，不参与服务发现。域名路由到 Gateway 端口，内部服务调用仍通过 namespace registry：

```nginx
server_name api.gradievo.com;
proxy_pass http://127.0.0.1:19999;

server_name staging-api.gradievo.com;
proxy_pass http://127.0.0.1:29999;
```
