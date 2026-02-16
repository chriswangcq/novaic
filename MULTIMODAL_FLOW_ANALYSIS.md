# 多模态处理流程分析

## 用户疑问
> LLM handler 进行 context 组装时，是不是原来那些多模态识别逻辑都不用了？

## 回答：仍然需要，但作用变了

---

## TRS 架构下的多模态处理流程

### 完整调用链

```python
# llm_handlers.py:handle_llm_call()

# Step 1: 展开 result_id → TRS 标准格式
messages_for_llm = expand_messages_for_llm(messages, provider=provider)
# 输入:  [{"role": "tool", "result_id": "res_123", "tool_call_id": "call_1"}]
# 输出:  [{"role": "tool", "content": '{"_mcp_content": [...]}', "tool_call_id": "call_1"}]

# Step 2: 清理顺序
sanitized_messages = sanitize_context(messages_for_llm)
# 确保 tool results 紧跟 assistant+tool_calls

# Step 3: 多模态处理
processed_messages = process_multimodal_messages(sanitized_messages, provider)
# 解析 _mcp_content，提取图片，转为 LLM API 格式
```

---

## 各环节详解

### Step 1: `expand_messages_for_llm`

**作用**: 将 `result_id` 转为 TRS 标准的 `_mcp_content` 格式。

**TRS SDK 返回** (`to_llm_content`):
```python
# trs_sdk.py:to_llm_content()
{
  "_mcp_content": [
    {"type": "text", "text": "执行成功"},
    {"type": "image", "data": "iVBORw0KG...", "mimeType": "image/png"}
  ]
}
# ↑ 序列化为 JSON 字符串
```

**为什么不直接返回 OpenAI 格式？**
因为 `_mcp_content` 是**通用中间格式**，兼容多种场景：
- OpenAI: 需要转为 `image_url` + user message
- Anthropic: 需要转为 `image` + source
- 其它 provider: 可能有不同格式

### Step 2: `sanitize_context`

**作用**: 确保 tool results 紧跟 assistant message（OpenAI API 要求）。

**不受 TRS 影响**: 仍然需要，因为 context 顺序要求不变。

### Step 3: `process_multimodal_messages`

**作用**: 
1. 解析 tool result 的 `content`（JSON 字符串）
2. 识别 `_mcp_content` 字段（优先级最高）
3. 提取图片，生成纯文本版 tool result
4. 将图片作为单独的 user message 添加

**为什么仍然需要？**

OpenAI/Anthropic API **不支持在 tool result 中直接放图片**，必须：
- Tool result: 纯文本
- 图片: 单独的 user message

**代码逻辑**:
```python
# context.py:process_multimodal_messages()

# 1. 检测 _mcp_content（TRS 返回的标准格式）
if "_mcp_content" in result:
    for item in result["_mcp_content"]:
        if item["type"] == "image":
            images.append({"data": item["data"], "mime_type": item["mimeType"]})
        elif item["type"] == "text":
            text_parts.append(item["text"])
    
    # 找到了 _mcp_content，直接返回（不再检查其他字段）
    return text, images

# 2. 降级检测（兼容旧格式）
if "screenshot" in result:
    images.append({"data": result["screenshot"], "mime_type": "image/png"})
```

---

## TRS vs 传统多模态处理对比

### 传统方式（无 TRS）

```python
# 工具返回
{"screenshot": "base64..."}
  ↓ 直接存入 context
{"role": "tool", "content": '{"screenshot": "base64..."}'}
  ↓ process_multimodal_messages
1. 解析 JSON
2. 检测 "screenshot" 字段
3. 提取 base64
4. 转为 user message
```

**特点**:
- context 存储包含完整 base64
- 每次加载 context 都要传输大量数据
- 多模态识别逻辑直接扫描字段名（`IMAGE_FIELD_NAMES`）

### TRS 方式（新架构）

```python
# 工具返回
{"screenshot": "base64..."}
  ↓ Tools Server 推 TRS
TRS 识别 "screenshot"，存入 File Service，返回 result_id
  ↓ 存入 context
{"role": "tool", "result_id": "res_123"}
  ↓ expand_messages_for_llm (LLM 调用前)
TRS.to_llm_content() → '{"_mcp_content": [{"type": "image", "data": "base64..."}]}'
  ↓ process_multimodal_messages
1. 解析 JSON
2. 检测 "_mcp_content" 字段（优先）
3. 提取 base64
4. 转为 user message
```

