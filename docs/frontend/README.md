# Frontend UI 拆页地图
> 路径：`docs/frontend/`

前端是最直扑用户感受的一环，这套薄壳如何把极速与性能同时拿捏住？配搭 [docs/frontend-architecture.md](../frontend-architecture.md) 看。

## 目录索引

| 专题 | 说明 |
|------|------|
| [webrtc-ui-rendering.md](webrtc-ui-rendering.md) | **视频流上墙**：底层拿到一坨 P2P 轨道流，怎么安全优雅地挂载在 `<video>` 实例里面并且随着容器缩放响应式保帧的。 |
| [zustand-ephemeral-state.md](zustand-ephemeral-state.md) | **瞬时态收纳引擎**：用 Zustand 规整碎片化界面变迁；为什么不把 UI 状态全存进 Entangled？ |
| [tauri-ipc-commands.md](tauri-ipc-commands.md) | **IPC 并发天堑**：调用 `invoke` 跟 Rust 打黑话时的反序列化大坑，如何确保高频信号（比如鼠标划取连发）不会把 Tauri 的频道给糊死。 |
| [virtual-scrolling-and-logs.md](virtual-scrolling-and-logs.md) | **万条记录不闪退**：面对 AI 执行时疯狂喷射几十个大步骤跟两万行 Shell 日志，UI 是怎么处理 Dom 复用的。 |
