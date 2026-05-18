# 槽位级订阅路网体系 (NavState Slots)

> 路径参考：`novaic-app/src-tauri/src/commands/nav.rs` 和 `src/data/entangled/nav.ts`

## 1. 订阅交叉与“互相踩死”的过往 (Static PrevNav 缺陷)
在这个实时端侧架构进入高楼阶段时暴露出巨大弱点。过去的组件级由于全局静态依赖同一个订阅变量：
- 一开始组件说：“我订阅聊天，取消主界面的刷新”。
- 然后突然跳出一个提示悬浮框组件高喊：“我要订阅这套设备的更新！取消不是它所在的一切刷新”。
这导致在弹窗的 0.1 秒内，背后的主聊天室被默默取消了后端信道，导致全屏幽灵般失去了实时的功能更新。

## 2. NavState 引入了插槽系统
针对跨状态共享数据，由于 Entangled 原本只有一层逻辑状态，我们现在给 Rust 底层和 TypeScript 切割出 `HashMap<slot_name, Vec<SubSpec>>`。
每一套视窗（或是每一种行为模块）：例如左边的栏叫 `"main_menu"`、弹出悬浮层叫 `"vm-deviceId"`，拥有自己的插槽 `slot`。
- 新的路由钩子 `useNavChanged('vm-context', { deviceId }, ... { slot: ... })`。
- 这使得各组件可以在互不统属的情况下提出自己的要求，Rust 底层在收到每个不一样的 Slot 请求后：
- 如果它们都需要订阅聊天表，这不会抛错。底侧会自动为其进行 `Refcount (引用计数+1)`。

## 3. 并发解构与单一渲染管道
在处理 `App.tsx` 中的全局大导航变更时，过去由三个分别的 `useEffect` 同时检测环境：很容易再次出现并行推送不同的频道去给 Rust 覆盖导致被强行注销。
目前的最终解为 `deriveDesiredMainNav` 函数结合一根单发 Effect 通道：
不论是进入了 `conversation` 仍是 `home`；只要环境触发变化。这个函数把你需要被订阅或剔除的操作在内部**串行化（Enqueue）**，用标准的 `Command` 发送：它一次性通过 Rust 确保所有对应的环境表一起激活（包含聊天、状态、甚至是绑定的 AgentBinding 监控等），完成极其复杂但在操作层面零竞态条件的客户端同步闭环。
