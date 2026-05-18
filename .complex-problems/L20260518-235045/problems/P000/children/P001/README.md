# 归档旧文档并清理文档目录

## Problem

将现有 docs/ 目录完整归档到 docs-archive/，为新文档腾出干净空间。需要同时处理 CI guard 脚本的路径依赖，确保归档操作不破坏 CI。

## Success Criteria

- docs/ 下全部旧文件移到 docs-archive/（保留 git 历史可追溯）
- 新 docs/ 目录为空或只有占位 README
- CI guard 脚本路径依赖梳理清楚，必要时临时适配
- git status 干净，变更可解释
