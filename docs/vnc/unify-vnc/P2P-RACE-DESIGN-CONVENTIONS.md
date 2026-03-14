# P2P 竞态修复设计约定（3 轮设计-Review 循环）

## 设计范围

| ID | 问题 | 涉及模块 |
|----|------|----------|
| R1/R5 | 推送无 ACK、无重试 | Gateway (p2p.py, pc_client.py)、CloudBridge |
| R2/R3 | 手机立即 connect vs PC 建连耗时、Relay 10s 不足 | relay.rs (手机)、novaic-quic-service |
| R4 | PC 重试无 session 刷新 | cloud_bridge.rs |
| E2 | RFB 不暴露 close reason | 前端 VNC 层、noVNC |

## 输出规范

每轮设计需包含：
1. **问题陈述**：简要复述
2. **方案设计**：具体改动（文件、代码位置、伪代码）
3. **接口变更**：新增/修改的 API、消息格式
4. **风险与回退**：兼容性、回退策略
5. **实施顺序**：依赖关系、建议步骤

## 3 轮循环

- **Round 1**：初版设计 → Review 报告（指出缺口、冲突、建议）
- **Round 2**：基于 Review 再设计 → 再 Review
- **Round 3**：最终设计 → 最终 Review → 产出实施计划
