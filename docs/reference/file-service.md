# 文件服务与语音录制

> 对应 **`HANDOVER.md` §十三**。

## 文件 API（`/api/files/`）

历史双系统已统一到 **`/api/files/`**。

- 截图等：`ImageStorage` → File Service `from-base64`（概念）。
- 聊天附件：`uploadChatFile` → Gateway `POST /api/files/upload` → `files` 表。
- 读取：`GET /api/files/{file_id}` → Gateway 校验 `user_id` → 代理 File Service。

## 语音录制（Rust cpal）

WKWebView 中 `navigator.mediaDevices` 常不可用，**麦克风走 Rust**：

```
invoke('start_audio_recording') → cpal 采集 PCM
invoke('stop_audio_recording') → hound 写 WAV → base64 → 上传
```

实现注意：`cpal::Stream` 的 Send/Sync 与 WAV 体积（可后续压缩 Opus）。
