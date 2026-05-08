# P005 Ticket - 审计测试 CI 部署守卫覆盖

## Problem Definition

审计当前测试、CI、部署脚本是否足以守住 FSM substrate + business DSL 的架构边界，尤其防止新代码未接入、旧逻辑回流、worker roster 漂移、部署脚本不启动新 worker。

## Proposed Solution

只读检查：

- `.github/workflows/lint.yml`
- `scripts/ci/*fsm*` / runtime worker supervision / deploy smoke / start config checks
- `scripts/start.sh`
- `deploy`
- `novaic-app/scripts/start-backends.sh`
- targeted tests 和必要 lint。

## Acceptance Criteria

- 说明 CI 是否覆盖 Runtime FSM/worker residue。
- 说明 start/deploy 是否启动新 worker roster。
- 说明是否有 roster/config SSOT gap。
- 给出已运行验证命令与结果。

## Verification Plan

- 读取 workflow 和 scripts。
- 运行 deploy/start/worker supervision lint。
- 运行 compile/bash syntax checks。
- 总结未覆盖风险。

## Risks

- 本地 lint 通过不等于真实远端部署成功；必须明确部署 smoke 的边界。

## Assumptions

- 本票只审计，不实际部署。
