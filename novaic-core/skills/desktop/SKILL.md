---
name: novaic-desktop
description: Desktop control with two-phase mouse workflow (aim → execute). Use when operating local applications like WeChat, VSCode, or any desktop software through mouse and keyboard automation.
---

# Desktop Control

控制桌面应用程序的核心工具：screenshot、mouse、keyboard。

## 🚨 核心规则：AIM → EXECUTE 二段式操作

**所有鼠标点击必须先 aim 获取 aim_id，然后用 aim_id 执行！**

❌ 禁止：`mouse(action="click", x=500, y=300)`
✅ 正确：`mouse(action="aim", ...)` → `mouse(action="click", aim_id="...")`

## 强制工作流程

```
1. screenshot() → 全屏截图，估算目标坐标 (X, Y)
2. mouse(action='aim', x=X, y=Y) → 获取 aim_id + 放大截图
3. 你来判断（看 MAGENTA 准星位置）：
   - 准星在目标上 → mouse(action='click', aim_id='...')
   - 准星接近但偏了 → 调整坐标重新 aim
   - 准星离目标很远 → 用 zoom=2 重新 aim
```

## Zoom 策略（你来判断）

| 准星与目标距离 | 建议 zoom | 说明 |
|--------------|----------|------|
| 初次定位 | 2 | 默认值，视野范围大 |
| 较远 (>100px) | 2 | 保持视野，先调大方向 |
| 接近 (~50px) | 4-6 | 放大精细微调 |
| 小元素精确点击 | 6-8 | 高倍确保准确 |

**判断要点：**
- 大按钮：准星在按钮范围内即可点击
- 小图标/链接：准星需要接近中心

## 可用工具

### screenshot

纯查看工具。

```python
# 全屏截图（默认带网格）
screenshot()

# 指定区域
screenshot(area={"x": 100, "y": 100, "width": 500, "height": 300})

# 不显示网格
screenshot(grid=False)
```

注意：`mouse(action='aim')` 返回的截图**始终带网格**，无需手动指定。

### mouse

二段式鼠标操作。

**瞄准（返回 aim_id + 截图 + 判断方法）：**
```python
mouse(action="aim", x=600, y=450)        # 默认 zoom=2
mouse(action="aim", x=600, y=450, zoom=4)  # 更高放大
```

**执行（必须使用 aim_id）：**
```python
mouse(action="click", aim_id="aim_abc123")       # 单击
mouse(action="double", aim_id="aim_abc123")      # 双击
mouse(action="right_click", aim_id="aim_abc123") # 右键
mouse(action="scroll", aim_id="aim_abc123", direction="down", amount=3)
```

**拖拽（down → move → up）：**
```python
# 1. 瞄准起点
mouse(action="aim", x=100, y=100)  # → aim_id_1

# 2. 按下
mouse(action="down", aim_id="aim_id_1")

# 3. 瞄准终点
mouse(action="aim", x=500, y=500)  # → aim_id_2

# 4. 移动到终点
mouse(action="move", aim_id="aim_id_2")

# 5. 松开
mouse(action="up")
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

1. ❌ 直接传 x/y 给 click → 使用 aim_id
2. ❌ aim_id 过期后继续使用 → 重新 aim（10分钟有效）
3. ❌ 不看准星位置就点击 → 仔细判断准星是否在目标上
4. ✅ 操作后 screenshot() 验证结果
