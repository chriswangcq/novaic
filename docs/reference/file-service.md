# 文件服务与语音录制

> 对应原 `**HANDOVER.md` §十三**。

## 文件服务统一（`/api/files/`）

历史 `**/api/images/`** 与 `**/api/files/**` 已统一到 `**/api/files/**`。

```
截图 → ImageStorage.save_image() → POST File Service /api/files/from-base64
聊天附件 → uploadChatFile() → Gateway POST /api/files/upload → files 表
访问 → GET /api/files/{file_id} → Gateway 校验 user_id → 代理 File Service
```

## 语音录制（Rust cpal）

Tauri WKWebView 中 `navigator.mediaDevices` 常为不可用，**麦克风走 Rust**：

```
invoke('start_audio_recording') → cpal 采集 PCM
invoke('stop_audio_recording') → hound 写 WAV → base64 → 上传
```

注意：`cpal::Stream` 使用 `unsafe impl Send/Sync`；WAV 体积大（约 11MB/分钟），后续可换 Opus 等压缩。