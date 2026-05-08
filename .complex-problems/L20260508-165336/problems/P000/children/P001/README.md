# 证明当前 runtime 是否实际走新 FSM/worker/roster 路径

## Problem

审计当前代码是否真的走新 FSM substrate、worker registry、runtime roster、generic worker/effect path，而不是只新增了未接入代码。需要从入口、注册、启动、deploy、测试和 CI guard 多个角度证明 live path。

## Success Criteria

- 找到 main entry / registry / start.sh / deploy 如何接入 runtime roster。
- 找到 session/task/saga ledger 如何接入通用 FSM runner。
- 找到 worker command registry 如何接入 WorkerSpec 和 process runner。
- 证明旧 direct/manual path 未继续作为生产启动路径。
- 输出证据清单和 remaining risk。
