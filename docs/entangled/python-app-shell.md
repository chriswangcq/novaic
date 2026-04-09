# 独立服务外壳 App Shell

> 路径参考：`Entangled/packages/server-python/entangled/app/`

## 1. Entangled-Service 的遗债消除
过去的 NovAIC 根目录下存在一个巨大的独立库项目 `entangled-service`。由于我们想要把通用实时库的职责分离，旧代码既有自身的 `main` 和网络组件，同时又依赖 NovAIC 领域概念。因此，在终极重构中，独立的库已被彻底从世界删除。

## 2. 独立应用厂 (`factory.py`)
取而代之的是，在 Entangled 自己名下诞生了一个免开发启动应用的方法：`entangled.app`。
- 如果某个外部工程希望简单地用上带有这个实时同步架构的“黑盒”服务器，只需给一个 Entity 注册的 List 调用 `factory.create_app` 即可生成一份 FastAPI 跑例。
- 所有的 `main` 就是把本地的一套 `SqlEntityStore` 拼起来而已。完全实现了和业务逻辑框架无耦合。

## 3. JWT 集成与挂载路由 (`auth.py` / `ws.py`)
被剥离的这套轻量服务自带全系端点（Endpoints）：
- **Auth 验证**：它暴露 `/auth/login` 等签发独立 JWT 而非依赖重型的 `api.gradievo.com`。
- **全系 REST APIs**：在 `crud.py` 里直接为你用元编程路由暴露增删改查。
- **主 WebSocket 打通**：提供 `/api/ws` 可以用标准版的 React/Rust Client 直连。
- 目前对于 NovAIC 产品全量架构，这种启动方式主要是供**外部轻量级参考或是独立 SDK 开发**使用的。NovAIC 在云端其实是用 `novaic-gateway` 以子模块**内部寄生使用**的形式去运转核心 Entangled 同步能力（参阅 gateway-integration 特集）。
