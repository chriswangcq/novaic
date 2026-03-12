# NovAIC VNC 统一优化 — 协作文档空间

> 本目录集中存放 Device / AppInstance / VNC 统一优化相关的设计文档与任务清单，便于团队协作。

---

## 文档索引

| 文档 | 说明 |
|------|------|
| [01-current-state.md](./01-current-state.md) | 现状与调研（系统架构、Device、AppInstance、VNC、Gaps） |
| [02-expert-design.md](./02-expert-design.md) | 专家统一优化方案（设计思路、改造顺序、关键决策） |
| [03-maindesk-vs-subuser.md](./03-maindesk-vs-subuser.md) | Maindesk vs Subuser VNC 差异分析（参考） |
| [04-task-breakdown.md](./04-task-breakdown.md) | **任务清单**（按 Phase 拆分的可执行任务） |
| [05-my-devices-api.md](./05-my-devices-api.md) | My Devices API |
| [06-phase2-multi-pc-design.md](./06-phase2-multi-pc-design.md) | Phase 2 多 PC 设计 |
| [07-phase2-subagent-review-summary.md](./07-phase2-subagent-review-summary.md) | Phase 2 Subagent 审核 |
| [08-phase3-subagent-review-summary.md](./08-phase3-subagent-review-summary.md) | Phase 3 Subagent 审核 |
| [09-phase4-design-code-verification.md](./09-phase4-design-code-verification.md) | Phase 4 设计文档与代码对照检查 |
| [10-phase4-vnc-10-agent-review-summary.md](./10-phase4-vnc-10-agent-review-summary.md) | Phase 4 10 Subagent 审核汇总 |
| [11-phase4-vnc-stability-10-subagent-master-report.md](./11-phase4-vnc-stability-10-subagent-master-report.md) | **Phase 4 VNC 稳定性 10 Subagent 综合研究** |

---

## 改造顺序

```
Phase 1 (Device 模型) ─┬─→ Phase 2 (AppInstance / 拓扑)
                       └─→ Phase 3 (VNC 后端)
                                  └─→ Phase 4 (前端收敛)
```

**整体周期**：约 4–6 周

---

## 快速入口

- **了解现状**：先读 [01-current-state.md](./01-current-state.md)
- **理解方案**：再读 [02-expert-design.md](./02-expert-design.md)
- **执行任务**：按 [04-task-breakdown.md](./04-task-breakdown.md) 逐项推进
