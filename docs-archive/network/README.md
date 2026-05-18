# 网络设施与穿透调度 (Network Pipeline) 拆页地图
> 路径：`docs/network/`

由于网络层是一个极其下沉的重资产黑盒环境。这里不再涉及细致入微的每行打洞实现（这属于底端协议层的库维护），主要解释我们的整个架构怎么串起以及借用了哪些协议与外部组合完成链路。
配搭 [docs/network-architecture.md](../network-architecture.md) 看。

## 目录索引

| 专题 | 说明 |
|------|------|
| [stun-and-turn-lifecycle.md](stun-and-turn-lifecycle.md) | **TURN/STUN 的流转生命**：我们的 WebRTC 怎么拿到外部票根并找人，解析长会话的那个清理僵尸进程的策略。 |
| [quic-relay-routing.md](quic-relay-routing.md) | **QUIC 终极托底与下发 CDN**：详细介绍遇到穿透失败为什么切 QUIC，以及顺手做成 Web 发布版本塔的设计缘由。 |
