# NovAIC 响应式布局设计方案 V2

> 基于三视角分析（UX / 技术 / 设计）的整合方案设计文档

---

## 一、设计目标

1. **可调节**：用户可拖拽调整各模块宽度/高度
2. **可发现**：分隔条、操作按钮易于发现，不依赖悬停
3. **可持久**：布局偏好持久化，刷新后恢复
4. **可响应**：小屏自动折叠/overlay，大屏保持三栏
5. **一致性**：统一设计 token、动画、反馈模式

---

## 二、整体布局结构

### 2.1 桌面端（≥1024px）

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Header (h-10 统一)                                                          │
├────────────┬────────────────────────────────────────────┬──────────────────┤
│            │                                            │                  │
│  Agent     │  Resizer   │      ChatPanel (flex-1)       │  Resizer  │Device│
│  Drawer    │  (可拖拽)   │  ┌─────────────────────────┐  │  (可拖拽)  │Sidebar│
│  (可拖拽)  │            │  │ CollapsibleExecutionLog │  │           │(可拖拽)│
│  w:200-400 │            │  │ (按钮常显)              │  │           │w:180-400│
│            │            │  ├─────────────────────────┤  │           │      │
│            │            │  │ MessageList             │  │           │      │
│            │            │  │                         │  │           │      │
│            │            │  ├─────────────────────────┤  │           │      │
│            │            │  │ ChatInput                │  │           │      │
│            │            │  └─────────────────────────┘  │           │      │
├────────────┴────────────────────────────────────────────┴──────────────────┤
│ Footer (h-6 统一)                                                           │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 平板端（768px ~ 1023px）

```
┌─────────────────────────────────────────────────────────┐
│ Header                                                   │
├──────────┬──────────────────────────────────────────────┤
│ Agent    │  ChatPanel (主)     │ DeviceSidebar (可折叠)   │
│ Drawer   │                   │ 默认折叠为图标栏 w-12     │
│ overlay  │                   │ 点击展开 w-52~200         │
└──────────┴──────────────────────────────────────────────┘
```

### 2.3 移动端（<768px）

```
┌─────────────────────────────┐
│ Header                      │
├─────────────────────────────┤
│ ChatPanel (全宽)             │
│                             │
│ Agent Drawer → overlay 全屏  │
│ DeviceSidebar → overlay 全屏 │
└─────────────────────────────┘
```

---

## 三、模块规格定义

### 3.1 尺寸约束

| 模块 | 默认宽度 | 最小宽度 | 最大宽度 | 说明 |
|------|----------|----------|----------|------|
| Agent Drawer | 288px (w-72) | 200px | 400px | 关闭时为 0 |
| ChatPanel | flex-1 | 320px | - | 保证聊天区最小可用 |
| DeviceSidebar | 208px (w-52) | 180px | 400px | 可折叠为 48px 图标栏 |
| Execution Log 半屏 | 50% | 30% | 70% | 可拖拽垂直 Resizer |

### 3.2 响应式断点

| 断点 | 宽度 | 布局策略 |
|------|------|----------|
| `xl` | ≥1280px | 三栏 + 双 Resizer，全功能 |
| `lg` | 1024~1279px | 三栏 + 双 Resizer，DeviceSidebar 可折叠 |
| `md` | 768~1023px | Agent Drawer overlay，DeviceSidebar 默认折叠 |
| `sm` | <768px | 单栏，Drawer/Sidebar 均为 overlay |

---

## 四、状态模型

### 4.1 布局状态（LayoutState）

```typescript
interface LayoutState {
  // 面板宽度（px）
  drawerWidth: number;
  sidebarWidth: number;
  
  // 折叠状态
  drawerOpen: boolean;
  sidebarCollapsed: boolean;  // 折叠为图标栏
  
  // Execution Log
  logExpanded: boolean;       // 是否半屏展开
  logHeightRatio: number;     // 半屏时高度比例 0.3~0.7
  
  // 响应式：由视口宽度推导，不持久化
  // breakpoint: 'xl' | 'lg' | 'md' | 'sm'
}
```

### 4.2 持久化格式

