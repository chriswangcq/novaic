# 强类型映射网络 (Schema Code Generation)

> 路径：引指 `novaic-common` schemas 与模型分发器

## 1. 异构服务的三重巴别塔
在没有使用单源 Schema 前。
你时常遇到 `Gateway` (用 Python 发了含有 `agent_id` 下划线风格) 的 JSON。
如果发给 `novaic-app` 用 TS；前端通常只能非常苦逼甚至写大量极多冗余的 TS 类型宣告如：
`type GatewayReturn = { agent_id: string }`
过上三天这变量名如果在后端改了。前端并不知情、编译时并无警报，只有你上了测试或正式环境，拿到 `undefined` 后程序抛红才发现！

## 2. 核心锚定化 (SOT - Source of Truth)
所以我们在项目体系加入了强大的共享基元生成方案：
在 `common` 里面存放的 `Pydantic` 是唯一的真实结构描述者（或者借助某些规范 JSON Schema 等）。
在我们启动 `deploy services` 或是相关预发包编译时！我们运行了内部编写好的工具脚本（比如借助诸如 `datamodel-code-generator` 或 `pydantic-to-typescript` 工具）。
瞬间帮前端生成出一个带随着版本发行的 `types_generated.ts` 文件。
前端的引入从强写死变成了：
`import { AgentResponseSchema } from 'novaic-common/types'`。
这彻底做到了只要服务器把 `id` 改为了 `UUID`：不仅后端的代码改了，这把变动连同类型的火焰能够以最快速度烧进另外的那些子库，直到它们修复前不允许过构建或者发包！跨语言契约神圣而不可干犯。
