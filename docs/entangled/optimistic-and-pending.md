# 乐观并发机制与 Pending Ops

> 路径参考：`novaic-app/src/data/entangled/dispatch.ts` 与 `Entangled/packages/client-rust/src/cache.rs`

## 1. 临时本地并发标识 (`_opt_`)
如果完全依赖双向推送返回，在弱网环境下用户点击按钮后必然感知到 1~2 秒甚至更高的极不愉快延时。所以，Entangled 在 UI 设计上深度使用了乐观并发（Optimistic Writes）：
1. 用户提交 Mutation（如发一条 Chat Message）。
2. 在前端或 Rust 层生成一个临时的、以 `_opt_` 开头的虚假 `id`。
3. `Cache` 立刻把它 `INSERT` 并告诉终端，这让文字聊天马上滑到最底！
4. 它被带上请求发送并在后端接受完整的 ID 分配或生成。

## 2. Pending Ops 表
这会带来一个可怕的状况。一旦 Websocket 突然断网、网络失败。临时行 `_opt_` 永远不会通过云端返回真的那个带有正确数据库数字的 `id` 的 Entity Object，也就会永远挂在“Loading…” 的状态。
- 为此，Rust 设置了一张名为 **`pending_ops`** 的记录表。所有被发出去正在半空中的 `_opt_` 数据均有一条镜像。
- 如果真的没有发成功，App 重连后它可以作为重发缓冲；
- 如果你试图彻底格式化用户会话，清理它是一切的关键。

## 3. Ghost "Sending..." 排障
在过去由于未把表列入联机清扫。导致出现了臭名昭著的幽灵排障现象：
> "服务器端已明确说 Sent，但你重新安装这台设备，UI 上仍叠加着好几条 Sending"。
根因在于：使用 `useMessages` 构建界面时，逻辑会自动把被判断为 `_opt_` 开头且存在本地表中的 User_Message 渲染成“正在发送风车”。
如今 `Cache::clear_all()` 如果执行，必定联合 `pending_ops` 一起铲走，根治这一死结。
