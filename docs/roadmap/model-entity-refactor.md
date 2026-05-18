# 实体模型重构

## 状态

Status: Closed

## 概述

实体模型统一了 Business 层的 Entity Schema 定义，通过 Action Hooks 机制支持 CRUD 和自定义操作。重构已完成。

## 当前架构

Business 服务管理 19 个 Entity Schema，每个实体通过 Entangled 同步协议实时同步到客户端。实体操作通过 Action Hooks 触发副作用（如消息发送触发 Agent 执行）。

详见 [Business 服务架构](../services/business.md) 和 [Entangled 同步协议](../architecture/entangled-sync-protocol.md)。
