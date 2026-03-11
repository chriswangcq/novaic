# NovAIC 布局与 Execution Log 统一变更方案

> 将「响应式布局 + 可拖拽」与「Execution Log 按 Subagent 拆分胶囊」合并为单一变更方案

---

## 一、变更总览

| 需求 | 核心内容 |
|------|----------|
| **布局响应式** | 三栏可拖拽、布局持久化、响应式断点、设计 token 补全 |
| **Execution Log 胶囊** | 按 subagent 分胶囊、胶囊可折叠、浮动条胶囊标识 |

**合并原则**：共享 Resizer、设计系统、状态持久化；统一实施顺序，避免冲突。

---

## 二、整体布局结构（含 Execution Log）

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Header (h-10 统一)                                                          │
├────────────┬────────────────────────────────────────────┬──────────────────┤
│  Agent     │  Resizer   │      ChatPanel (flex-1)       │  Resizer  │Device│
│  Drawer    │  (水平)     │  ┌─────────────────────────┐  │  (水平)   │Sidebar│
│  w:200-400 │            │  │ CollapsibleExecutionLog │  │           │w:180-400│
│            │            │  │ (按钮常显 + 胶囊预览)    │  │           │      │
│            │            │  ├─────────────────────────┤  │           │      │
│            │            │  │ MessageList             │  │           │      │
│            │            │  │                         │  │           │      │
│            │            │  ├─ Resizer (垂直) ───────┤  │           │      │
│            │            │  │ ExecutionLog (半屏)     │  │           │      │
│            │            │  │ ┌─ 主 Agent 胶囊 ──────┐│  │           │      │
│            │            │  │ │ LogCard...           ││  │           │      │
│            │            │  │ └─────────────────────┘│  │           │      │
│            │            │  │ ┌─ Subagent 胶囊 ──────┐│  │           │      │
│            │            │  │ │ LogCard...           ││  │           │      │
│            │            │  │ └─────────────────────┘│  │           │      │
│            │            │  ├─────────────────────────┤  │           │      │
│            │            │  │ ChatInput               │  │           │      │
│            │            │  └─────────────────────────┘  │           │      │
├────────────┴────────────────────────────────────────────┴──────────────────┤
│ Footer (h-6 统一)                                                           │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 三、统一状态模型

### 3.1 布局状态（LayoutState）

```typescript
interface LayoutState {
  // 面板宽度（px）
  drawerWidth: number;
  sidebarWidth: number;
  
  // 折叠状态
  drawerOpen: boolean;
  sidebarCollapsed: boolean;
  
  // Execution Log
  logExpanded: boolean;
  logHeightRatio: number;
  
  // Execution Log 胶囊（可选持久化）
  expandedCapsules: Set<string>;  // 'main' | subagent_id
}
```

### 3.2 持久化格式

```typescript
interface LayoutPersistence {
  drawerWidth: number;
  sidebarWidth: number;
  drawerOpen: boolean;
  sidebarCollapsed: boolean;
  logExpanded: boolean;
  logHeightRatio: number;
  expandedCapsules: string[];  // 展开的胶囊 ID 列表
  version: number;
}
```

- **Storage Key**: `novaic-layout-v2`
- **expandedCapsules**: 默认展开全部时存空数组 `[]`；部分折叠时存展开的 ID

---

## 四、组件与模块设计

### 4.1 共享组件

| 组件 | 用途 | 变更 |
|------|------|------|
| **Resizer** | 水平（Drawer、Sidebar）、垂直（Log 半屏） | 支持 axis、RAF 节流 |
| **LayoutContainer** | 三栏布局容器 | 新增 |

### 4.2 布局相关

| 组件 | 变更 |
|------|------|
| App.tsx | 接入 LayoutContainer、Resizer |
| AgentDrawer | 宽度由 LayoutContainer 控制，drawerOpen 持久化 |
| DeviceSidebar | 标题「{Agent} 的设备」、档位（展开/折叠/隐藏） |
| ChatPanel | 半屏 Resizer、logHeightRatio 持久化 |

### 4.3 Execution Log 相关

| 组件 | 变更 |
|------|------|
| **LogCapsule** | 新增：胶囊容器（Header + Content） |
| **ExecutionLog** | 分组逻辑、胶囊渲染、Tab 与过滤联动 |
| **CollapsibleExecutionLog** | 按钮常显、预览条加 `[主]`/`[A]` 胶囊标识 |

### 4.4 设计系统

| 类型 | 变更 |
|------|------|
| tailwind.config.js | 补全 nb-surface-hover、nb-border-hover、nb-card |
| 全局 | Header 统一 h-10、Footer 统一 h-6 |

---

## 五、统一实施路线图

### Phase 1：基础设施（1 天）

| 任务 | 说明 |
|------|------|
| 扩展 Resizer | 支持 `axis: 'horizontal' \| 'vertical'`，RAF 节流 |
| Tailwind token 补全 | nb-surface-hover、nb-border-hover、nb-card |
| Header/Footer 高度统一 | Setup、Dashboard 等页面统一为 h-10/h-6 |
| 布局状态与持久化 | LayoutPersistence 类型、load/save 逻辑 |

**验收**：Resizer 可水平/垂直使用，设计 token 可用，布局状态可持久化

---

### Phase 2：三栏可拖拽（1-2 天）

| 任务 | 说明 |
|------|------|
| 新增 LayoutContainer | 管理 drawerWidth、sidebarWidth、Resizer |
| ChatPanel ↔ DeviceSidebar Resizer | 水平 Resizer，宽度可拖拽 |
| Agent Drawer Resizer | Drawer 与 Main 之间 Resizer |
| 持久化 | 拖拽结束写入 localStorage，启动时恢复 |
| drawerOpen 持久化 | 存入 LayoutPersistence |