**特点**:
- context 存储只有 result_id（体积减少 90%+）
- TRS 统一处理多模态识别（Tools Server 端）
- process_multimodal_messages 仍需要，但现在识别的是 **标准的 `_mcp_content`**，而非零散的字段名

---

## 关键变化

### ❌ 不需要的逻辑

**在 LLM handler 的 context 组装时**，以下逻辑**被 TRS 接管**：
- ✅ ~~识别 `screenshot`、`image_base64` 等字段~~  
  → TRS 在工具执行后立即识别，存入时已规范化
- ✅ ~~判断字符串是否为 base64 图片~~  
  → TRS 在 create 时完成
- ✅ ~~将图片存入 File Service~~  
  → TRS 自动完成，返回 URL

### ✅ 仍需要的逻辑

1. **`expand_messages_for_llm`** - 新增，必需  
   按需将 result_id 转为完整 content（调用 TRS /for-llm）

2. **`sanitize_context`** - 不变，必需  
   确保 tool results 顺序正确（OpenAI API 要求）

3. **`process_multimodal_messages`** - 不变，必需  
   提取图片为单独的 user message（OpenAI/Anthropic API 要求）

**但识别来源变了**：
- 旧: 扫描 `IMAGE_FIELD_NAMES` 各个字段
- **新: 优先识别 `_mcp_content`**（TRS 返回的标准格式）

---

## 代码验证

### multimodal.py 的识别优先级

```python
def extract_from_result(result: Dict[str, Any]) -> Tuple[str, List[Dict]]:
    # 优先级 1: _mcp_content（TRS 返回格式）✅
    if "_mcp_content" in result:
        # ... 解析 _mcp_content
        if text_parts or images:
            return text, images  # 找到后直接返回
    
    # 优先级 2: content 数组（MCP 标准）
    if "content" in result and isinstance(result["content"], list):
        return _parse_content_array(result["content"])
    
    # 优先级 3: 传统字段名（向后兼容）
    for field_name in IMAGE_FIELD_NAMES:
        if field_name in result and _is_likely_base64_image(result[field_name]):
            # ...
```

**关键**: `_mcp_content` 优先级最高，找到后直接返回，不再检查其他字段。

### TRS 已完成的工作

在 TRS 的 `create_from_raw` 阶段：
```python
# trs_sdk.py:_parse_raw_to_items()
def _parse_raw_to_items(raw: Any):
    # 1. 检测 IMAGE_FIELD_NAMES 字段 ✅
    for field in IMAGE_FIELD_NAMES:
        val = inner.get(field)
        if val and multimodal.has_images({field: val}):
            items.append(("image", {"data": val, "mimeType": "image/png"}))
            break
    
    # 2. 检测 _mcp_content / content 数组 ✅
    # 3. 检测其它嵌套格式 ✅
```

所以 **多模态识别已提前到 Tools Server（推 TRS 时）完成**。

---

## 结论

### ✅ 多模态识别提前到 TRS，但 LLM handler 仍需处理

| 环节 | 旧逻辑 | 新逻辑（TRS） | 是否需要 |
|------|--------|--------------|---------|
| **识别图片字段** | LLM handler 扫描 IMAGE_FIELD_NAMES | TRS create 时识别 | ❌ LLM handler 不再需要 |
| **存入 File Service** | LLM handler 或工具自己做 | TRS create 时完成 | ❌ LLM handler 不再需要 |
| **规范化格式** | 分散在各处 | TRS 统一规范（_mcp_content） | ❌ LLM handler 不再需要 |
| **展开 result_id** | 无 | expand_messages_for_llm | ✅ **新增，必需** |
| **清理顺序** | sanitize_context | 不变 | ✅ 仍需要 |
| **提取图片为 user message** | process_multimodal_messages | 不变 | ✅ **仍需要** |

### 核心区别

**识别阶段前移**:
- 旧: LLM handler 读取 context 时识别图片字段
- 新: Tools Server 推 TRS 时识别，LLM handler 读取时图片已规范化为 `_mcp_content`

**识别逻辑复用**:
- `IMAGE_FIELD_NAMES`、`has_images`、`_is_likely_base64_image` 等逻辑
- 旧: 在 LLM handler 的 process_multimodal_messages 使用
- **新: 在 TRS SDK 的 _parse_raw_to_items 使用**
- process_multimodal_messages 现在优先识别 `_mcp_content`（不再扫描零散字段）

**所以原来的多模态识别逻辑没有废弃，而是重用在了 TRS 创建阶段！**
</thinking>

<function_calls>
<invoke name="Read">
<parameter name="path">/Users/wangchaoqun/novaic/novaic-backend/task_queue/utils/multimodal.py