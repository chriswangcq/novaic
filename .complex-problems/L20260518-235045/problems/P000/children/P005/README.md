# CI guard 适配与最终验证

## Problem

新文档结构下，CI guard 脚本（lint_docs_status_consistency.py、lint_current_docs_residue.sh、lint_deploy_fresh_smoke.py、check_start_config_contract.py）可能因路径变化而失败。需要适配脚本或文档结构，确保所有 guard 通过。同时做最终的文档-代码一致性交叉验证。

## Success Criteria

- 所有 docs 相关 CI guard 脚本通过
- 脚本适配最小化（优先调整文档结构满足 guard，其次调整 guard 脚本）
- 新文档与代码的引用交叉验证通过
- git diff --stat 变更范围合理
- docs-archive/ 确认完整
