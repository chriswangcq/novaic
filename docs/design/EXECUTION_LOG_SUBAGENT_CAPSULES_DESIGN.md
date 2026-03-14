# Execution Log 按 Subagent 拆分独立胶囊设计方案

> 将 Execution Log 按 subagent 拆分为独立胶囊，提升多子任务场景下的可读性与可操作性

---

## 一、设计目标

1. **按 subagent 分组**：每个 subagent 的日志独立成「胶囊」，视觉上清晰分离
2. **独立可操作**：每个胶囊可单独折叠/展开、筛选、聚焦
3. **保持时序**：胶囊之间按首次出现时间排序，胶囊内日志按时间顺序
4. **兼容无 subagent**：主 Agent 日志（无 subagent_id）归入「主 Agent」胶囊

---

## 二、当前实现 vs 目标

### 2.1 当前实现

| 维度 | 现状 |
|------|------|
| 展示方式 | 扁平列表，可选 Tab 过滤（全部 / subagent A / subagent B） |
| subagent 标识 | 每条 LogCard 上显示 `subagent_id` 小标签（仅「全部」时） |
| 过滤 | 点击 Tab 后只显示该 subagent 的日志，其他隐藏 |

### 2.2 目标

| 维度 | 目标 |
|------|------|
| 展示方式 | 按 subagent 分组的胶囊列表，每个胶囊独立容器 |
| subagent 标识 | 胶囊标题栏显示 subagent 名称/ID，胶囊内不再重复 |
| 过滤 | 保留 Tab 筛选，但默认展示所有胶囊；可增加「仅展开选中胶囊」等模式 |

---

## 三、胶囊视觉设计

### 3.1 胶囊结构

