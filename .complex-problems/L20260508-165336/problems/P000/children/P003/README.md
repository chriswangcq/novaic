# 扫描旧路径、兼容分支、残留词汇与 CI guard 覆盖

## Problem

审计 active code 是否存在旧路径、兼容分支、fallback/shadow/legacy residue、未接入新逻辑、或者 guard 未覆盖的风险。需要区分防回归测试中的旧词与活路径中的旧逻辑。

## Success Criteria

- 运行 targeted residue scans。
- 运行 architecture guard/lint/test 命令。
- 列出命中项，并分类为活路径问题、防回归测试文本、文档/账本历史。
- 判断当前 CI guard 是否足以防止新旧双路回流。
- 发现 gap 时给出后续工单。