```typescript
interface LayoutPersistence {
  drawerWidth: number;
  sidebarWidth: number;
  drawerOpen: boolean;
  sidebarCollapsed: boolean;
  logExpanded: boolean;
  logHeightRatio: number;
  version: number;  // 用于未来迁移
}
```

- **Storage Key**: `novaic-layout-v2`
- **写入时机**: `mouseup` 或折叠状态变化时，防抖 300ms
- **恢复校验**: 宽度需在 MIN~MAX 范围内，否则回退默认值

---

## 五、组件设计

### 5.1 Resizer 增强

**扩展为支持水平/垂直**：

```typescript
interface ResizerProps {
  axis: 'horizontal' | 'vertical';
  onResize: (delta: number) => void;
  onDoubleClick?: () => void;
  /** 拖拽时的视觉反馈 */
  isDragging?: boolean;
}
```

**交互规范**：
- 默认：1px 细线，`bg-nb-border`
- 悬停：4px 可拖拽区域，`bg-nb-accent/30`，显示 `⋮⋮` 或 `⋯` 图标
- 拖拽中：高亮 `bg-nb-accent/50`
- 双击：恢复默认宽度/高度

**性能**：
- 使用 `requestAnimationFrame` 节流 mousemove
- 父组件用 CSS 变量 `--panel-width` 更新，减少 React 重渲染

### 5.2 LayoutContainer（新增）

**职责**：统一管理三栏布局、Resizer、尺寸约束、持久化

```tsx
<LayoutContainer
  drawerWidth={drawerWidth}
  sidebarWidth={sidebarWidth}
  onDrawerResize={...}
  onSidebarResize={...}
  breakpoint={breakpoint}
>
  <AgentDrawer ... />
  <main>
    <ChatPanel ... />
    <DeviceSidebar ... />
  </main>
</LayoutContainer>
```

### 5.3 DeviceSidebar 增强

**标题栏**：
- 标题：`{currentAgent?.name ?? '当前'} 的设备`
- 右侧：折叠按钮 `⊟`（折叠为图标栏）、关闭按钮 `✕`（隐藏，仅 md 以下）

**预设档位**（点击标题栏或按钮循环）：
- 展开：当前宽度（可拖拽）
- 折叠：48px 图标栏，仅显示设备类型图标
- 隐藏：0px（仅 md 以下可用）

**无设备时**：收缩为 48px，显示「+ 添加设备」

### 5.4 CollapsibleExecutionLog 增强

**按钮常显**：
- 展开/收起、全屏按钮始终可见，不依赖 `isHovered`
- 或改为图标按钮，悬停显示 tooltip

**半屏可调高度**：
- 在半屏与 MessageList 之间增加垂直 Resizer
- 支持 30%~70% 范围拖拽
- 双击恢复 50%

### 5.5 Agent Drawer

**持久化**：`drawerOpen` 存入 LayoutPersistence

**Header 快速切换**（可选 Phase 2）：
- 在 Header 当前 Agent 名称旁增加下拉/左右箭头
- 无需打开 Drawer 即可切换最近使用的 Agent

---

## 六、设计系统补全

### 6.1 Tailwind 新增 Token

```javascript
// tailwind.config.js - colors 补充
'nb': {
  // ... 现有
  'surface-hover': '#1c2128',   // 与 hover 对齐
  'border-hover': '#484f58',
  'card': '#161b22',
}
```

### 6.2 统一规范

| 元素 | 规范 |
|------|------|
| Header 高度 | `h-10` (40px) 全局统一 |
| Footer 高度 | `h-6` (24px) 全局统一 |
| 卡片圆角 | `rounded-lg` |
| 按钮圆角 | `rounded-lg` |
| Modal 圆角 | `rounded-xl` |
| 过渡动画 | `transition-all duration-200 ease-out` |
| 间距 scale | 4/8/12/16/24/32 (px) |

### 6.3 错误/空状态统一

- ErrorBoundary、连接超时、设备错误：统一使用 `nb-*` 色系
- 空状态：统一插画风格、文案结构、CTA 按钮样式

---

## 七、实施路线图

### Phase 1：基础可拖拽（1-2 天）

