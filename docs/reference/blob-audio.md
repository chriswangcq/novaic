# Blob 附件与语音录制

> 对应原 `**HANDOVER.md` §十三**。

## Blob Service

新的大对象引用统一使用 `blob://{namespace}/{blob_id}`，详见
`docs/reference/blob-service.md`。历史文件接口已经物理删除；本页只保留当前附件与语音录制链路。

当前路径：

```text
附件上传 → Gateway POST /api/blobs/from-base64 → Blob Service /v1/blobs
附件访问 → Rust cache → Gateway POST /api/blobs/fetch → Blob Service /v1/blobs/{namespace}/{blob_id}
消息附件字段 → blob://user-file/{blob_id}
```

## 语音录制（Rust cpal）

Tauri WKWebView 中 `navigator.mediaDevices` 常为不可用，**麦克风走 Rust**：

```
invoke('start_audio_recording') → cpal 采集 PCM
invoke('stop_audio_recording') → hound 写 WAV → base64 → 上传
```

注意：`cpal::Stream` 使用 `unsafe impl Send/Sync`；WAV 体积大（约 11MB/分钟），后续可换 Opus 等压缩。
