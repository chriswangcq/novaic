# NovAIC 核心业务实体模型 (Entity Data Models)

> 这是记录整个系统中，最具价值和跨模块反复被操纵调用的数据核心基元结构。

所有业务流都是对这些实体（Entities）进行 CRUD 与流通；并且在由于 `Entangled` 大统一改版后，这套核心的生命定义权已经从各路凌乱纷杂的挂靠模块合并规入核心数据图谱。

---

## 1. Agent 核心执行代理

作为系统中你拥有并差遣的干员大基元：

- **结构简析**：
  * `agent_id` (PK): 全局唯一下发的 UUID。
  * `device_id` (FK): 这是极其重要的跨端纽带。如果不绑设备（即空缺），这只是条虚无思考会聊天的 AI。一绑定，这立马化为了这个设备的操作员，享有能发出命令透过 `Gateway / VmControl` 向此机器下打动作权限。
  * `status`: 常伴发的是其在生命周期（Idle / Computing / Suspended 等）。

## 2. Chat Message 对话序列（指令的载体与返回）

用户发个笑脸或者系统返回了满屏幕的日志全在这张被拆开揉磨无数遍的核心表：

- **结构简析**：
  * `message_id` (PK)
  * `role`: 标准划分，含 (`user`, `assistant`, 及极其特殊的 `system_log` 代表底层汇报情况不需人能全看懂) 
  * `content`: 文本、亦或者某些极度复杂的 JSON 字符串（前侧包含那些用来给被过滤解析了带有着 UI 面板组件命令的指令载荷）。
  * `status`（**legacy**, PR-21 之后只读）: 老的控制流旗帜，仍保留是因为还有读路径在依赖。
      * `sending` / `completed` / `error`：详见 git blame 历史。
  * `lifecycle` (**PR-21 新增, 单一权威状态**): `pending → claimed → consumed | orphaned | deduped`，详见 [`docs/architecture/scope-lifecycle.md`](./scope-lifecycle.md)。
      * 所有写入必须走 `Entangled` 的 `POST /v1/messages/{id}/transition` 单一入口，CI (`scripts/ci/lint_lifecycle.sh`) 强制阻挡裸 `UPDATE`。
  * `claimed_by_scope` (PR-21): 当 `lifecycle='claimed'` 时记录认领它的 scope_id，便于 PR-26 孤儿扫描。
  * `lifecycle_updated_at` (PR-21): epoch ms，用于诊断和 SLA 追踪。

## 3. Context & Memories 单切分快照

由于引入的 `Cortex V3 （无状态大脑）`。我们废弃了那种将海量聊天全都挤入一串庞大的 json 放进传统 DB。
- 新的 `Node / Step Tree` 快照结构不是传统的 Entity 表格了，而是存放向底部的云 `S3`/硬盘对象体：代表着某个特定状态下的知识结晶体，是高度分离压缩了之后的压缩片。不再拥有诸如 `user/uuid_xxx/session` 极长冗杂的实时绑定读写！
