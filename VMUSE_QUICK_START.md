# VMUSE 快速启动卡片 🚀

## 📦 已完成
✅ 从 git 恢复完整 VMUSE (35 工具)  
✅ 去 FastMCP 化 (http_server.py)  
✅ 自动部署脚本 (deploy_vmuse_to_vm.sh)  
✅ 代码包就绪 (/tmp/novaic-mcp-vmuse.tar.gz)

## 🚀 部署（VM 启动后）

```bash
./deploy_vmuse_to_vm.sh
```

## 🎯 工具清单 (35)

- **Desktop (3)**: screenshot (grid), mouse (2-phase), keyboard
- **Browser (9)**: navigate, click, type, screenshot, scroll, eval, tabs×3  
- **Shell (2)**: run_command, run_python
- **Files (4)**: read, write, list, info
- **Windows (7)**: list, focus, max, min, close, resize, launch
- **Context (7)**: snapshots, clipboard, recent, env

## ⚡ 鼠标操作（两阶段）

```python
# ❌ 不能直接点坐标
mouse(action='click', x=100, y=200)

# ✅ 正确流程
# 1. Aim
result = mouse(action='aim', x=100, y=200, zoom=4)
# → aim_id + screenshot

# 2. Click  
mouse(action='click', aim_id=result['aim_id'])
```

## 📋 API 格式

```
POST /api/vms/{vm_id}/vmuse/{tool}/{operation}
```

示例:
- `/vmuse/desktop/screenshot` → `/api/desktop/screenshot`
- `/vmuse/desktop/mouse` → `/api/desktop/mouse`
- `/vmuse/browser/navigate` → `/api/browser/navigate`

## 📚 详细文档

- `VMUSE_RESTORE.md` - 完整指南
- `deploy_vmuse_to_vm.sh` - 自动部署

---

**快速提交:**
```bash
git commit -m "feat: restore complete VMUSE (35 tools) with de-fastmcp HTTP server"
```
