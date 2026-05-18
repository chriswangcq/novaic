# 边缘与基础设施服务代码调研

## Problem

调研边缘和基础设施服务：novaic-gateway、Entangled（在 novaic-common 或独立）、novaic-device、novaic-llm-factory、novaic-blob-service（如存在独立目录）、novaic-sandbox-service、novaic-logicalfs、novaic-common。

## Success Criteria

- gateway：Rust 代码结构、路由、auth 机制、WebSocket 处理
- device：入口文件、API 路由、CloudBridge/VmControl 集成
- llm-factory：入口文件、API 路由、provider 路由机制
- sandbox-service：入口文件、API 路由、进程执行机制
- logicalfs：模块结构、与 Cortex 的集成方式
- common：共享包结构、config、client、工具定义
- 每个服务的端口和启动方式
