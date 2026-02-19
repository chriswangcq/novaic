# Team Mechanism Announcement Prompt

请从本轮开始执行新的 **Round 文件驱动机制**。所有任务分配、汇报、审阅、再分配，统一以仓库内文件为准，不再以口头同步视为完成。

你们需要遵循以下规则：

1. 单一事实源  
   - 本轮目录：`ops-rounds/round-002/`
   - 任务单：`10-dispatch/`
   - 汇报：`20-reports/`
   - 审阅结论：`30-review/reviewer-findings.md`
   - 再分配：`40-redispatch/`

2. 状态码统一  
   - 仅允许：`PLANNED`、`IN_PROGRESS`、`BLOCKED`、`DONE`、`DONE_WITH_GAPS`、`REJECTED`
   - 定义见：`ops-rounds/governance/status-codes.md`

3. 证据强制  
   - 每条完成项必须附 evidence：测试命令、产物路径、文档路径
   - 无 evidence 的完成项会被判定为未完成

4. Gate 机制  
   - 本轮 Gate 定义见：`ops-rounds/round-002/00-control/gate-criteria.md`
   - 有未关闭 P0 则本轮直接 FAIL

5. 节奏  
   - 每天 11:00 同步阻塞
   - 每天 18:00 前更新各自 report 文件

请各团队立刻打开并执行自己的派单文件：
- Platform: `ops-rounds/round-002/10-dispatch/team-platform.md`
- API: `ops-rounds/round-002/10-dispatch/team-api.md`
- Runtime: `ops-rounds/round-002/10-dispatch/team-runtime.md`
- Agent Runtime: `ops-rounds/round-002/10-dispatch/team-agent-runtime.md`
- Tools: `ops-rounds/round-002/10-dispatch/team-tools.md`
- Storage-A/B: `ops-rounds/round-002/10-dispatch/team-storage-ab.md`
- Desktop: `ops-rounds/round-002/10-dispatch/team-desktop.md`
