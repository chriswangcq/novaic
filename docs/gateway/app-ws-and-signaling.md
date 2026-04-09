# 业务数据生命线与信令混载：AppBridge WS

> 路径参考：`novaic-gateway/gateway/api/app_client.py`

## 1. 从 SSE 到纯纯的 Websockets
前端在早期拥有无数繁杂的分发接口——通过 HTTP 来收信、通过 SSE 去监听消息变化。经过整合后，所有前端的变现数据刷新与推送完全抛弃了被动的 Server-Sent-Events。
唯一的出口归结于针对 `/api/app/ws` 发起的主 Websockets。

## 2. Request / Response 的无痛化封装
当你以为这是和普通的 SSE 一样只负责后台给你“喂食”状态的话，你就大错特错了。
AppBridge 是一套自己封装了带业务号回应体系的操作。我们向网关 WebSocket 可以完全发起任何带 `request_id` 的调用甚至直接要求服务器停摆某个 agent (`interrupt` 事件)：
```json
// 一条由前打向后的业务停摆要求请求：
{"type":"request", "request_id":"uuid-A12", "action":"chat_send/interrupt", "data":{...}}
```
网关不需要再去启动臃肿的 HTTP 处理端，直接在内旋路由上寻找匹配并就地进行数据库插入或其他处理，由于 `Entangled` 就运行在它自己的同源代码中：
返回给前端的时候甚至顺便打包了 Entangled 的 Schema 数据包推送。

## 3. WebRTC 信令混载 (Signaling Mulitplex)
一个特别逆天的用法发生在 WebRTC 端内视频通讯打洞。
WebRTC 在找目标 P2P 地址之前要求交换一个叫做 `offer / answer / candidate` ICE 数据的小碎包。如果你通过普通的 POST 方法提交并且拉回，这种延迟常常会产生乱序。
在这条早已贯穿前后端的 AppBridge 之上。这三类数据被视为**带外的指令操作包**混在大通道一起流过。
这保证了绝对的发送接收顺序队列，保证了桌面端的连接瞬间打通并且永远跟所有的更新事件属于同一队列，没有了资源抢占问题并获得了完美的端管互联体验。
