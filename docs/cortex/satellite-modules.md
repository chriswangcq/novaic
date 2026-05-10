# 卫星模块速查（非核心路径）

> 以下模块在 `novaic_cortex/` 中存在，**不**单独开长文；此处说明职责与何时再读源码。

## 1. `entangled_access.py`

- **`get_entangled_client()`**：单例 **`EntangledClient`**，读 **Entangled** 实体（如 agent 元数据）。
- 环境：**`ENTANGLED_SERVICE_URL`**，或回退 **`common.config.ServiceConfig`** / 默认 `http://127.0.0.1:19900`。
  > 注：Entangled 独立服务已并入 `Entangled/packages/server-python/entangled/app`，启动方式：`python -m entangled.app.main`。
- 注释说明：**多数业务应留在 owning service/package**；Cortex 直连仅适用于纯数据读，或 Cortex 组装上下文时的特殊需求。

## 2. Blob storage helpers

- Cortex active path stores large tool/runtime payload bytes behind `blob://...`
  references and keeps prompt-facing observations small.
- Large bytes belong to Blob Service; Cortex owns work-trace semantics,
  payload manifests/status, payload refs, and projection rules.
- Live `/ro` and `/rw` files go through LogicalFS. The Blob object adapter lives
  in `novaic-logicalfs`, below that file authority. Cortex does not own S3/OSS
  credentials or Blob object API details.

## 3. `step_result_projection.py`

- 读取 Cortex step 中的 **工具结果**，完成格式化、解析、与 LLM 表示转换；已获取的
  字节内容可转换为 **`_mcp_content`** 块，默认上下文只保留 observation 摘要与 payload ref。

---

若某条调用链贯穿 Entangled / Blob payload / step result projection，可从这里跳到对应 `.py` 再对照 Blob Service 边界文档。
