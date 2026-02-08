# Subagent Build 指南

> 执行 build 任务时参考本文档。

---

## 快速 Build

```bash
cd /Users/wangchaoqun/novaic
sh build.sh
```

---

## Build 产物

```
novaic-app/src-tauri/target/release/bundle/
├── macos/
│   └── NovAIC.app          # macOS 应用
└── dmg/
    └── NovAIC_x.x.x_aarch64.dmg  # DMG 安装包
```

---

## Build 步骤详解

### Step 1: Python Backend

```bash
cd novaic-backend
pyinstaller --clean --noconfirm novaic-backend.spec
```

输出: `dist/novaic-backend/`

### Step 2: 复制资源

```bash
cp -r novaic-backend/dist/novaic-backend novaic-app/src-tauri/resources/
cp -r novaic-vm/src novaic-mcp-vmuse/
```

### Step 3: 前端 + Tauri

```bash
cd novaic-app
npm run tauri build
```

---

## 常见 Build 错误

### TypeScript 类型错误

**症状**：
```
error TS2532: Object is possibly 'undefined'.
error TS18048: 'xxx' is possibly 'undefined'.
```

**修复**：
```typescript
// 错误
a.id - b.id

// 修复：添加默认值
(a.id ?? 0) - (b.id ?? 0)
```

### TypeScript unknown 类型错误

**症状**：
```
error TS18046: 'xxx' is of type 'unknown'.
```

**修复**：
```typescript
// 错误
{value && <div>...</div>}

// 修复：显式转换为布尔值
{!!value && <div>...</div>}
```

### Python 导入错误

**症状**：
```
ModuleNotFoundError: No module named 'xxx'
```

**修复**：检查 `novaic-backend.spec` 的 `datas` 和 `hiddenimports`

---

## Build 后验证

1. **检查产物存在**：
```bash
ls -la novaic-app/src-tauri/target/release/bundle/dmg/
```

2. **检查大小正常**（约 40-50MB）：
```bash
du -sh novaic-app/src-tauri/target/release/bundle/dmg/*.dmg
```

---

## 汇报模板

Build 完成后汇报：

```markdown
## Build 结果

**状态**：成功 / 失败

**修复的错误**（如有）：
- [文件] [错误] [修复方法]

**产物**：
- `NovAIC.app`
- `NovAIC_x.x.x_aarch64.dmg` (xxMB)
```
