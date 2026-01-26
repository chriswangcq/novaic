---
name: novaic-desktop
description: Desktop control with screenshot verification workflow. Use when operating local applications like WeChat, VSCode, or any desktop software through mouse and keyboard automation.
---

# Desktop Control

控制桌面应用程序的核心工具：screenshot、mouse、keyboard。

## 🚨 关键规则：点击前必须确认准星位置

**这是最重要的规则。盲目点击会导致操作失败。**

## 强制工作流程

```
1. screenshot() → 获取全屏截图，估算目标坐标 (X, Y)
2. screenshot(center={"x":X, "y":Y}, zoom_factor=2) → 放大查看
3. 确认 MAGENTA 准星是否在目标上？
   - YES → 执行 mouse(action="click", x=X, y=Y)
   - NO → 调整坐标，重复步骤 2-3
```

## Zoom Factor 选择

| 元素大小 | zoom_factor |
|----------|-------------|
| 大按钮 | 2 |
| 中等图标 | 3 |
| 小元素 | 4-5 |

## 可用工具

### screenshot

截取桌面截图，带红色坐标网格。

```python
# 全屏截图
screenshot()

# 放大指定区域
screenshot(center={"x": 600, "y": 450}, zoom_factor=2)

# 网格密度：fine=100px, normal=200px, coarse=400px
screenshot(grid_density="fine")
```

### mouse

鼠标操作：点击、双击、拖拽、滚动。

```python
# 单击
mouse(action="click", x=450, y=320)

# 双击
mouse(action="double", x=450, y=320)

# 右键
mouse(action="click", x=450, y=320, button="right")

# 拖拽
mouse(action="drag", x=100, y=100, to_x=500, to_y=500)

# 滚动
mouse(action="scroll", x=450, y=320, direction="down", amount=3)
```

### keyboard

键盘输入和快捷键。

```python
# 输入文本
keyboard(action="type", text="Hello World")

# 快捷键
keyboard(action="key", keys=["ctrl", "s"])
keyboard(action="key", keys=["ctrl", "shift", "p"])
```

支持的特殊键：ctrl, alt, shift, super, enter, tab, escape, backspace, delete, up, down, left, right, f1-f12

## ⚠️ 常见错误

1. ❌ 不要盲目点击，总是先截图确认
2. ❌ 不要在操作失败后立即重试，先截图查看当前状态
3. ✅ 操作后截图验证结果
