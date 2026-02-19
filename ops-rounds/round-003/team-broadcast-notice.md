# Round 003 群发通知（可直接发送）

各团队请注意：Round 003 现在开始执行，目标是**收口 Round 002 遗留项并达成 PASS**。

统一规则：
1. 单一事实源：`ops-rounds/round-003/`
2. 任务单在：`10-dispatch/`
3. 汇报截止：每天 18:00，写入 `20-reports/`
4. 无 evidence 不算完成（必须有命令、结果摘要、产物/文档路径）
5. 任一 P0 未关闭，整轮不能 PASS

请各团队立刻领取并执行：
- Platform：`ops-rounds/round-003/10-dispatch/team-platform.md`
- API：`ops-rounds/round-003/10-dispatch/team-api.md`
- Runtime：`ops-rounds/round-003/10-dispatch/team-runtime.md`
- Agent Runtime：`ops-rounds/round-003/10-dispatch/team-agent-runtime.md`
- Tools：`ops-rounds/round-003/10-dispatch/team-tools.md`
- Storage-A/B：`ops-rounds/round-003/10-dispatch/team-storage-ab.md`
- Desktop：`ops-rounds/round-003/10-dispatch/team-desktop.md`

本轮重点闭环项：
- Desktop：clean-machine 实测闭环
- Agent Runtime：跨进程/重启幂等闭环
- Platform：去 bridge + 5 组件 matrix 消费证据
- Storage-A/B：contract diff + CI 证据闭环

请 11:00 前回复是否有阻塞；18:00 前提交日报与证据。
