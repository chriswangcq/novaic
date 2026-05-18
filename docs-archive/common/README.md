# Common 共享契约与配置域 拆页地图
> 路径：`docs/common/`

## 目录索引

| 专题 | 说明 |
|------|------|
| [schema-code-generation.md](schema-code-generation.md) | **降临全语言的基元**：详细描述 Pydantic Base -> Typescript Type -> Rust Struct 这种在单源数据驱动下让三种不同性格的编译器闭嘴听从教导的发源路线。 |
| [port-conflict-resolution.md](port-conflict-resolution.md) | **19996 惨案与服务字典编排**：当本机的 `VmControl` (占了 19996 用来让被控端回源连接) 撞上了为了发云上跑单干脆同端起测而在本地跑起来的 `Cortex` 的绝杀撞车冲突是怎么用 `SERVICES.json` 重定向摆平的。 |
