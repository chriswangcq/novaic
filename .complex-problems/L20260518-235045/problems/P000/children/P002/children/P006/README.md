# 后端核心服务代码调研

## Problem

调研后端核心服务的代码结构：novaic-agent-runtime（含 Queue Service）、novaic-cortex、novaic-business。这三个是 agent 执行链路的核心。

## Success Criteria

- agent-runtime：入口文件、worker 类型、saga/task 处理流程、queue_service 目录结构、API 路由
- cortex：入口文件、API 路由全表、核心模块划分（scope/context/shell/sandbox/payload）
- business：入口文件、API 路由、action hook 机制、与 Entangled/Device/Queue 的集成点
- 每个服务的进程角色和启动方式
- 服务间调用关系（谁调谁、用什么协议）
