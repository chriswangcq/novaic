# 历史文件服务与语音录制

> 对应原 `**HANDOVER.md` §十三**。

## 历史文件服务（`/api/files/`）

这是迁移期考古页，不是新代码入口。新的大对象引用统一使用
`blob://{namespace}/{blob_id}`，详见 `docs/reference/blob-service.md`。
历史 `**/api/images/`** 与 `**/api/files/**` 曾统一到 `**/api/files/**`。

```
截图/附件 → uploadChatFile() / Gateway POST /api/files/from-base64 → Storage-A /api/files/from-base64
访问 → GET /api/files/{path} 或 POST /api/files/fetch → Gateway 校验 user_id → 代理 Storage-A
```

上述路径只能作为历史数据迁移/清理参考；不要在新业务路径继续生成
`fs://`、`/api/files/*` 或 service-private URL。

## 语音录制（Rust cpal）

Tauri WKWebView 中 `navigator.mediaDevices` 常为不可用，**麦克风走 Rust**：

```
invoke('start_audio_recording') → cpal 采集 PCM
invoke('stop_audio_recording') → hound 写 WAV → base64 → 上传
```

注意：`cpal::Stream` 使用 `unsafe impl Send/Sync`；WAV 体积大（约 11MB/分钟），后续可换 Opus 等压缩。
