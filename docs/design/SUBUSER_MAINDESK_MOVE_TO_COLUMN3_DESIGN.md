# Subuser / Maindesk 移至第三栏设计

> 目标：将 Main Desktop 与 Subuser 的切换、管理从第二栏（AgentDrawer）移到第三栏（DeviceManagerPage）。

---

## 一、现状

### 1.1 三栏结构

| 栏 | 组件 | Devices  tab 时内容 |
|----|------|---------------------|
| 第一栏 | PrimaryNav | Agents \| Devices \| Setting |
| 第二栏 | AgentDrawer | 设备列表 + **可展开的 Main Desktop / Subuser 树** |
| 第三栏 | DeviceManagerPage | 仅 VNC 画布（无设备列表、无 subuser 切换） |

### 1.2 当前交互

1. 第二栏：点击 Linux 设备 → 展开树 → 显示「Main Desktop」「subuser1」「subuser2」…
2. 第二栏：点击 Main Desktop 或某个 subuser → 设置 `selectedVmUser`
3. 第三栏：根据 `selectedDeviceId` + `selectedVmUser` 渲染对应 VNC 视图

### 1.3 问题

- 第二栏承担「选设备」和「选桌面（main/subuser）」两个职责，信息密度高
- 第三栏只展示画布，缺少上下文和操作入口
- 用户期望：第二栏只做导航（选设备），第三栏做内容区（选桌面 + 看桌面 + 管理 subuser）

---

## 二、目标设计

### 2.1 职责划分

| 栏 | 职责 | 内容 |
|----|------|------|
| 第二栏 | **仅设备导航** | 设备列表（扁平，无展开树） |
| 第三栏 | **设备内容区** | Main/Subuser 切换 + VNC 画布 + Subuser 管理 |

### 2.2 第二栏改动

- **移除**：Linux 设备下的展开树（Main Desktop、Subuser 列表）
- **保留**：设备列表、楼层分组、状态、添加设备入口
- **简化**：点击设备仅设置 `selectedDeviceId`，不再在第二栏选择 main/subuser

### 2.3 第三栏改动

当 `selectedDeviceId` 对应 Linux 设备且 `status === 'running'` 时，第三栏结构：

```
┌─────────────────────────────────────────────────────────────────────┐
│ 设备名 · 状态     [Main Desktop] [subuser1] [subuser2]  [+ 添加]   │  ← 顶部切换栏
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│                        VNC 画布 (DeviceDesktopView)                 │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

- **顶部切换栏**：Tab 或 Segmented Control，包含 Main Desktop + 各 subuser
- **Subuser 管理**：在切换栏右侧或下拉菜单中提供「添加 subuser」「删除」「重启 VNC」
- **VNC 画布**：与现有一致，根据当前选中的 main/subuser 渲染

---

## 三、具体实现方案

### 3.1 AgentDrawer（第二栏）

**修改点**：`DeviceListItem` 与 `devicesContent`

1. **移除展开逻辑**：
   - 删除 `expandedDeviceIds`、`onToggle`、`isExpanded`
   - 删除 `ChevronDown` 展开按钮
   - 删除 `{isLinux && isExpanded && (...)}` 下的 Main Desktop / Subuser 列表

2. **保留**：
   - 设备行点击 → `openDevice(device.id)`（设置 `selectedDeviceId`，清空 `selectedVmUser`）
   - 添加 subuser 按钮（Users 图标）→ 打开 AddVmSubuserModal

3. **默认选中**：
   - 进入设备时默认 `selectedVmUser = null`（Main Desktop）
   - 第三栏负责展示 Main Desktop，用户可在第三栏切换到 subuser

### 3.2 DeviceManagerPage（第三栏）

**修改点**：为 Linux 设备增加「Main / Subuser 切换栏」

1. **新增组件** `LinuxDesktopSwitcher`：
   - 位置：VNC 画布上方
   - 内容：Main Desktop | subuser1 | subuser2 | … | [+ 添加]
   - 选中态与 `selectedVmUser` 同步
   - 点击 tab → 更新 `selectedVmUser`（null = Main，对象 = subuser）
   - 右侧：添加 subuser 按钮、subuser 行内删除/重启 VNC（可选放在 hover 或下拉）

2. **布局**：
   - 顶部：`h-10` 或 `h-11` 的 switcher 栏
   - 下方：`flex-1` 的 `DeviceDesktopView`（main 或 vm_user）

3. **复用**：
   - `VmUsersSection` 的逻辑（加载 users、add/delete/restart）迁移到 `LinuxDesktopSwitcher` 或作为其子逻辑
   - `DeviceDesktopView` 不变，仍通过 `subjectType` + `username` 区分 main/subuser

### 3.3 状态流

```
第二栏点击设备
  → setSelectedDeviceId(id)
  → setSelectedVmUser(null)  // 默认 Main Desktop

第三栏加载
  → 若 Linux + running：显示 LinuxDesktopSwitcher + DeviceDesktopView
  → 用户点击 subuser tab
  → setSelectedVmUser({ username, displayNum })
  → DeviceDesktopView 重渲染为 vm_user 模式
```

### 3.4 手机式布局

- 手机式下，第二栏为 overlay，第三栏全屏
- 第三栏的 switcher 同样置于顶部，与 PC 一致
- 无需额外分支

---

## 四、文件改动清单

| 文件 | 改动 |
|------|------|
| `AgentDrawer.tsx` | 移除 DeviceListItem 内展开树、Main/Subuser 列表；简化设备行 |
| `DeviceManagerPage.tsx` | 新增 `LinuxDesktopSwitcher`；Linux 设备时在 VNC 上方渲染 |
| `DeviceListPanel`（若独立） | 移除 compact 模式下的 `VmUsersSection` 嵌入（若存在） |
| `DeviceVNCView.tsx` | 无需改，仍由 DeviceManagerPage 按 selectedVmUser 选择渲染 main/subuser |

---

## 五、UI 草图（第三栏）

```
┌──────────────────────────────────────────────────────────────────┐
│  Linux VM · Running                                               │
│  ┌─────────────┬──────────┬──────────┐  [+ 添加]                  │
│  │ Main Desktop│ subuser1 │ subuser2 │                            │
│  └─────────────┴──────────┴──────────┘                            │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│   ████████████████████████████████████████████████████████████   │
│   ██                                                    ██       │
│   ██              VNC 桌面画面                          ██       │
│   ██                                                    ██       │
│   ████████████████████████████████████████████████████████████   │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

- Tab 样式：Segmented Control 或 underline tab，与现有风格一致
- Subuser 行：hover 显示删除、重启 VNC 图标（与当前 VmUsersSection 一致）

---

## 六、兼容与回退

- `selectedVmUser` 仍存于 store，第三栏与 AgentDrawer 共享
- 若需回退，恢复 AgentDrawer 内展开树即可，无需改 store 结构