| 任务 | 说明 |
|------|------|
| 扩展 Resizer | 支持 axis，增加 RAF 节流 |
| 接入 ChatPanel-DeviceSidebar Resizer | 在两者之间插入 Resizer，宽度可拖拽 |
| 布局状态统一 | 新建 `useLayoutStore` 或扩展 store，管理 `sidebarWidth` |
| 持久化 | 拖拽结束写入 localStorage，启动时恢复 |

**验收**：用户可拖拽调整 DeviceSidebar 宽度，刷新后保持

### Phase 2：Drawer + 设计补全（1 天）

| 任务 | 说明 |
|------|------|
| Agent Drawer Resizer | Drawer 与 Main 之间接入 Resizer |
| drawerOpen 持久化 | 存入 LayoutPersistence |
| Tailwind token 补全 | nb-surface-hover、nb-border-hover、nb-card |
| Header/Footer 高度统一 | Setup、Dashboard 等页面统一为 h-10/h-6 |

### Phase 3：Execution Log + DeviceSidebar 增强（1-2 天）

| 任务 | 说明 |
|------|------|
| Execution Log 按钮常显 | 移除 isHovered 依赖 |
| 半屏垂直 Resizer | 可拖拽调整 log 高度，持久化 logHeightRatio |
| DeviceSidebar 标题优化 | 显示「{Agent} 的设备」 |
| DeviceSidebar 预设档位 | 展开/折叠/隐藏（小屏） |

### Phase 4：响应式断点（1 天）

| 任务 | 说明 |
|------|------|
| 断点 Hook | `useBreakpoint()` 返回 xl/lg/md/sm |
| md 以下 | DeviceSidebar 默认折叠，Drawer overlay |
| sm 以下 | 单栏，Drawer/Sidebar 均为 overlay |
| 无设备时收缩 | DeviceSidebar 收缩为 48px |

### Phase 5：优化与收尾（可选）

| 任务 | 说明 |
|------|------|
| LayoutMode 整合或移除 | 若保留 full/normal/mini，需与布局打通 |
| Header 快速切换 Agent | 下拉或左右箭头 |
| 无障碍 | Resizer 键盘支持、ARIA、焦点 trap |
| 首次使用引导 | 三栏用途 Tooltip 或引导浮层 |

---

## 八、文件变更清单

| 文件 | 变更类型 |
|------|----------|
| `src/components/Layout/Resizer.tsx` | 修改：支持 axis、RAF |
| `src/components/Layout/LayoutContainer.tsx` | 新增：布局容器 |
| `src/App.tsx` | 修改：接入 LayoutContainer、Resizer |
| `src/store/index.ts` | 修改：扩展布局状态、持久化 |
| `src/config/index.ts` | 修改：LAYOUT_CONFIG 扩展 |
| `src/types/index.ts` | 修改：LayoutState、LayoutPersistence |
| `tailwind.config.js` | 修改：补全 nb token |
| `DeviceSidebar.tsx` | 修改：标题、档位、折叠 |
| `CollapsibleExecutionLog.tsx` | 修改：按钮常显 |
| `ChatPanel.tsx` | 修改：半屏 Resizer、logHeightRatio |
| `SetupWorkspace.tsx` | 修改：Header h-10 统一 |

---

## 九、风险与降级

| 风险 | 降级方案 |
|------|----------|
| 拖拽性能差 | 已用 RAF + CSS 变量，若仍卡顿可提高节流阈值 |
| 持久化数据损坏 | 恢复时校验 version 和范围，失败则用默认值 |
| 小屏布局错乱 | 断点下强制 overlay，禁用拖拽 |
| 旧版 localStorage 冲突 | 使用新 key `novaic-layout-v2`，与旧 key 并存 |

---

## 十、附录：默认值速查

```typescript
const LAYOUT_DEFAULTS = {
  drawerWidth: 288,
  drawerMin: 200,
  drawerMax: 400,
  sidebarWidth: 208,
  sidebarMin: 180,
  sidebarMax: 400,
  sidebarCollapsedWidth: 48,
  logHeightRatio: 0.5,
  logHeightMin: 0.3,
  logHeightMax: 0.7,
};
```
