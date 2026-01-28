---
name: novaic-desktop
description: Desktop control with two-phase mouse workflow (aim → execute). Use when operating local applications like WeChat, VSCode, or any desktop software through mouse and keyboard automation.
---

# Desktop Control

控制桌面应用程序的核心工具：screenshot、mouse、keyboard。

## 核心概念

### 坐标系统
- 屏幕使用像素坐标，左上角是 (0, 0)
- **全屏截图**：红色网格标注系统坐标
- **aim 截图**：十字坐标轴标注 **delta 值**（以准星为原点）

### aim 截图的十字坐标轴
```
aim 返回的截图中心是准星位置，有两条穿过准星的坐标轴：

        -200  -100   0   +100  +200      ← X轴刻度(delta_x)
          |     |    |     |     |
  ─────────────────⊙───────────────── 水平轴（X轴）
          |     |    |     |     |
                    -100
                    -200                 ← Y轴刻度(delta_y)

⊙ = 准星（原点，坐标为 0）
刻度数字 = 直接可用的 delta 值
```

### zoom 的作用
```
zoom = 放大倍数，控制视野大小和刻度间距

zoom=2 → 视野大，刻度间距 100px
zoom=4 → 视野中等，刻度间距 50px
zoom=4 → 视野中等，刻度间距 25px
zoom=6 → 视野小，刻度间距 10px
zoom=10 → 视野很小，刻度间距 5px（精细微调）

zoom 越大 → 视野越小 → 刻度越密 → 微调越精细
```

### delta 微调
**直接从十字轴读取**，无需计算：
```python
# 初次定位
mouse(action='aim', x=600, y=400)  # → 看到准星在⊙，目标在 -50 刻度处

# 直接用读到的刻度值
mouse(action='aim', aim_id='...', delta_x=-50, zoom=4)
```

目标在哪个刻度，delta 就填什么数字。

## 工作流程

```
screenshot() → 看全屏红色网格，估算目标坐标 (X, Y)
      ↓
mouse(action='aim', x=X, y=Y) → 获取 aim_id，看十字坐标轴
      ↓
判断：准星是否在目标元素内部？
  ├─ 在元素内部 → 直接点击！mouse(action='click', aim_id='...')
  └─ 在元素外部 → 需要 delta 微调进入元素
```

### ⚠️ 重要：不要追求"点在正中心"

**错误行为**：准星已在按钮内，却还要微调到按钮中心
**正确行为**：准星在按钮内的任何位置都可以直接点击

判断标准：
- ✅ 准星在按钮/元素内部 → 直接点击
- ❌ 准星在按钮边缘外 → 需要微调

### ⚠️ 小幅度微调必须先放大 zoom

如果你认为需要微调（delta < 50px），**必须先放大 zoom 确认**：
```
错误：zoom=2 下直接 delta_x=-30  ← 看不清，可能根本不需要调
正确：先 zoom=6 或更高 → 看清准星是否真的在元素外 → 再决定是否微调
```

**原则**：delta 越小，zoom 要越大。禁止在低 zoom 下做小幅度盲调。

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
2. **目标很近时先放大 zoom**：delta < 50 时，先用 zoom=6~10 看清楚再调
3. **delta 要小于网格间距**：避免一次移动过头
   - zoom=2 网格 50px，zoom=6 网格 10px，zoom=10 网格 5px
4. **直接读刻度作为 delta**：目标在 -30 刻度处，delta 就是 -30
5. **在元素内就直接点！** ⚠️ 禁止"对准中心"的强迫症行为
   - 按钮、链接、图标：准星在元素边界内 → 立即点击
   - 不要因为"没在正中间"而微调，这是浪费操作
6. **只有小图标（<20px）才需要精准**：菜单小图标、状态栏图标等
