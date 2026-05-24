# MCP 标准契约与工具伪装

> 路径参考：`novaic-mcp-vmuse/` 中的 schema 定义层落点设计

## 1. 原生的工具调用死胡同
在各家模型闭源或者各说一套词之前（过去你往往得为 OpenAI 定制一版 function calling、然后为 Claude 搞另外一套完全迥异的 xml 参数对齐格式）。
如果由我们在 Gateway 甚至是由 Worker 那帮干粗活的代码自己去写：“Hey Claude，这里给你个功能是获取截图”，它的工作量会呈几何增长直到压垮适配工程师。

## 2. 迎入 MCP (Model Context Protocol) 框架
VMuse 之所以被取名为 MCP 附带后缀。全是因为我们在这层直接拉入并拥抱了极其优雅标准的开源下发协议！
这个仓库本身其实是一座将“执行代码”装模作样地包装成一份有着极为清晰：
```json
{
  "name": "take_screenshot_and_analyze",
  "description": "Snap a current view from device :id",
  "inputSchema": { "type": "object", "properties": {"device_id":...} }
}
```
的字典菜单大本营！

## 3. 历史形态：在 Agent Runtime 里直接联运
早期设计里，VMuse 可以像一块 MCP 插板一样被 Runtime 直接引入：在 `sagas`
节点走到思考（Think）时，把 VMuse 暴露的工具清单交给 LLM，模型选择工具后由
Runtime 下沉执行，再把图片或者成功信号包装成标准回复。

这段设计只描述历史形态。它不再是当前推荐的实时媒体边界，因为直接把截图、
文件字节或 MCP image content 放进 LLM 工具历史，很容易重新引入大块 base64 文本、
上下文膨胀和投影语义混乱。

## 4. 当前形态：shell / Blob / display 分层
当前 live path 应遵循更窄的边界：

- VMuse / Device 负责底层捕获与动作执行。
- Cortex shell capability 负责把设备返回的截图或文件字节转成 Blob artifact。
- shell stdout 只返回终端文本和 `tool-output.v1` manifest，例如
  `blob://runtime-artifact/...`，不把 raw base64/media bytes 写进历史文本。
- Runtime / Cortex 历史回放保持 manifest-only，不展开旧图片。
- 只有 agent 显式调用 `display` 查看某个 Blob artifact 时，当前轮才把图片作为
  provider-native image content 投影给模型。

因此，VMuse 仍然可以保留 MCP/HTTP 形式的底层能力，但 Runtime 不应再把 VMuse
媒体工具当成直接给 LLM 的主入口。LLM 面向的是 shell 文本契约和显式 `display`
感知契约，媒体字节由 Blob 承载。
