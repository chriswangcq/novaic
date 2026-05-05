# VmControl (Rust 终端引擎) 拆页地图
> 路径：`docs/vmcontrol/`

记录那些沉没在 `novaic-app/src-tauri/vmcontrol` 底部的 Rust Crate、硬核编译优化以及针对各平台怪异 Bug 解决史册。配搭 [docs/vmcontrol-architecture.md](../vmcontrol-architecture.md) 看。

## 目录索引

| 专题 | 说明 |
|------|------|
| [webrtc-unification.md](webrtc-unification.md) | **统一屏幕管线**：VmControl 如何把本地/设备画面归一到 WebRTC 媒体轨和 App 渲染面。 |
| [h264-hardware-encoding.md](h264-hardware-encoding.md) | **硬核抓取与压制 (VideoToolbox)**：这套修改自 RustDesk 的魔改系是怎么调用苹果硬件去扛起消抖、防丢帧和 CBR （恒定码率）的。 |
| [scrcpy-android-broadcaster.md](scrcpy-android-broadcaster.md) | **Scrcpy 双通道广播黑魔法**：处理手机多端共享：如果俩客户端同时点亮了一台 Android 实体机它为何不会炸？（底层 IDR 僵死锁解决） |
| [macos-sigtrap-cgevent.md](macos-sigtrap-cgevent.md) | **SIGTRAP 与 macOS 毒性案件簿**：深扒当时用跨平台 Enigo 发生闪退的“断言事故”，并全盘转向使用 core_graphics 生成原生 `CGEvent` 的键盘注入全解析。 |
