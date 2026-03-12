# 统一代码 Review 报告（5 名 Subagent 批判性审查）

> 审查心态：找 bug 有奖励，批判性视角

---

## 一、Subagent 发现汇总

### Agent 1（Rust setup/auth/storage）

| 问题 | 严重度 | 描述 |
|------|--------|------|
| 固定密钥派生 | CRITICAL | storage_key() 用固定 seed，同密钥可解密任何 secure_store.dat |
| set() JSON 解析静默丢数据 | CRITICAL | unwrap_or_default() 导致损坏时整库被替换 |
| data_dir 回退 "." | HIGH | mobile 上 app_data_dir 失败时用 "." 可能不可写 |
| VncProxy port 竞态 | MEDIUM | port 异步设置，3 秒内可为 0 |
| parent() 为 None | MEDIUM | store_path 父目录可能为空 |

### Agent 2（Rust commands/gateway/vnc）

| 问题 | 严重度 | 描述 |
|------|--------|------|
| std::sync::Mutex 在 async 中 | HIGH | GatewayUrlState 用 std::Mutex，在 async 命令中阻塞 |
| 持 tokio::Mutex 跨 await | MEDIUM | main.rs 中 vnc_proxy_state.lock().await 内再 .write().await |

### Agent 3（Frontend auth/secureStorage/App）

| 问题 | 严重度 | 描述 |
|------|--------|------|
| Gateway URL 每次启动覆盖 | HIGH | restoreSession 强制同步为 VITE_GATEWAY_URL，覆盖用户配置 |
| fallbackInterval 泄漏 | MEDIUM | unmount 后 pushToken 的 .then 仍可能设 interval 且不清理 |
| 缺少 cancelled 检查 | MEDIUM | getCurrentUser 后未检查 cancelled 就 setState |
| detectTauri 竞态 | LOW | 多调用者可能重复 probe |
| token 过期未检查 | LOW | needsRefresh 为 false 时直接返回，不校验 expiry |

### Agent 4（跨平台/async）

| 问题 | 严重度 | 描述 |
|------|--------|------|
| StorageBackend 同步阻塞 | HIGH | get/set/delete 为 sync I/O，在 async 命令中阻塞 runtime |
| blocking_lock 在 setup | MEDIUM | 当前 setup 同步，风险低；若改为 async 则有问题 |
| detectTauri 早于 StorageBackend | LOW | 前端可能在 setup 完成前 invoke |
| restoreSession 与 setup 竞态 | LOW | 同上 |

### Agent 5（安全）

| 问题 | 严重度 | 描述 |
|------|--------|------|
| 固定加密密钥 | CRITICAL | 与 Agent 1 相同 |
| secure_store.dat 权限 | HIGH | fs::write 默认权限，其他用户可读 |
| 登出/刷新竞态 | HIGH | 登出时 _doRefresh 完成会 saveSession，恢复会话 |
| localStorage 迁移可被投毒 | MEDIUM | XSS 可写入 localStorage，迁移时带入 SecureStorage |
| 空字符串重置 Gateway | MEDIUM | set_gateway_url("") 重置为云端，可能误触 |
| gateway_url.txt 权限 | LOW | 同上 |
| 错误体含 token | LOW | gateway_client 错误信息可能包含敏感内容 |

---

## 二、客观评估（逐项）

### 2.1 确认为真实 Bug（建议修复）

| 问题 | 评估 | 建议 |
|------|------|------|
| **Gateway URL 每次启动覆盖** | 真实。App.tsx 每次启动都把 gateway_url 强制设为 VITE_GATEWAY_URL，会覆盖用户手动配置（如本地开发）。 | 仅首次启动或 gateway_url.txt 不存在时同步；或增加「仅当与预期不同且用户未显式配置」的逻辑。 |
| **登出/刷新竞态** | 真实。logout 清空后，若 _doRefresh 尚未完成，其 saveSession 会恢复 token。 | 增加 `_logoutRequested` 标志，_doRefresh 完成前检查；或 logout 时取消/忽略进行中的 refresh。 |
| **fallbackInterval 泄漏** | 真实。unmount 时 cleanup 已执行，fallbackInterval 仍为 null；pushToken 的 .then 之后才赋值，该 interval 不会被 clear。 | 在 .then 回调中检查组件是否仍 mounted，或把 interval 存到 ref 并在 cleanup 中统一清理。 |
| **set() JSON 解析静默丢数据** | 真实。decrypted 解析失败时 unwrap_or_default() 会丢弃原有数据。 | 改为 `map_err(...)?` 或对解析失败做显式处理（如备份+报错），避免静默覆盖。 |
| **std::sync::Mutex 在 async** | 真实。GatewayUrlState 用 std::Mutex，在 async 命令中会阻塞 worker。锁持有时间短，高并发下才有明显影响。 | 可改为 `tokio::sync::RwLock<String>`，或接受现状并注明为已知技术债。 |

