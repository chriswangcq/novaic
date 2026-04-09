# 内网穿透中转桥：CloudBridge WS 与 Vm 管理

> 路径参考：`novaic-gateway/gateway/vm/manager.py` 和 `gateway/api/routes.py` 等。

## 1. 为什么需要 CloudBridge？
在一个“桌面端内嵌重重环境与虚拟机”（如我们的 Tauri UI 需要跑 QEMU 的 Linux，或是接远端手机屏幕）并在“云端拥有高管大脑（Gateway、Agent）”的网络拓扑里：
云端那台网关没法主动往内网用户电脑里面发起请求：“喂，把你本地开的那个 Chrome 里的截图用 VNC 发我一下”。必须依靠一条由内打向外、且永远长连的隧道。

这套长连接被定义在路口：`/internal/pc/ws`。
- Tauri 端本地启动的一个专属二进制包称为 **`VmControl`**，它一跑起来就会建立对云网关这条 Web Socket 直连。
- 它在网关这边通过一个称为 `pc_client_manager` 的组件进行保持与生命期维持。它充当着云打着反向代理。

## 2. CloudBridge 承载的内容
由于内网控制权由本地 `VmControl` 把持，它反手把自己所有的能耐注册给了这条管道的事件流：
- **上报虚拟机列表 (Agent List Sync)**：本地扫到了哪些虚拟机、配置及当前是否活着的进程状态，自动由网桥上抛告诉网关去更新（网关会在 `manager.py` 借以管理和修复重启列表）。
- **执行指令 (Downstream Execute)**：当我们在云端发出的某些操作需要打碎重配虚拟机资源、或是获取某个本地 Vnc URL 资源。
例如在 `api/vm.py` 里检查能否下载重置云镜像之类：网关是不碰真实的硬盘与资源的；全部请求只是封装成 JSON 从这边被塞进去打到了 `VmControl` 执行后抛结果上来。

## 3. Strict 模式下的硬隔离
进入 Phase 3 的部署，云端彻底被改作：云不产生执行态！
云端在关于 VM 的一切操作，如果没有收到来自 `vmcontrol` 的确认或在系统初始化里发生 `health()` 健康度脱节：将强行抛出拒绝接纳请求。即完全通过 `manager.py` (The Single VM Source-of-Truth) 限定边界。
