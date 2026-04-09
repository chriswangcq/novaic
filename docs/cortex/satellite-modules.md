# 卫星模块速查（非核心路径）

> 以下模块在 `novaic_cortex/` 中存在，**不**单独开长文；此处说明职责与何时再读源码。

## 1. `entangled_access.py`

- **`get_entangled_client()`**：单例 **`EntangledClient`**，读 **Entangled** 实体（如 agent 元数据）。
- 环境：**`ENTANGLED_SERVICE_URL`**，或回退 **`common.config.ServiceConfig`** / 默认 `http://127.0.0.1:19900`。
- 注释说明：**多数业务仍应走 `GatewayProxy`**；直连适用于纯数据读、或 Cortex 组装上下文时的特殊需求。

## 2. `file_resolver.py`

- 解析 **`fs://`** URI（**user 相对**，不含 `user_id`）；多种模式：**http_url** / **local** / **inline**（与 LLM 预算相关）。
- 设计见仓库内 **`docs/oss-storage-unified-plan.md`**（若存在）。

## 3. `trs.py`（Cortex Native TRS）

- Native **工具结果**格式化、解析、与 LLM 表示转换；**`resolve_for_llm`** 将 **`fs://`** 解析为 **`_mcp_content`** 块注入消息。

## 4. `tenant.py`

- **`TenantLayout`**：多租户 OSS 前缀 **`users/{user_id}/agents/{agent_id}/`** 等形式化封装（与 `WorkspaceRegistry` + `Workspace._key` 一致；见 [storage-and-keys.md](storage-and-keys.md)）。

## 5. `aliyun_oss_s3.py`

- **`boto3_client_aliyun_oss`**：启动时创建 **S3 兼容 OSS** 客户端（见 [deployment-and-startup.md](deployment-and-startup.md)）。

---

若某条调用链贯穿 Entangled / `fs://` / TRS，可从这里跳到对应 `.py` 再对照 **`docs/oss-storage-unified-plan.md`**。
