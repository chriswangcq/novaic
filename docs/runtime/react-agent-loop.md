# ReAct 与主脑逻辑环：Agent Loop

> 路径参考：`novaic-agent-runtime/task_queue/handlers/llm_handlers.py` 及相关思维解析逻辑

## 1. 对 LLM 的极致伪装与欺骗
现代大型模型常常带有一套过于死板或者并不适应于我们超级框架的自我防卫体系，如果任由模型主观推理它的能力边界，将会发生大量拒绝调用或者死锁。
我们在 `react_think` （常于 handlers 或 prompt 组合工厂中寻觅）里面构建了坚实的护城河：
- 注入高度强制化的 `System Prompt`：“You are NovAIC instance... You MUST use \<think> blocks...”。
- 抹除原生的 Tool Chain：大模型原生的 `function_call` 一直很愚蠢且费 Token。我们将 Cortex 里能用的系统技能以 JSON Array 的形式强制打在 System 末尾，要求模型不要原生去 call，甚至是通过纯 `<thought>` 推演最后输出指定结构。

## 2. `<think>` 提取与剥离管线 (Streaming 降级)
考虑到我们在 `novaic-llm-factory` 里接入的有 DeepSeek、Kimi 或者 Claude 这种并不同源的模型：
当我们取回了带着厚重 XML / HTML 包裹或是原始 `<think>推理文字</think> 真正回答` 的全文本之后：
真正的 Regex / String 剥离器会在后方阻截工作，将结果分成 `reasoning_content` 和真正的 `text` 并且分开更新进后端的数据库里（这也是为何在客户端你不仅能看到对话框、如果点进展板里你还能拉出 `思维草稿箱` 的缘故，它们分属两条不同渠道保存并由 Runtime 解耦）。

## 3. 当遇到死胡同时
死循环（LLM 一次次调用同一个工具获得同一样无用的 `Result: NotFound`）在自动智能体领域是灭顶之灾：
Runtime 中设定了 `stuck` 超时和 `Max Iteration = N` 安全锁。如果在这层逻辑中一趟 Saga 发生同一工具超频的调用或步数过多极耗积分的异常走秀。Saga 立即斩断循环抛出警报截返：“AI 陷入深思过度并停止服务”。
