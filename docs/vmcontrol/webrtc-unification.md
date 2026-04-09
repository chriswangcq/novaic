# WebRTC 终极收编与弃用 noVNC

> 路径：`vmcontrol/src/peer.rs` 及相关的 Media Track 流下放

## 1. 过去的多协议混编痛点 (noVNC 惨剧)
在旧时代，你作为用户在系统打开一台新设备是个抽盲盒的体验：
如果是 Linux 虚拟系统，必须靠 Websocket 反射一个包含极度性能负担的 noVNC iframe 来让 CPU 用 JavaScript 去一格格画画。如果你用的是 macOS 远控，又可能变成另一套 MJPEG 图片堆叠刷屏法。
这在开发统一度、端到端延迟（Latency）及防抖全方面溃败。

## 2. All In WebRTC 架构设计
我们依托 `webrtc-rs` （或是由其他信令封装的底层核心库）建立起了一条标准的流体数据模型隧道。
现在的数据进入途径变成：

- **源视频发生器 (Source Generaters)**:
   无论是来自于给 Android 架设的 `scrcpy` 解复用器出来的原始帧数据；还是抓取 macOS 本地显示核心截取的内存像素。
   
- **单一漏斗转译为媒体轨 (Add Track)**:
  全部数据均被转译送去打上 `H.264` 或者其他指定硬件的编流印记（Profile/Level/RTP Header）并作为一块完整的 `opus` 音频与 `video` 媒体流。喂给 WebRTC 发射。

- **输入通道 (DataChannel)**:
  所有传向回本机的键盘点击、鼠标滚轮，以前也是走五花八门的 HTTP API 甚至专门的 TCP 协议，现在全都装在这一个 P2P 握手下的 `webrtc_data_channel`（使用 protobuf 甚至紧凑的 JSON）发向服务端解析，从而大幅降低由于信令拆开而带来的操作不同步现象。
