# Phase 1 任务分工（4 名工程师）

> 参考 `docs/DESIGN-P2P-UNIFIED.md`、`docs/P2P_REFACTOR_PROPOSAL_A.md`

---

## 工程师 1：config.rs

**产出**：`novaic-app/src-tauri/p2p/src/config.rs`

**内容**：
1. `resolve_p2p_port() -> u16`：读取 `NOVAIC_P2P_PORT`，默认 19998
2. `P2pServerConfig`：port, stun_server, heartbeat_interval_secs, stun_retry_interval_secs，`Default` 实现
3. `ConnectStrategy`：enum { DirectOnly, DirectThenRelay, RelayOnly }
4. `P2pClientConfig`：connect_strategy, punch_timeout_secs, relay_url，`Default` 实现

**依赖**：无

**p2p/src/lib.rs**：新增 `pub mod config;`，`pub use config::*;`

---

## 工程师 2：server.rs

**产出**：`novaic-app/src-tauri/p2p/src/server.rs`

**内容**：
1. `P2pServerCloudConfig`：gateway_url, cloud_token, device_id（p2p 定义，vmcontrol 构造传入）
2. `P2pServer`：new(config, data_dir)
3. `P2pServer::start(cloud_config, vmcontrol_http_port) -> Result<(LocalVmControlInfo, oneshot::Sender<()>)>`
   - 流程：load identity → STUN → QUIC bind → heartbeat loop（若有 cloud_config）→ accept loop
   - 返回 LocalVmControlInfo：device_id, cert_der, **port**（新增）
4. `LocalVmControlInfo` 若在 vnc_proxy 定义，则 server 返回等价结构；或迁移到 p2p::types

**依赖**：config（工程师 1）、现有 rendezvous/hole_punch/tunnel/device_id/crypto

**注意**：CloudBridgeConfig 在 vmcontrol，p2p 不依赖 vmcontrol。用 P2pServerCloudConfig 解耦。

---

## 工程师 3：client.rs

**产出**：`novaic-app/src-tauri/p2p/src/client.rs`

**内容**：
1. `P2pClient`：new(config)
2. `P2pClient::connect(gateway_url, jwt, target_device_id) -> Result<Connection>`
   - 内部：rendezvous::locate → 校验 ext_addr、cert → hole_punch::connect_to_peer
   - 当前仅实现 ConnectStrategy::DirectOnly
3. `P2pClient::connect_direct(addr, device_id, cert_der) -> Result<Connection>`
   - 转发到 hole_punch::connect_to_peer（供 vnc_proxy 本地连接用）

**依赖**：config（工程师 1）、rendezvous、hole_punch

---

## 工程师 4：集成

**产出**：修改 vmcontrol、vnc_proxy、lib.rs、setup

**内容**：
1. **vmcontrol/lib.rs**：
   - 移除 setup_p2p_server，改用 P2pServer
   - 构造 P2pServerConfig（port 用 resolve_p2p_port()）
   - 构造 P2pServerCloudConfig 从 cloud_config
   - 调用 p2p_server.start()，获得 local_info
   - 将 local_info 写入 SharedLocalVmControl（需 lib.rs 支持，当前在 VmControl 启动后写入）
   - graceful shutdown 时发送 p2p_shutdown

2. **vnc_proxy**：
   - HandlerState 新增 p2p_client: Arc<P2pClient>
   - get_or_create_local_conn：用 local_info.port 替代 LOCAL_P2P_PORT，调用 p2p_client.connect_direct()
   - get_or_create_remote_conn：调用 p2p_client.connect(gateway_url, token, device_id)
   - 移除对 p2p::hole_punch 的直接 use

3. **lib.rs / setup**：
   - 构造 P2pClientConfig、P2pClient，注入 VncProxy
   - LocalVmControlInfo 需包含 port，以便 vnc_proxy 使用

**依赖**：工程师 1、2、3 完成

---

## 执行顺序

1. **工程师 1** 先完成（无依赖）
2. **工程师 2、3** 可并行（依赖 1）
3. **工程师 4** 最后（依赖 2、3）
