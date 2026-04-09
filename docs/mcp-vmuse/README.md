# MCP & VMuse 大规模操作端 拆页地图
> 路径：`docs/mcp-vmuse/`

大模型的智力再怎么聪明，没有能够操控屏幕和鼠标的手脚也只能干瞪眼。配搭 [docs/mcp-vmuse-architecture.md](../mcp-vmuse-architecture.md) 食用以发掘 NovAIC 中最具科幻感的一面。

## 目录索引

| 专题 | 说明 |
|------|------|
| [mcp-protocol-mapping.md](mcp-protocol-mapping.md) | **标准协议整合**：把极其复杂的动作怎样强行封装适应 MCP 规范，并骗 LLM 乖乖通过标准函数向外吐出参数。 |
| [browser-vision-automation.md](browser-vision-automation.md) | **降维网页视觉控制**：给网页加盖隐形标记网格！为什么不能把全屏扔过去？我们如何通过抽取特殊 DOM 属性让大黑盒算准鼠标应该点击坐标（x,y）在哪儿？ |
| [qemu-qmp-interaction.md](qemu-qmp-interaction.md) | **直插云端宿主底层的 QMP**：给 Linux 或者安卓发送重启电源信号或者拿到物理层断电状态的控制线底层原理。 |