```
┌─────────────────────────────────────────────────────────────────┐
│ 胶囊标题栏                                                       │
│ [图标] Subagent A (或 "主 Agent")    [3 条] [运行中●] [▼ 折叠]   │
├─────────────────────────────────────────────────────────────────┤
│ 胶囊内容区                                                       │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │ LogCard 1                                                │   │
│   └─────────────────────────────────────────────────────────┘   │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │ LogCard 2                                                │   │
│   └─────────────────────────────────────────────────────────┘   │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │ LogCard 3                                                │   │
│   └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 胶囊标题栏

| 元素 | 说明 |
|------|------|
| 图标 | 主 Agent 用 `User`/`Monitor`，subagent 用 `Bot`/`Cpu` 等，可区分 |
| 名称 | 主 Agent：`主 Agent` 或 `Main`；subagent：`subagent_id` 或可读名 |
| 日志数 | `N 条` |
| 状态 | 有 running 时显示 `运行中●`，有 failed 时显示 `失败●` |
| 折叠按钮 | `▼` 展开 / `▶` 折叠，点击切换 |

### 3.3 胶囊样式

- **容器**：`rounded-xl`，`border border-nb-border`，`bg-nb-surface/80`
- **标题栏**：`bg-nb-surface-2/50`，`px-3 py-2`，可点击折叠
- **内容区**：`p-2` 或 `p-3`，LogCard 之间 `space-y-2`
- **主 Agent 胶囊**：可选轻微区分色，如 `border-l-2 border-l-blue-500/50`
- **subagent 胶囊**：可选 `border-l-2 border-l-violet-500/50` 等

---

## 四、数据模型

### 4.1 分组逻辑

```typescript
// 将 logs 按 subagent_id 分组
function groupLogsBySubagent(logs: LogEntry[]): Map<string | 'main', LogEntry[]> {
  const groups = new Map<string | 'main', LogEntry[]>();
  
  for (const log of logs) {
    const key = log.subagent_id ?? 'main';
    if (!groups.has(key)) {
      groups.set(key, []);
    }
    groups.get(key)!.push(log);
  }
  
  return groups;
}
```

### 4.2 胶囊排序

- **主 Agent**（`main`）始终排第一
- **subagent** 按该胶囊内**第一条日志的 timestamp** 升序排列
- 同一会话中，主 Agent 先产生日志，subagent 后产生，因此主 Agent 通常在前

### 4.3 与现有过滤的兼容

- **logSubagentId === null**：展示所有胶囊
- **logSubagentId === 'xxx'**：只展示该 subagent 的胶囊（单胶囊模式）
- Tab 行为保持不变，但单胶囊时不再显示「全部」以外的 Tab（或隐藏 Tab 行）

---

## 五、组件结构

### 5.1 新增/修改组件

```
ExecutionLog (现有，修改)
├── LogCapsule (新增) - 单个胶囊
│   ├── LogCapsuleHeader - 标题栏
│   └── LogCapsuleContent - 内容区（LogCard 列表）
└── 虚拟列表 / 滚动容器
```

### 5.2 LogCapsule 接口

```typescript
interface LogCapsuleProps {
  /** 胶囊 ID：'main' | subagent_id */
  capsuleId: string;
  /** 显示名称 */
  displayName: string;
  /** 是否为主 Agent */
  isMain: boolean;
  /** 该胶囊内的日志 */
  logs: LogEntry[];
  /** 是否展开 */
  isExpanded: boolean;
  /** 切换展开 */
  onToggleExpand: () => void;
  /** 是否显示 subagent 标签（单胶囊时可不显示） */
  showSubagentBadge: boolean;
  /** 展开的 log key 集合 */
  expandedLogs: Set<string>;
  /** 切换 log 展开 */
  onToggleLogExpand: (logKey: string) => void;
}
```

### 5.3 折叠状态管理

- **胶囊折叠**：`expandedCapsules: Set<string>`，key 为 `'main'` 或 `subagent_id`
  - 默认：全部展开
  - 可持久化到 sessionStorage（可选）
- **Log 展开**：沿用现有 `expandedLogs: Set<string>`

---

## 六、CollapsibleExecutionLog 浮动条适配

### 6.1 浮动条中的胶囊预览

当前浮动条显示最近 4 条 log。改为按胶囊分组预览：

- **方案 A**：仍显示最近 4 条 log，但每条前加胶囊名缩写，如 `[主] 思考...`、`[A] run_terminal_cmd...`
- **方案 B**：显示各胶囊的摘要，如 `主 Agent: 2 条 · Subagent A: 1 条 运行中`
- **方案 C**：保持 4 条 log，不区分胶囊（实现简单）

**推荐**：方案 A，改动小且信息清晰。

### 6.2 全屏/半屏模式

全屏、半屏模式下的 ExecutionLog 使用相同的胶囊结构，无需额外适配。

---

## 七、虚拟列表与性能

### 7.1 当前虚拟列表

ExecutionLog 使用 `useVirtualList`，按单条 log 做虚拟化。

### 7.2 胶囊模式下的虚拟化

**方案 A**：以胶囊为虚拟化单元
- 每个胶囊一个 virtual item
- 胶囊内 log 数量可能很多，需计算胶囊高度
- 实现复杂，需 `measureElement` 或估算高度

**方案 B**：仍以 log 为虚拟化单元，但渲染时按胶囊分组
- 虚拟列表的 item 仍是单条 log
- 渲染时在 log 外层包一层胶囊结构（同胶囊的 log 共享一个胶囊容器）
- 需要「胶囊边界」信息：哪些 index 属于同一胶囊

**方案 C**：不做虚拟化，直接渲染所有胶囊
- 胶囊数量通常不多（主 + 若干 subagent）
- 每个胶囊内 log 数量可能较多，可在胶囊内部做虚拟化
- 实现相对简单

**推荐**：Phase 1 用方案 C，胶囊数量少时性能可接受；若单胶囊内 log 过多，再为胶囊内容区加虚拟列表。

---

## 八、实施路线图

### Phase 1：基础胶囊结构（1 天）

| 任务 | 说明 |
|------|------|
| 新增 LogCapsule 组件 | 含 Header + Content，可折叠 |
| 修改 ExecutionLog | 用 groupLogsBySubagent 分组，渲染胶囊列表 |
| 胶囊折叠状态 | expandedCapsules 本地 state，默认全展开 |
| 主 Agent 命名 | 无 subagent_id 的 log 归入「主 Agent」胶囊 |

**验收**：日志按 subagent 分胶囊展示，可折叠/展开胶囊

### Phase 2：与过滤联动（0.5 天）

| 任务 | 说明 |
|------|------|
| logSubagentId 过滤 | 选中某 subagent Tab 时，只渲染该胶囊 |
| Tab 与胶囊一致 | 单胶囊时 Tab 可隐藏或简化 |

### Phase 3：浮动条与细节（0.5 天）

| 任务 | 说明 |
|------|------|
| CollapsibleExecutionLog | 预览条中每条 log 前加 `[主]`/`[A]` 等胶囊标识 |
| 胶囊折叠持久化 | 可选，存入 sessionStorage |
| 主 Agent / subagent 视觉区分 | 边框色或图标区分 |

### Phase 4：性能优化（可选）

| 任务 | 说明 |
|------|------|
| 胶囊内虚拟列表 | 单胶囊 log 数 > 50 时启用 |
| 胶囊虚拟化 | 胶囊数 > 10 时考虑 |

---

## 九、文件变更清单

| 文件 | 变更类型 |
|------|----------|
| `src/components/Visual/LogCapsule.tsx` | 新增 |
| `src/components/Visual/ExecutionLog.tsx` | 修改：分组逻辑、渲染胶囊 |
| `src/components/Visual/CollapsibleExecutionLog.tsx` | 修改：预览条加胶囊标识 |
| `src/store/index.ts` | 无变更（或扩展 expandedCapsules 持久化） |

---

## 十、边界情况

| 情况 | 处理 |
|------|------|
| 无 subagent_id 的 log | 归入「主 Agent」胶囊 |
| 仅有主 Agent 日志 | 只显示一个胶囊，可考虑不显示「主 Agent」标题，或简化样式 |
| 无日志 | 保持现有空状态 |
| subagent_id 为空字符串 | 与 undefined 同等对待，归入主 Agent |
| 胶囊内仅 1 条 log | 仍显示胶囊，标题栏可简化（如不显示折叠按钮） |

---

## 十一、附录：胶囊标题栏示意

```
主 Agent 胶囊：
┌──────────────────────────────────────────────────────────────┐
│ [Monitor] 主 Agent    3 条    运行中●    [▼]                   │
└──────────────────────────────────────────────────────────────┘

Subagent 胶囊：
┌──────────────────────────────────────────────────────────────┐
│ [Cpu] subagent-abc-123    5 条    完成    [▼]                  │
└──────────────────────────────────────────────────────────────┘
```