### 2.2 部分成立 / 需结合场景判断

| 问题 | 评估 | 说明 |
|------|------|------|
| **固定加密密钥** | 威胁模型相关。密钥可从源码推导，攻击者拿到 secure_store.dat 可解密。但需物理/文件系统访问，且当前主要防的是「随便看一眼」的场景。 | 若需抗本地攻击者，应做 per-device 派生；否则可视为「混淆」级别，暂不升级。 |
| **secure_store.dat 权限** | 在 Unix 上 fs::write 默认 644，其他用户可读。多用户桌面场景下是问题。 | 建议写入后 chmod 0o600；Windows 需单独考虑。 |
| **StorageBackend 同步阻塞** | 真实。sync I/O 在 async 命令中会阻塞。当前读写量小，影响有限。 | 可用 spawn_blocking 包装，或接受为低优先级优化。 |
| **空字符串重置 Gateway** | 按设计实现。空字符串重置为云端是产品决策，但确实容易被误用。 | 可要求显式参数（如 resetToDefault: true），或保留现状并文档说明。 |

### 2.3 误报或可忽略

| 问题 | 评估 | 说明 |
|------|------|------|
| **parent() 为 None** | 误报。store_path 为 data_dir.join("secure_store.dat")，parent 恒为 Some(data_dir)。 | 无需修改。 |
| **data_dir 回退 "."** | 边缘情况。Tauri app_data_dir 在正常环境下很少失败；失败时用 "." 可能不可写，但直接 panic 也可能更糟。 | 可记录日志或尝试更稳妥的回退，非紧急。 |
| **detectTauri 早于 StorageBackend** | 理论风险。Tauri 正常流程是 setup 先于 WebView，实际很少发生。 | 可加重试或 readiness 检测，优先级低。 |
| **blocking_lock 在 setup** | 当前 setup 为同步，blocking_lock 合理。 | 若未来 setup 改为 async，需一并调整。 |

---

## 三、优先级建议

### P0（建议尽快修）

1. **Gateway URL 覆盖**：避免每次启动覆盖用户配置  
2. **登出/刷新竞态**：防止登出后会话被恢复  
3. **fallbackInterval 泄漏**：防止 interval 泄漏导致内存/行为异常  

### P1（本迭代内考虑）

4. **set() JSON 解析**：避免静默数据丢失  
5. **secure_store.dat 权限**：多用户环境下限制为仅当前用户可读  

### P2（技术债/优化）

6. **GatewayUrlState 改为 RwLock**：减少 async 中的阻塞  
7. **StorageBackend 用 spawn_blocking**：避免 sync I/O 阻塞 runtime  

### P3（可选）

8. **加密密钥 per-device 派生**：提升本地攻击抵抗能力  
9. **localStorage 迁移校验**：降低 XSS 投毒影响（前提是已有 XSS 防护）  

---

## 四、总体结论

- **Subagent 发现**：约 25 条，去重后约 15 个独立问题  
- **确认真实 Bug**：5 个（Gateway 覆盖、登出竞态、interval 泄漏、JSON 静默丢数据、Mutex 阻塞）  
- **部分成立**：4 个（固定密钥、文件权限、sync 阻塞、空字符串重置）  
- **误报/可忽略**：4 个  

**客观评价**：审查有效，发现了若干真实问题，尤其是 Gateway URL 覆盖和登出/刷新竞态，对用户体验和安全性影响较大。固定密钥、JSON 解析和 fallbackInterval 泄漏也值得优先处理。部分发现属于架构/技术债，可按优先级逐步改进。
