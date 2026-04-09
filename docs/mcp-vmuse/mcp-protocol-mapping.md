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

## 3. 在 Agent Runtime 的联运
这意味着这其实成了被系统里的 Runtime 无需关心里面到底执行什么就能直接引入即用的插板！
在 `sagas` 节点走到思考（Think）时，我们的组装大器只需要把这个库给它预定义的清单像扔进信箱一样倒给 LLM。模型拿到自己也看得懂的规范清单并说：“去使用某某指令吧”；指令流经 Runtime 下沉到此地，这里完成真实调用并且把图片或者成功信号套个标准的回复大皮塞回去，完全做到了核心执行器库与大脑调用语法的相互隔离保活。
