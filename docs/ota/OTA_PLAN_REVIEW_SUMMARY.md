# OTA 实施方案 — 5 名 Subagent 评审意见汇总

> 对 `OTA_RE_ENABLE_IMPLEMENTATION_PLAN.md` 初稿的评审结论，已整合进 `OTA_RE_ENABLE_IMPLEMENTATION_PLAN_V2.md`

---

## 一、评审分工与结论

| Subagent | 重点 | 核心意见 |
|----------|------|----------|
| **1. 架构与流程** | Phase 划分、启动顺序、fallback | 伪代码有 bug（w 未定义）；补充 fallback 决策树；移动端 show 需明确；窗口创建时机需验证 |
| **2. Capability 与安全** | URL 校验、匹配规则、安全 | 推荐 urlpattern 或 host 白名单；明确匹配规则；Gateway 为信任根；CSP 启用时需验证 |
| **3. 前端与兼容性** | __TAURI__ 检测、纯浏览器、移动端 | 必须在 render 之前同步检测；纯浏览器需 Fallback；移动端 show 逻辑需补充；关注 iOS postMessage bug |
| **4. 实现细节** | fetch、日志、任务顺序 | 超时区分 connect/整体；错误分类；任务依赖调整；日志格式统一；缓存用 version 失效 |
| **5. 部署与运维** | 发布顺序、回滚、灰度 | 先前端再 Gateway；回滚流程文档化；保留旧版本目录；运维检查清单 |

---

## 二、主要修改点（初稿 → V2）

### 2.1 Phase 1

| 修改 | 说明 |
|------|------|
| 伪代码修正 | `w.show()` 在正确作用域，`did_navigate` 逻辑清晰 |
| Fallback 决策树 | 补充完整分支：窗口 None、navigate 失败、非 2xx、JSON 失败 |
| 移动端 show | 明确无论桌面/移动端，OTA 结束时必须 show() |
| 环境变量 | 支持 1/true/yes/on（不区分大小写） |
| fetch 实现 | connect_timeout 3s、整体 6s；serde_json 解析；错误分类 |

### 2.2 Phase 2

| 修改 | 说明 |
|------|------|
| 实现方式 | 明确 urlpattern 与 host 白名单二选一 |
| 匹配规则 | 补充协议、host、路径、部署约束 |

### 2.3 Phase 3

| 修改 | 说明 |
|------|------|
| 执行时机 | **必须在** `ReactDOM.render` 之前，同步检测 |
| 检测条件 | `isOtaOrigin() && !('__TAURI__' in window)` |
| Fallback 文案 | 主+副文案，覆盖 capability 未匹配等边缘情况 |

### 2.4 Phase 4

| 修改 | 说明 |
|------|------|
| 合并到 1–3 | 日志、常量作为配套，不单独成 Phase |
| 日志规范 | tracing + 格式 + 级别约定 |
| 缓存 | 可选，version 失效，格式明确 |

### 2.5 新增章节

| 章节 | 内容 |
|------|------|
| 部署与运维 | 发布顺序、回滚流程、运维检查清单 |
| 安全与配置 | 权限边界、Gateway 信任、CSP、新命令流程 |

---

## 三、任务清单调整

**原顺序**：1 恢复逻辑 → 2 开关 → 3 校验 → 4 前端 → 5 日志 → 6 缓存 → 7 文档

**V2 顺序**（按依赖）：

1. NOVAIC_OTA_ENABLED 开关
2. fetch + navigate
3. URL 校验
4. 移动端 show
5. 窗口创建时机验证
6. 日志与 fallback
7. 前端 __TAURI__ 检测
8. 部署文档
9. 可选：缓存

---

## 四、风险补充

| 风险 | 来源 | 缓解 |
|------|------|------|
| 窗口在 spawn 时未创建 | Subagent 1 | 验证时机，必要时轮询 |
| 移动端 show 缺失 | Subagent 1, 3 | 任务 #4 明确补充 |
| iOS postMessage JSON bug | Subagent 3 | 关注 Tauri #9266 |
| Service Worker | Subagent 3 | 项目未使用，未来不引入 |
| 回滚时旧版本被删 | Subagent 5 | 约定保留上一版本 |

---

## 五、文档索引

| 文档 | 用途 |
|------|------|
| `OTA_RE_ENABLE_IMPLEMENTATION_PLAN.md` | 初稿 |
| `OTA_RE_ENABLE_IMPLEMENTATION_PLAN_V2.md` | 完善版（实施依据） |
| `OTA_PLAN_REVIEW_SUMMARY.md` | 本文，评审汇总 |
| `OTA_RE_ENABLE_IMPLEMENTATION_PLAN_REVIEW.md` | Subagent 3、4 生成的详细评审 |
