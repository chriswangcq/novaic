# VmControl & 端侧设施底座架构总览

在 `novaic-app/src-tauri/vmcontrol/` 之下，藏有一只纯 Rust 打造的高手办级猛兽。
它早已远超一个简单的“网页调个 HTTP 的工具”。它是一个包含了 **WebRTC 实时流转发**、**硬件H.264压制** 以及与 **操作系统底层驱动事件桥接** 的黑客级系统模块。

---

## 1. 结构定位
Tauri 是一个用于挂载前台 WebUI (React/Vite) 的壳子，但你不能用 JS 来完成毫秒级打游戏级别的视频录制投射。
`vmcontrol` 就是附着在这个进程边界里作为大后盾服务。

- 对于同机启动的 `novaic-app`，它提供了本地极低延迟的高频鼠标轨迹与剪切板桥梁。
- 对于身在云端的 `Cortex/Gateway` 来说，`vmcontrol` 是一双在内网“拥有眼睛与手的机器总管”：它通过 CloudBridge WS 时刻向外宣告：“我接管了一台 Android 设备，或者是一台 QEMU 的机器”。

## 2. 核心大一统：全面进入 WebRTC
如果你回溯了之前的系统版本，你会发现早年控制不同机器要开不同的网页（开 Android 要看 mjpeg，看 Linux 要调个无窗口的 noVNC iframe 刷流）。
这一切被一次伟大的网络架构升级颠覆。在核心里它如今是一个宏大的 **WebRTC Peer Connection 承接引擎**！不管是：
- QEMU 所在的纯虚拟 VNC Linux 系统。
- 真机通过 Scrcpy 协议拔下来的安卓手机屏幕比特流。
- 还是干脆录制了本地操作 macOS 的桌面视频片段（VideoToolbox 控制）。

这些乱七八糟所有底层的数据源，统统被 `vmcontrol/src/video` 等模块压扁揉碎，最后全部注入到了唯一统一的 **WebRTC Data Channel 与 Media Track** 里送达。
你无论看的是啥设备，在前端全被缩为同一个 `<video>` 组件播送。这是一次极度舒适的技术降维打击！

详情参阅同级 `docs/vmcontrol/` 细颗粒度文档，那里记录着它是怎么抗击网络风暴，甚至处理底层 Mac 内存锁崩溃硬仗的。
