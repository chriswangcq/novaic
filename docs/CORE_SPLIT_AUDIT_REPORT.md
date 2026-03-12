# Core 拆分审计报告

> 由 5 个测试团队 subagent 于迁移后执行，检查遗漏与逻辑省略。

---

## 一、审计结论汇总

| 模块 | 完整性 | 关键问题 | 已修复 |
|------|--------|----------|--------|
| core/config | ✅ | 硬编码超时可迁移到 AppConfig | 可选 |
| core/gateway_client | ✅ | `get` 缺少空 body 处理 | ✅ 已修复 |
| core/sse_stream | ✅ | 无 | - |
| core/error | ✅ | AppError 未使用（设计选择） | - |
| 交叉引用 | ✅ | 无错误引用 | - |

---

## 二、各团队详细发现

### Agent 1：config 常量完整性

- **常量**：HTTP_*、SSH_*、VM_*、SERVICE_* 等已全部迁移
- **引用**：http_client、vm/deploy、core/gateway_client 均正确使用 `core::config::AppConfig`
- **建议**：sse_stream（3600s、30s）、vm/setup（3600s、100ms）、main.rs 中硬编码超时可迁移到 AppConfig

### Agent 2：gateway_client 逻辑完整性

- **方法**：get、post、patch、put、delete、health_check 均已迁移
- **遗漏**：`get` 在空 body 时未返回 `Ok(Value::Object(Map::new()))`，与 post/patch/put/delete 不一致
- **修复**：已在 `get` 中补充空 body 处理

### Agent 3：sse_stream 逻辑完整性

- **函数**：spawn_sse_stream、abort_sse_streams 完整
- **事件**：sse-chat、sse-logs、sse-chat-error、sse-logs-error、sse-chat-open、sse-logs-open 均正确
- **解析**：data: 行、[DONE]、keepalive 过滤逻辑正确
- **引用**：main.rs 已更新为 `core::sse_stream::*`

### Agent 4：error 与引用完整性

- **变体**：VmError、AgentError、FileError、NetworkError、ConfigError 齐全
- **实现**：From\<io::Error\>、From\<reqwest::Error\>、Serialize 完整
- **说明**：AppError 当前未被使用，与 vmcontrol 的 error 正确分离

### Agent 5：交叉引用与依赖

- **mod 声明**：无残留 mod config/error/gateway_client/sse_stream
- **引用路径**：main、vm/deploy、http_client 均使用 `core::` 或 `crate::core::`
- **循环依赖**：未发现

---

## 三、已实施修复

1. **core/gateway_client.rs `get` 方法**：在 `serde_json::from_str` 前增加空 body 判断，与 post/patch/put/delete 行为一致。

---

## 四、可选后续改进

1. 将 sse_stream、vm/setup、main 中的硬编码超时迁移到 AppConfig
2. 对未使用的 AppConfig 常量加注释或标记 deprecated
3. 若计划统一错误类型，可逐步用 AppError 替换 `Result<T, String>`
