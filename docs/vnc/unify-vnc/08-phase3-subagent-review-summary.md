# Phase 3 改动 — 10 Subagent 审核汇总

> 2025-03-12：对 Phase 3（VNC 后端统一）改动进行 10 名 subagent 全面审核，客观评估并吸收确实有问题之处。

---

## 一、审核范围

| 模块 | 文件 | 改动概要 |
|------|------|----------|
| p2p | vnc_endpoint.rs | 新增 ensure_vnc_endpoint（maindesk + subuser 轮询 + Unix 代理） |
| p2p | tunnel.rs | 简化为调用 ensure_vnc_endpoint，移除 find_vnc_target |
| vmcontrol | vnc.rs | 使用 ensure_vnc_endpoint 替代 find_vnc_socket |
| 前端 | types/vnc.ts, DeviceVNCView, VNCView, VmUserVNCView | RFB_OPTIONS 统一 |

---

## 二、Subagent 发现汇总

### 2.1 已确认并修复（subagent 已实现）

| # | 问题 | 处理 | 来源 |
|---|------|------|------|
| 1 | **Path traversal** — resource_id 未校验，可注入 `../` 等 | ✅ `validate_resource_id()` 白名单 `[a-zA-Z0-9_-]`，max 80 字节 | 安全 subagent |
| 2 | **Registry 无限增长** — VM 停止后 port 文件消失，但 registry 不清理 | ✅ 命中 registry 时检查 port 文件存在，否则 remove stale | 错误处理 subagent |
| 3 | **id_len overflow** — tunnel 中 id_len 未校验 | ✅ 分配前校验 id_len | 安全 subagent |

### 2.2 高优先级（需修复）

| # | 文件 | 问题 | 评估 |
|---|------|------|------|
| 4 | vnc_endpoint.rs | **Empty vm_id** — `":alice"` 通过 filter，vm_id="" → 无效路径 `share-/vnc-alice.port` | 确实有问题。validate_resource_id 对 subuser 未检查 vm_id 非空 |
| 5 | vnc_endpoint.rs | **Double-registration race** — 并发同一 resource_id 可同时创建代理，remove_file 可能删掉对方 socket | 确实有问题。需 per-resource 创建锁 |
| 6 | vmcontrol vnc.rs | **Error mapping** — 所有错误映射为 404，Invalid/Internal 应 400/500 | 建议修复，非阻塞 |

### 2.3 中优先级（建议修复）

| # | 问题 | 评估 |
|---|------|------|
| 7 | **Subuser retry 成本** — 3 次重试 × 30s 轮询 ≈ 90s | 可接受。Xvnc 启动慢时需等待；可后续优化为「仅 connect 失败时重试」 |
| 8 | **vncStream.ts** 未使用 RFB_OPTIONS | 建议：使用 RFB_OPTIONS 并显式 override clipViewport。当前为 dead code，可延后 |
| 9 | **VM 停止时 proxy 不清理** — 无 shutdown_proxy_for_vm | 架构级改动，需 vmcontrol 与 p2p 生命周期联动。建议 Phase 4 或后续迭代 |

### 2.4 低优先级 / 暂不处理

| # | 问题 | 评估 |
|---|------|------|
| 10 | single VM novaic-vnc-*.sock fallback | 无证据表明旧代码有此逻辑，保持严格匹配 |
| 11 | clipViewport 与 scaleViewport | noVNC 支持同时使用，无冲突 |
| 12 | vncStream clipViewport: false | 有意为之（frame capture），保留并更新注释 |
| 13 | vmcontrol 路由 doc 与 :id 命名 | 文档不一致，低优先级 |

---

## 三、各 Subagent 结论摘要

| Subagent | 关注点 | 主要发现 |
|----------|--------|----------|
| 1 | vnc_endpoint 逻辑 | Critical: empty vm_id、path traversal、double-registration race、无 VM 停止清理 |
| 2 | tunnel.rs | Medium: subuser retry 成本高；其余 OK |
| 3 | vmcontrol vnc 路由 | Medium: 错误全映射 404；doc 与 route 命名不一致 |
| 4 | RFB 前端 | Low: vncStream 未更新；clipViewport 在 constructor 中无效但无害 |
| 5 | subuser proxy 竞态 | Critical: 并发创建 race；registry 路径正确；VM 停止无清理 |
| 6 | 错误处理 | Registry 已加 port 文件检查；30s/500ms 合理；port 文件删除 OK |
| 7 | 安全 | 已实现 validate_resource_id；tunnel id_len 校验 |
| 8 | 调用链 | resource_id 格式一致；vmcontrol 路由由 Gateway 调用；vncStream 为 dead code |
| 9 | 资源生命周期 | proxy 永不退出；registry 不清理；需 shutdown_proxy_for_vm |
| 10 | 回归 | 无 subuser 行为回归；vmcontrol 兼容；vncStream 有意 override |

---

## 四、待修复清单

### 必须修复（已实现）

1. **vnc_endpoint validate_resource_id** — ✅ subuser 分支增加 `vm_id.is_empty()` 检查
2. **vnc_endpoint 创建竞态** — ✅ 使用 `CREATION_LOCKS`（per-resource_id `Arc<Mutex<()>>`），创建代理时持锁

### 建议修复（已实现）

3. **vmcontrol vnc.rs** — ✅ 按错误内容映射 400/500（Invalid→400，Failed to create/bind→500）
4. **vncStream.ts** — ✅ 使用 RFB_OPTIONS，override clipViewport

### 后续迭代（已实现）

5. **shutdown_proxy_for_vm** — ✅ VM 停止时 abort proxy 任务、移除 socket、清理 registry；stop_vm 中调用
6. **Subuser retry 优化** — 暂不实现，可后续优化

---

## 五、参考文档

| 文档 | 说明 |
|------|------|
| docs/VNC_ENDPOINT_PHASE3_REVIEW.md | vnc_endpoint 详细审查 |
| docs/PHASE3-SECURITY-REVIEW.md | 安全审查与 validate_resource_id |
| docs/PHASE3_ERROR_HANDLING_REVIEW.md | 错误处理与 registry 清理 |
| docs/PHASE3-RESOURCE-LIFECYCLE-REVIEW.md | 资源生命周期与 shutdown 建议 |
