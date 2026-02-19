# Week 1 Work Report - Desktop Team

## Team
Desktop Team

## Date
2026-02-19

## Mission Alignment
本周围绕 Desktop Team 工单目标推进了桌面端启动稳定性与可观测性基线，重点落在三件事：
- 降低独立构建/独立运行时对父目录结构的强耦合
- 提升进程编排启动阶段的可诊断性（尤其是冷启动失败）
- 补齐端侧日志落盘，保证失败时可快速定位根因

## Completed Work

### 1) Startup Diagnostics Baseline (D4)
- 在 `novaic-app/src-tauri/src/main.rs` 增加结构化启动诊断事件（JSONL）：
  - 新增 `StartupDiagnosticEvent`
  - 新增 `append_startup_diagnostic(...)`
- 诊断日志写入应用数据目录：
  - `logs/startup-diagnostics.jsonl`
- 当前覆盖的关键阶段包括：
  - `app-bootstrap`
  - `cleanup`
  - `port-preflight`
  - `runtime-orchestrator` 启动/失败
  - `runtime-orchestrator-health` 超时
  - `gateway` 启动/失败
  - `gateway-health` 超时
  - `vmcontrol` 启动/失败

### 2) Process Orchestration Preflight (D4)
- 在主启动流程加入端口预检：
  - 新增 `ensure_ports_available(...)`
  - 启动前校验 `19993~19999` 的关键服务端口可用性
- 若端口冲突，启动流程会中止并记录可操作错误信息：
  - 明确指出冲突的服务名 + 端口
  - 指导先停止冲突进程后重试

### 3) Reduce Parent-Directory Assumptions for VmControl (D2)
- 改造 vmcontrol 二进制定位逻辑：
  - 新增 `resolve_vmcontrol_binary_path(...)`
  - 支持 `NOVAIC_VMCONTROL_BIN` 环境变量覆盖
  - 支持 bundle 资源路径
  - 支持开发态 `src-tauri/vmcontrol/target/{debug,release}`
- 减少“必须依赖固定父目录结构”才能启动的风险

### 4) Endpoint Observability for VmControl (D4)
- 将 vmcontrol 进程日志改为落盘，便于端侧排障：
  - `logs/vmcontrol.log`
- 相比原先丢弃 stdout/stderr，可在用户机器直接回溯 vmcontrol 启动与运行问题

## Tests and Verification
- 本地构建校验：
  - `cargo check --manifest-path novaic-app/src-tauri/Cargo.toml` -> passed
- IDE lints 校验：
  - 修改文件未引入新增 linter error

## Impact Assessment
- **启动可靠性**：端口预检提前失败，避免“半启动”或静默失败
- **排障效率**：启动过程与 vmcontrol 都有落盘日志，失败原因可追踪
- **独立化能力**：vmcontrol 路径解析不再依赖单一路径假设，提升独立构建/运行兼容性

## Risks / Gaps
- 本轮尚未完成 `rc` 安装包产物构建与冷机全链路验收（D5）
- 启动诊断已覆盖关键路径，但仍可继续补充 Queue/Tools/File Service 的细粒度状态事件

## Next Steps
- 产出 Desktop 冷启动 smoke 脚本，自动校验：
  - 关键端口预检行为
  - `startup-diagnostics.jsonl` 事件完整性
  - `vmcontrol.log` 生成与内容
- 对接 CI 增加桌面端启动 smoke job
- 推进 `rc` 安装包构建与 clean-machine 启动验收报告
