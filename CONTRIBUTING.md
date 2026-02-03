# Contributing to NovAIC

感谢你对 NovAIC 的关注！欢迎各种形式的贡献。

## 开发环境

请参阅 [DEVELOPMENT.md](DEVELOPMENT.md) 了解如何搭建本地开发环境。

## 贡献流程

### 1. Fork 项目

点击 GitHub 页面右上角的 Fork 按钮。

### 2. Clone 你的 Fork

```bash
git clone https://github.com/<your-username>/nb-cc.git
cd nb-cc
```

### 3. 创建分支

```bash
git checkout -b feature/your-feature-name
```

分支命名规范：
- `feature/xxx` - 新功能
- `fix/xxx` - Bug 修复
- `docs/xxx` - 文档更新
- `refactor/xxx` - 代码重构

### 4. 开发与测试

```bash
# novaic-core
cd novaic-core
pip install -e ".[dev]"
pytest

# novaic-app
cd novaic-app
npm install
npm run build
npm run lint
```

### 5. 提交代码

```bash
git add .
git commit -m "feat: add xxx feature"
```

提交信息规范：
- `feat: xxx` - 新功能
- `fix: xxx` - Bug 修复
- `docs: xxx` - 文档更新
- `refactor: xxx` - 重构
- `test: xxx` - 测试相关
- `chore: xxx` - 构建/工具相关

### 6. 推送并创建 PR

```bash
git push origin feature/your-feature-name
```

然后在 GitHub 上创建 Pull Request。

## Pull Request 指南

- 保持 PR 小而集中，一个 PR 只做一件事
- 确保所有 CI 检查通过
- 更新相关文档
- 如果涉及 UI 变更，请附上截图

## 代码检查

提交前请确保以下检查通过：

```bash
# Python (novaic-gateway, novaic-vm)
cd novaic-gateway
python -m py_compile main.py
black --check .
isort --check .

# TypeScript (novaic-app)
cd novaic-app
npm run lint
npm run build

# Rust (novaic-app/src-tauri)
cd novaic-app/src-tauri
cargo check
cargo clippy
```

## 报告 Bug

请在 GitHub Issues 中报告 Bug，并包含以下信息：

- **操作系统**: macOS / Windows / Linux 及版本
- **NovAIC 版本**: 运行的组件版本
- **复现步骤**: 详细描述如何复现问题
- **预期行为**: 你期望发生什么
- **实际行为**: 实际发生了什么
- **日志/截图**: 相关日志或截图（请隐藏敏感信息）

## 功能建议

欢迎在 GitHub Issues 中提出功能建议。请描述：

- **使用场景**: 你想用这个功能做什么
- **当前方案**: 目前是如何解决的（如果有）
- **建议方案**: 你期望的解决方式

## 代码风格

### Python

- 遵循 PEP 8
- 使用 Black 格式化
- 使用 isort 排序导入
- 函数/类添加 docstring

### TypeScript

- 使用 ESLint + Prettier
- 优先使用函数式组件
- Props 使用 TypeScript 接口定义

### Rust

- 遵循 Rust 官方风格指南
- 使用 `cargo fmt` 格式化
- 使用 `cargo clippy` 检查

## 项目结构

```
├── novaic-gateway/   # 核心后端服务 (Gateway + Workers)
├── novaic-app/       # 桌面客户端 (Tauri + React)
├── novaic-vm/        # VM 管理 + MCP 工具服务
└── dev-guide/        # 开发文档
```

每个包相对独立，可以单独开发和测试。

## 许可证

贡献的代码将采用与项目相同的 MIT 许可证。

## 联系方式

如有问题，可以通过以下方式联系：

- GitHub Issues
- GitHub Discussions

感谢你的贡献！
