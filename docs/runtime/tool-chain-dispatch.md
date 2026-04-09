# 工具链解体与新分发路由机制

> 路径：`novaic-agent-runtime/task_queue/handlers/` 分类分发器

## 1. 过去的遗老：被抛弃的 Tools Server
曾经，这里专门有着巨大的独立 Flask / FastApi 服务叫做 `novaic-tools-server`，AI 如果想要执行工具代码会发向一个臃肿不堪且充满所有乱七八糟依赖的接口。
然而这就引起了“神明也要拿筷子”的谬误：
既然我们可以让更贴近业务的层自己去消化任务，为什么要独立个服务呢？它被正式拆解下放。

## 2. Cortex 承继与知识动作代理
凡是带有文件系统增删改查（如 `touch_file`, `exec_node_script`）或涉及工作空间内部沙盒（Sandbox）的指令：
Saga 不会再自己亲自跑到有漏洞的主机上运行！！它是以 Payload 的形式发起 HTTP 指令，要求在那个端口 `19996` 上的神树中心（Cortex）代跑！Cortex 内带有完美的隔离机制、路径权限防御（禁止跨出工作区），并在安全结束后把包含标准输出 `STDOUT/STDERR` 的值返回给 Runtime 的 Handler。

## 3. VM 设备动作反打派系
如果是对宿主干预指令（例如：截个用户机器此时运行的手机里的游戏图片）。
Handler 直接走一条下发请求经由 `/internal` 找回老家 Gateway。利用 Gateway 所搭建的 `VmControl CloudBridge` 的能力，透传出这个截屏要求！

这种将动作流经 `Cortex` (静读知识系) 和 `Gateway` (硬件互动系) ，彻底粉碎并且分布化了我们的动作大循环。让每个模块在专有的安保层级里运作。
