---
name: novaic-desktop
description: Desktop control with two-phase mouse workflow (aim → execute). Use when operating local applications like WeChat, VSCode, or any desktop software through mouse and keyboard automation.
---

# Desktop Control

控制桌面应用程序的核心工具：screenshot、mouse、keyboard。

## 核心概念

### 坐标系统
- 屏幕使用像素坐标，左上角是 (0, 0)
- 截图上的红色网格标注的是**系统坐标**（真实像素位置）
- 不管 zoom 多少，网格数字始终是系统坐标

### zoom 的作用
```
zoom = 放大倍数，决定截图显示屏幕的多大区域

zoom=2 → 显示屏幕 1/2 区域（视野大，网格稀疏）
zoom=4 → 显示屏幕 1/4 区域（视野小，网格更密）
zoom=6 → 显示屏幕 1/6 区域（视野更小，网格很密）

视野越小 → 看得越清楚 → 网格越密 → 越容易精确定位
```

### delta 微调
当准星接近目标但需要微调时，可以用 delta 相对位移：
```python
# 初次定位
mouse(action='aim', x=600, y=400)  # → aim_id_1

# 微调：向左移 50px，向上移 20px
mouse(action='aim', aim_id='aim_id_1', delta_x=-50, delta_y=-20, zoom=4)
# 新位置 = (600-50, 400-20) = (550, 380)
```

**计算 delta 的方法：**
1. 读网格，找到准星当前坐标（如 x=600）
2. 读网格，找到目标的坐标（如 x=550）
3. delta_x = 目标x - 准星x = 550 - 600 = -50

## 工作流程

```
screenshot() → 看全屏，估算目标位置 (X, Y)
      ↓
mouse(action='aim', x=X, y=Y) → 获取 aim_id，看准星位置
      ↓
判断准星是否在目标上？
  ├─ 是 → mouse(action='click', aim_id='...')
  └─ 否 → 根据偏差调整：
           - 用 delta 微调坐标
           - 根据需要调整 zoom
           - 重新 aim
```

## API 参考

### screenshot
```python
screenshot()                    # 全屏，带网格
screenshot(grid=False)          # 全屏，不带网格
screenshot(area={...})          # 指定区域
```

### mouse

**瞄准：**
```python
# 绝对坐标定位
mouse(action='aim', x=600, y=400)
mouse(action='aim', x=600, y=400, zoom=4)  # 指定放大倍数

# delta 微调（基于上次 aim 位置）
mouse(action='aim', aim_id='aim_xxx', delta_x=-50, delta_y=20, zoom=4)
```

**执行（必须用 aim_id）：**
```python
mouse(action='click', aim_id='aim_xxx')
mouse(action='double', aim_id='aim_xxx')
mouse(action='right_click', aim_id='aim_xxx')
mouse(action='scroll', aim_id='aim_xxx', direction='down', amount=3)
```

**拖拽：**
```python
mouse(action='aim', x=100, y=100)           # 起点
mouse(action='down', aim_id='aim_1')
mouse(action='aim', x=500, y=500)           # 终点（或用 delta）
mouse(action='move', aim_id='aim_2')
mouse(action='up')
```

### keyboard
```python
keyboard(action='type', text='Hello')
keyboard(action='key', keys=['ctrl', 's'])
```

## 技巧

1. **初次定位用低 zoom (2)**：视野大，容易找到目标
2. **微调时增大 zoom (4-6)**：网格更密，容易精确调整
3. **用 delta 而不是重新估算坐标**：更准确，不容易算错
4. **大按钮容错大**：准星在按钮任意位置都能点击
5. **小图标要精确**：准星需要接近中心
