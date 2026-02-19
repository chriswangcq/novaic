# Round 004 群发通知（可直接发送）

各团队注意：Round 004 现在开始，目标是**收口 Round 003 的剩余 gap 并达成 PASS**。

统一规则：
1. 单一事实源：`ops-rounds/round-004/`
2. 任务单：`10-dispatch/`
3. 每天 11:00 阻塞同步，18:00 前提交报告到 `20-reports/`
4. 无 evidence 不算完成（命令、结果摘要、产物/文档路径必须齐全）
5. 报告中必须包含 **Decision Needed** 段落（有困难/风险时必填）

请各团队立即执行：
- Platform：`ops-rounds/round-004/10-dispatch/team-platform.md`
- API：`ops-rounds/round-004/10-dispatch/team-api.md`
- Runtime：`ops-rounds/round-004/10-dispatch/team-runtime.md`
- Agent Runtime：`ops-rounds/round-004/10-dispatch/team-agent-runtime.md`
- Tools：`ops-rounds/round-004/10-dispatch/team-tools.md`
- Storage-A/B：`ops-rounds/round-004/10-dispatch/team-storage-ab.md`
- Desktop：`ops-rounds/round-004/10-dispatch/team-desktop.md`

本轮关键闭环项：
- Desktop：fresh clean-machine 证据补齐
- Storage-A/B + Platform + API：storage contract schema 入 `contracts/` 并完成 executable diff
- Platform：5+ 组件 matrix 消费证据

请在 report 中主动反馈困难和问题，按以下格式给决策输入：
- Decision Needed:
  - issue:
  - options:
  - recommendation:
  - impact:
