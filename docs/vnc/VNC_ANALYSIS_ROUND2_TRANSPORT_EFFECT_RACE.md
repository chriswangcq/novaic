# VNC 连接问题分析 — 第二轮：transport / effect / doConnect 竞态

## 1. 数据流概览

```
AgentDesktopView                    useVnc (VncCanvas)              vncBridge / 后端
─────────────────                  ─────────────────               ────────────────
useEffect [vncTargetKey]
  createVncTransport(target)
    → VncBridgeTransport.connect()
      → invoke('vnc_stream_connect')  ──────────────────────────────→ stream 610892fc
      ← streamId
    → setTransport(T1)
                                    transport 变化
                                    effect [transport, containerReady, ...]
                                      doConnect()
                                        prevTransport = lastTransportRef
                                        if (prevTransport && prevTransport !== t)
                                          prevTransport.close()  ────────────────→ vnc_stream_close
                                        lastTransportRef = t
                                        new RFB(container, t)
```

## 2. 竞态场景

### 2.1 场景 A：新 transport 覆盖旧 transport

1. createVncTransport 完成，`setTransport(T1)`
2. 渲染，useVnc 收到 T1，effect 跑 `doConnect(T1)`，RFB 建立，`lastTransportRef = T1`
3. 再次 createVncTransport 完成，`setTransport(T2)`
4. useVnc 收到 T2，effect 跑 `doConnect(T2)`
5. `prevTransport = lastTransportRef = T1`，`prevTransport !== T2`，执行 `T1.close()`
6. T1 的 stream 被关闭，对应 RFB 断开
7. 新建 RFB 使用 T2

**结果**：每次新 transport 都会关闭上一个，导致已建立的 VNC 被中断。

### 2.2 场景 B：createVncTransport 并发

1. effect 第一次跑，createVncTransport 开始（异步）
2. 在完成前，effect 再次跑（vncTargetKey 或 mount 变化）
3. 第二次 createVncTransport 开始
4. 两个 Promise 并发，先完成的调用 `setTransport(T1)`
5. 后完成的调用 `setTransport(T2)`，覆盖 T1
6. useVnc 只看到 T2，但 T1 的 stream 已创建且未被关闭

**结果**：产生多余 stream，且可能关闭错误的 transport。

### 2.3 场景 C：Strict Mode 双挂载

1. Mount 1：effect 跑，createVncTransport 开始
2. Unmount 1：cleanup，但 createVncTransport 的 Promise 仍在执行
3. Mount 2：effect 再跑，createVncTransport 再次开始
4. Promise1 完成 → setTransport(T1)（可能作用在已卸载实例上）
5. Promise2 完成 → setTransport(T2)
6. 若 requestId 校验通过，最终 transport 为 T2，T1 被丢弃

**结果**：T1 的 stream 成为孤儿，占用后端资源。

## 3. doConnect 中的「关旧开新」逻辑

```ts
// useVnc.ts doConnect
const prevTransport = lastTransportRef.current;
if (prevTransport && prevTransport !== t && typeof prevTransport !== 'string' && 'close' in prevTransport) {
  (prevTransport as VncBridgeTransport).close();
}
lastTransportRef.current = t;
// ... new RFB(container, t)
```

**设计意图**：transport 切换时关闭旧连接，避免泄漏。

**副作用**：只要 `transport` 引用变化（新实例），就会关旧开新。而每次 `createVncTransport` 都会返回新的 `VncBridgeTransport` 实例，所以每次新 transport 到来都会触发关闭上一个。

## 4. 根本矛盾

| 层级 | 行为 | 问题 |
|------|------|------|
| AgentDesktopView | 每次 effect 跑就 createVncTransport，得到新实例 | 无法复用已有 transport |
| useVnc | transport 变化就 doConnect，并关闭 prevTransport | 会主动断开已建立的连接 |
| 后端 | 每个 vnc_stream_connect 对应一个新 stream | 多个 stream 并行，但前端只用一个 |

**矛盾**：前端不断创建新 transport，useVnc 不断关旧开新，导致连接在握手完成前后被反复关闭。

## 5. 日志佐证

```
[Log] RFB connect 成功
[Log] createVncTransport 开始
[Log] vnc_stream_connect 成功 streamId=9936ba4a
[Log] doConnect 开始
[Log] close 调用 streamId=610892fc   ← 关闭的是已连接成功的 stream
[Log] RFB disconnect userInitiated=true
```

说明：第一次连接已成功，但新 transport 到来后，doConnect 关闭了正在使用的 transport。

## 6. 第二轮结论

1. **createVncTransport 每次返回新实例**，无法复用。
2. **doConnect 的「关旧开新」** 在 transport 频繁变化时会不断断开已建立的连接。
3. **需要**：要么减少 createVncTransport 调用，要么在 transport 语义相同时复用已有实例，避免无意义的关旧开新。
