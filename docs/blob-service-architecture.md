# Blob Service 存储架构概览

> 路径参考：`novaic-blob-service/`。该目录是当前 Blob Service 的实现目录。

Blob Service 是字节与对象存储基础设施。它和 Entangled、Cortex 的边界不同：

- Entangled 保存可同步的产品实体和状态。
- Cortex 保存 Agent 工作轨迹、scope、observation、payload ref。
- Blob Service 只保存字节、对象树、Blob 元数据、租户边界和后端对象存储适配。

它不解释文件属于什么业务，不生成 prompt，不总结 payload，也不承担 Agent Monitor 文案。

## 1. 定位脱钩

大对象不应该塞进 Runtime、Cortex、Entangled 或普通业务实体。当前主路径是：

```text
App / Runtime / Cortex → BlobRef → Blob Service → Disk or S3-compatible backend
```

新路径统一用：

```text
blob://{namespace}/{blob_id}
```

Blob Service 默认监听独立服务端口，避免大字节读写和 Agent/业务控制面混在一起。

## 2. 核心大件代理权与中转隔离

当前实现：

- `/v1/blobs`：JSON base64 上传，仅适合小附件。
- `/v1/blobs/{namespace}/{blob_id}`：读取字节。
- `/v1/blobs/{namespace}/{blob_id}/info`：读取 Blob 元数据。
- `/v1/blobs/{namespace}/{blob_id}/presign`：GET presign/proxy 访问。
- `/v1/blobs/uploads/*`：multipart upload session，part 使用 raw bytes，
  complete 后才生成稳定 Blob metadata。
- `/v1/objects/*`：Cortex object-tree 的 `put/get/list/move/delete` 原语。
- S3-compatible 后端当前使用 whole-object `put_object` 和 GET presign。

未实现的能力不要当成当前主路径：

- direct browser/App upload to object storage
- PUT/POST upload presign
- server-side audio transcode/compression

这些能力的目标方案见 `docs/roadmap/blob-large-file-multipart-audio.md`。

## 3. 音频与转换边界

当前语音录制链路是 Rust `cpal` 采集 PCM、`hound` 写临时 WAV、macOS
`afconvert` 压成 AAC/M4A，然后通过 multipart 上传为
`blob://audio-input/...`。WAV 只是编码中间文件，不是上传 fallback。

音频压缩是显式产品路径：

```text
Rust recorder → compressed AAC/M4A container → Blob upload → audio tool consumes blob://audio-input/...
```

Blob Service 不应在保存字节时偷偷转码。需要转码时，应由显式 tool 或 pipeline 读取一个 BlobRef，产出另一个 BlobRef，并把处理结果作为 observation/payload ref 写回上层。
