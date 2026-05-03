# Entangled Action Hook 当前架构

> 历史 gap 已关闭。当前实现不再是 “Entangled 回调 Gateway hook”；action hook 统一由 Business 处理。

## 当前链路

```text
App
  → Entangled WS action
  → Business action callback
  → Business handler
  → Entangled writes / Environment notifications / Device orchestration
```

## 当前所有权

| 能力 | Owner |
|---|---|
| schema/action contract | Business/Common schema push |
| action callback handler | Business `main_business.py` dispatcher |
| entity storage/sync | Entangled |
| endpoint discovery | Gateway App WS |
| UI subscription/cache | App Entangled Rust client |

## 禁止回退

- 不要把 action hook 重新挂回 Gateway。
- 不要在 Gateway 里恢复产品 entity store 或 action hook。
- 不要让 App WS 承载 Entangled schema/entity sync。

历史迁移细节保留在 roadmap tickets 和 git history；当前架构文档只描述现行主路径。
