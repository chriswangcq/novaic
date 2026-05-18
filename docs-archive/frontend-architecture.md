# Frontend (React / Tauri 交互层) 架构总览

在脱离了繁重的 Web 业务与冗杂的数据库缓存后，`novaic-app` 成为了一套极度干净的“薄壳”展现层（Thin-Client）。
前端从“重度数据管家”彻底缩退成了真正的“大屏呈现渲染器”。

---

## 1. 结构大分属
整个前端体系建立在非常边界分明的两极抽象：
- **无数据的主宰：Tauri 与跨端 IPC** (`src-tauri` / `src/invoke.ts`)
  UI 层不再接触硬盘和底层网络。所有的强业务动作（拉会议、启动 WebRTC、清洗缓存）通过跨语言异步 IPC（`invoke`）去呼叫底层的 Rust 代理，并在得到指令之后用 `listen` 去响应原生世界的广播（比如由于外部连进而导致的浮窗弹起）。
- **完全解耦的 React 生命周期** (`src/pages`, `src/components/`)
  界面视图被拆分为完全无状态（Stateless）或交由 `Zustand` 和 `Entangled Factory` 管理的可变组块引擎渲染机制。

## 2. 三大数据支柱：如何避免一盘散沙

### A. 全局配置与轻量持久化 (Local Settings)
基于浏览器的 `localStorage` 或轻量的存储接口来保存用户的界面主观意愿：比如 `Dark/Light Theme`、界面左右面板收起的宽度占比（SplitPane layout bounds）以及一些快速偏好设置。

### B. 会话与运行态流转 (Zustand Global State)
- **生命期**：关掉面板便灰飞烟灭的会话缓存池。
- **职责**：维护“当前鼠标按下的哪个聊天气泡（被选中的菜单索引）”、以及目前悬浮或侧边挂靠呈现的到底是谁的 Agent 信息等，提供极速响应交互效果而无需下探底座或云端请求。

### C. 实体业务数据呈现 (Entangled 视图同步源)
完全剥离了传统繁重的 `Axios / React Query` 分布式轮询方案。
所有的聊天队列、系统大纲、任务列表统一来自于前面讲过的 Entangled Rust Client 倒推上喷。前端针对这些只是做了简单得不能再简单的 `map()` 循环挂载甚至 `List Virtualization (虚拟长列表渲染)` 仅仅为应对一次推上来的两万条日志。

细读同级目录 `docs/frontend/`，深入感受界面无数据论的极致实践！
