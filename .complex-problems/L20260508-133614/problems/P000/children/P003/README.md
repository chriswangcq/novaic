# P003: Cortex registry 显式依赖边界收口

## Problem
Cortex registry 显式依赖边界收口

## Success Criteria
- WorkspaceRegistry 构造器不再隐式 from_env/time.time；startup boundary 显式注入 policy/clock
- 新增/更新测试证明缺失依赖 fail-fast 或显式传入
