# Blob 附件与语音录制

> 对应原 `**HANDOVER.md` §十三**。

## Blob Service

新的大对象引用统一使用 `blob://{namespace}/{blob_id}`，详见
`docs/reference/blob-service.md`。历史文件接口已经物理删除；本页只保留当前附件与语音录制链路。

当前路径：

```text
小附件上传 → Gateway POST /api/blobs/from-base64 → Blob Service /v1/blobs
大附件上传 → Gateway upload-config → Blob multipart upload → Gateway register
附件访问 → Rust cache → Gateway POST /api/blobs/fetch → Blob Service /v1/blobs/{namespace}/{blob_id}
消息附件字段 → blob://user-file/{blob_id}
```

## 语音录制（Rust cpal）

Tauri WKWebView 中 `navigator.mediaDevices` 常为不可用，**麦克风走 Rust**：

```
invoke('start_audio_recording') → cpal 采集 PCM
invoke('stop_audio_recording') → 临时 WAV → 显式压缩 AAC/M4A → 返回压缩字节
音频上传 → Blob multipart → blob://audio-input/{blob_id}
```

注意：`cpal::Stream` 使用 `unsafe impl Send/Sync`。WAV 只作为编码中间
文件；正常语音消息不再上传 WAV/base64。当前压缩编码主路径使用 macOS
`afconvert` 产出 `audio/mp4` / AAC；不支持的平台会显式失败，不启用 WAV
fallback。

## 音频压缩目标边界

当前已实现目标路径：

```text
Rust recorder → compressed AAC/M4A container → blob://audio-input/{blob_id}
```

约束：

- 优先在客户端/Rust 录制链路产出压缩容器，减少上传体积。
- Blob Service 只存储压缩后的字节和元数据，不在保存时隐式转码。
- 如果某个 audio tool 需要另一种格式，必须显式调用转码/解释工具，产出新的 BlobRef。
- 音频 Blob 元数据应包含 duration、codec、sample rate、channels、size。

详细实施计划见 `docs/roadmap/blob-large-file-multipart-audio.md`。