**验收**：用户可拖拽调整 Drawer、Sidebar 宽度，刷新后保持

---

### Phase 3：Execution Log 胶囊 + 增强（1.5-2 天）

| 任务 | 说明 |
|------|------|
| 新增 LogCapsule | 标题栏（名称、条数、状态、折叠）+ 内容区 |
| ExecutionLog 分组 | groupLogsBySubagent，渲染胶囊列表 |
| 胶囊折叠状态 | expandedCapsules，默认全展开 |
| logSubagentId 过滤 | 选中 Tab 时只渲染该胶囊 |
| CollapsibleExecutionLog 按钮常显 | 移除 isHovered 依赖 |
| 半屏垂直 Resizer | ChatPanel 内 Log 与 MessageList 之间，可调 logHeightRatio |
| 预览条胶囊标识 | 每条 log 前加 `[主]`/`[A]` 等 |
| 胶囊折叠持久化 | 可选，存入 LayoutPersistence |

**验收**：日志按 subagent 分胶囊展示，可折叠胶囊，半屏 Log 可调高度，按钮常显

---

### Phase 4：DeviceSidebar + 响应式（1 天）

| 任务 | 说明 |
|------|------|
| DeviceSidebar 标题 | 显示「{Agent} 的设备」 |
| DeviceSidebar 预设档位 | 展开/折叠/隐藏（小屏） |
| 断点 Hook | useBreakpoint() 返回 xl/lg/md/sm |
| md 以下 | DeviceSidebar 默认折叠，Drawer overlay |
| sm 以下 | 单栏，Drawer/Sidebar 均为 overlay |

**验收**：DeviceSidebar 可折叠，小屏布局正常

---

### Phase 5：优化与收尾（可选）

| 任务 | 说明 |
|------|------|
| LayoutMode 整合或移除 | 若保留需与布局打通 |
| Header 快速切换 Agent | 下拉或左右箭头 |
| 胶囊内虚拟列表 | 单胶囊 log 数 > 50 时启用 |
| 无障碍 | Resizer 键盘、ARIA、焦点 trap |

---

## 六、统一文件变更清单

| 文件 | 变更类型 | 说明 |
|------|----------|------|
| `src/components/Layout/Resizer.tsx` | 修改 | 支持 axis、RAF |
| `src/components/Layout/LayoutContainer.tsx` | 新增 | 布局容器 |
| `src/App.tsx` | 修改 | 接入 LayoutContainer、Resizer |
| `src/store/index.ts` | 修改 | 布局状态、持久化、expandedCapsules |
| `src/config/index.ts` | 修改 | LAYOUT_CONFIG 扩展 |
| `src/types/index.ts` | 修改 | LayoutState、LayoutPersistence |
| `tailwind.config.js` | 修改 | 补全 nb token |
| `src/components/Layout/DeviceSidebar.tsx` | 修改 | 标题、档位、折叠 |
| `src/components/Visual/LogCapsule.tsx` | 新增 | 胶囊组件 |
| `src/components/Visual/ExecutionLog.tsx` | 修改 | 分组、胶囊渲染、过滤 |
| `src/components/Visual/CollapsibleExecutionLog.tsx` | 修改 | 按钮常显、胶囊标识 |
| `src/components/Chat/ChatPanel.tsx` | 修改 | 半屏 Resizer、logHeightRatio |
| `src/components/Setup/SetupWorkspace.tsx` | 修改 | Header h-10 统一 |

---

## 七、依赖关系图

```
Phase 1 (基础设施)
    ├── Resizer 扩展 ───┐
    ├── Tailwind token  │
    └── 布局状态/持久化  │
                        │
Phase 2 (三栏可拖拽)   │
    ├── LayoutContainer ←┘
    ├── ChatPanel-Sidebar Resizer
    ├── Drawer Resizer
    └── drawerOpen 持久化
                        │
Phase 3 (Execution Log) │
    ├── LogCapsule (新增)
    ├── ExecutionLog 分组
    ├── 半屏 Resizer ←── Resizer
    ├── CollapsibleExecutionLog 增强
    └── 胶囊折叠/过滤
                        │
Phase 4 (DeviceSidebar + 响应式)
    ├── DeviceSidebar 档位
    └── useBreakpoint + 断点布局
```

---

## 八、默认值速查

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
  expandedCapsules: [] as string[],  // 空表示全部展开
};
```

---

## 九、风险与降级

| 风险 | 降级方案 |
|------|----------|
| 拖拽性能差 | RAF + CSS 变量；仍卡顿则提高节流阈值 |
| 持久化数据损坏 | 恢复时校验 version 和范围，失败用默认值 |
| 胶囊数量过多 | Phase 1 不虚拟化；>10 胶囊时考虑胶囊级虚拟化 |
| 小屏布局错乱 | 断点下强制 overlay，禁用拖拽 |
| 旧版 localStorage | 新 key `novaic-layout-v2`，与旧 key 并存 |

---

## 十、附录：胶囊与 Log 结构示意

```
ExecutionLog (半屏展开时)
├── Header (Terminal + 标题 + Subagent Tabs)
├── 滚动容器
│   ├── LogCapsule (主 Agent)
│   │   ├── LogCapsuleHeader
│   │   └── LogCapsuleContent
│   │       ├── LogCard 1
│   │       ├── LogCard 2
│   │       └── ...
│   ├── LogCapsule (subagent-xxx)
│   │   ├── LogCapsuleHeader
│   │   └── LogCapsuleContent
│   │       ├── LogCard 1
│   │       └── ...
│   └── ...
└── (加载更多)
```
