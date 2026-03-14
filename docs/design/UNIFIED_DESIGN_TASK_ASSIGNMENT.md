# NovAIC 布局与 Execution Log 变更 - 分工文档

> 4 名前端工程师，Phase 1~5 详细任务分工

---

## 一、人员与角色

| 工程师 | 代号 | 主责领域 | 备注 |
|--------|------|----------|------|
| 工程师 A | A | 布局容器、Resizer、断点 | 负责核心布局基础设施 |
| 工程师 B | B | 设计系统、DeviceSidebar、Agent 相关 | 负责视觉与侧边栏 |
| 工程师 C | C | Execution Log、CollapsibleExecutionLog | 负责日志展示与胶囊 |
| 工程师 D | D | 状态管理、持久化、ChatPanel | 负责 Store 与主内容区 |

---

## 二、Phase 1：基础设施（1 天）

**前置**：无  
**产出**：Resizer 可用、设计 token 可用、布局状态可持久化、Header/Footer 统一

### 2.1 工程师 A：Resizer 扩展

| 序号 | 任务 | 说明 | 产出物 |
|------|------|------|--------|
| A1.1 | 扩展 Resizer 支持 axis | 新增 `axis: 'horizontal' \| 'vertical'`，水平用 `clientX`，垂直用 `clientY` | Resizer.tsx |
| A1.2 | 实现 RAF 节流 | mousemove 中用 `requestAnimationFrame` 节流，避免高频更新 | Resizer.tsx |
| A1.3 | 垂直模式样式 | `axis=vertical` 时 `cursor-row-resize`，拖拽区域 `h-1`、悬停 `h-2` | Resizer.tsx |
| A1.4 | 单元/手动测试 | 水平、垂直拖拽、双击恢复均正常 | - |

**依赖**：无  
**被依赖**：Phase 2 的 B、C；Phase 3 的 D

---

### 2.2 工程师 B：Tailwind Token 补全

| 序号 | 任务 | 说明 | 产出物 |
|------|------|------|--------|
| B1.1 | 补全 nb-surface-hover | `#1c2128`，与 hover 对齐 | tailwind.config.js |
| B1.2 | 补全 nb-border-hover | `#484f58` | tailwind.config.js |
| B1.3 | 补全 nb-card | `#161b22` | tailwind.config.js |
| B1.4 | 全局替换未定义 token | 搜索 `nb-surface-hover`、`nb-border-hover`、`nb-card` 使用处，确保无 fallback 失效 | 相关组件 |

**依赖**：无  
**被依赖**：全项目

---

### 2.3 工程师 C：Header/Footer 高度统一

| 序号 | 任务 | 说明 | 产出物 |
|------|------|------|--------|
| C1.1 | 主工作区 Header | 确认 App.tsx 中 Header 为 `h-10` | App.tsx |
| C1.2 | SetupWorkspace Header | 将 `h-14` 改为 `h-10` | SetupWorkspace.tsx |
| C1.3 | AgentDashboard Header/Footer | 若有，统一为 `h-10`、`h-6` | AgentDashboard.tsx |
| C1.4 | Footer 统一 | 确认主工作区 Footer 为 `h-6`，其他页面若有 Footer 统一 | 相关文件 |
| C1.5 | 文档更新 | 在 design doc 中记录统一规范 | - |

**依赖**：无  
**被依赖**：无

---

### 2.4 工程师 D：布局状态与持久化

| 序号 | 任务 | 说明 | 产出物 |
|------|------|------|--------|
| D1.1 | 定义 LayoutPersistence 类型 | 见统一方案第三节，含 version | types/index.ts |
| D1.2 | 定义 LayoutState 类型 | 含 drawerWidth、sidebarWidth、logHeightRatio 等 | types/index.ts |
| D1.3 | 扩展 LAYOUT_CONFIG | 增加 sidebarWidth、sidebarMin/Max、logHeightRatio 等默认值 | config/index.ts |
| D1.4 | 实现 loadLayoutSettings | 从 localStorage 读取 `novaic-layout-v2`，校验 version 和范围 | store/index.ts |
| D1.5 | 实现 saveLayoutSettings | 防抖 300ms 写入，mouseup 时立即写入 | store/index.ts |
| D1.6 | Store 中挂载布局状态 | 将 drawerWidth、sidebarWidth、drawerOpen 等接入 store（可先占位，Phase 2 真正使用） | store/index.ts |

**依赖**：无  
**被依赖**：Phase 2 的 A、B、C、D；Phase 3 的 D

---

### Phase 1 验收标准

- [ ] Resizer 支持水平/垂直，RAF 节流生效
- [ ] `nb-surface-hover`、`nb-border-hover`、`nb-card` 可用
- [ ] Setup/主工作区 Header 均为 h-10，Footer 均为 h-6
- [ ] `loadLayoutSettings`、`saveLayoutSettings` 可读写 `novaic-layout-v2`

---

## 三、Phase 2：三栏可拖拽（1-2 天）

**前置**：Phase 1 完成  
**产出**：用户可拖拽调整 Drawer、Sidebar 宽度，刷新后保持

### 3.1 工程师 A：LayoutContainer 与 Drawer Resizer

| 序号 | 任务 | 说明 | 产出物 |
|------|------|------|--------|
| A2.1 | 新增 LayoutContainer | 接收 drawerWidth、sidebarWidth、onDrawerResize、onSidebarResize | LayoutContainer.tsx |
| A2.2 | 渲染三栏结构 | AgentDrawer | Resizer | main(ChatPanel | Resizer | DeviceSidebar) | LayoutContainer.tsx |
| A2.3 | Drawer 与 Main 之间 Resizer | 水平 Resizer，onResize 更新 drawerWidth，约束 200-400 | LayoutContainer.tsx |
| A2.4 | 宽度用 CSS 变量 | 使用 `--drawer-width`、`--sidebar-width` 减少重渲染 | LayoutContainer.tsx |
| A2.5 | 接入 App.tsx | 用 LayoutContainer 包裹主内容，传入 store 的布局状态与 actions | App.tsx |

**依赖**：A1（Resizer）、D1（load/save）  
**被依赖**：B2、C2

---

### 3.2 工程师 B：ChatPanel-Sidebar Resizer 与 DeviceSidebar 宽度

| 序号 | 任务 | 说明 | 产出物 |
|------|------|------|--------|
| B2.1 | Main 内 Resizer | 在 ChatPanel 与 DeviceSidebar 之间插入水平 Resizer | LayoutContainer.tsx |
| B2.2 | Sidebar 宽度约束 | 180-400px，双击恢复 208 | LayoutContainer.tsx |
| B2.3 | DeviceSidebar 使用动态宽度 | 从 props 或 context 读取 sidebarWidth，替代固定 w-52 | DeviceSidebar.tsx |
| B2.4 | 拖拽反馈 | Resizer 悬停、拖拽中视觉反馈符合设计规范 | Resizer.tsx（与 A 协作） |

**依赖**：A2（LayoutContainer 结构）、A1（Resizer）  
**被依赖**：无

---

### 3.3 工程师 C：drawerOpen 与 AgentDrawer 宽度

| 序号 | 任务 | 说明 | 产出物 |
|------|------|------|--------|
| C2.1 | drawerOpen 从 store 读取 | AgentDrawer 的 isOpen 来自 store.layoutState.drawerOpen | App.tsx / AgentDrawer |
| C2.2 | drawerOpen 持久化 | setDrawerOpen 时调用 saveLayoutSettings | store/index.ts |
| C2.3 | Drawer 宽度与展开联动 | drawerOpen=false 时 width=0，open 时用 drawerWidth | LayoutContainer.tsx |
| C2.4 | 启动时恢复 drawerOpen | loadLayoutSettings 后 set 到 store | store/index.ts |

**依赖**：D1（load/save）、A2（LayoutContainer）  
**被依赖**：无

---

### 3.4 工程师 D：持久化与 Store 打通

| 序号 | 任务 | 说明 | 产出物 |
|------|------|------|--------|
| D2.1 | Store 中布局 actions | setDrawerWidth、setSidebarWidth、setDrawerOpen，并触发 save | store/index.ts |
| D2.2 | 拖拽结束写入 | Resizer onMouseUp 时调用 setDrawerWidth/setSidebarWidth，由 store 统一 save | store/index.ts |
| D2.3 | 启动时恢复宽度 | initialize 或 mount 时 loadLayoutSettings，set 到 store | store/index.ts |
| D2.4 | 范围校验 | load 时 clamp 到 MIN-MAX，异常时回退默认值 | store/index.ts |

**依赖**：D1、A2、B2  
**被依赖**：全 Phase 2

---

### Phase 2 验收标准

- [ ] 拖拽 Drawer 与 Main 之间的 Resizer，Drawer 宽度变化，约束 200-400
- [ ] 拖拽 ChatPanel 与 Sidebar 之间的 Resizer，Sidebar 宽度变化，约束 180-400
- [ ] 刷新后 Drawer、Sidebar 宽度恢复
- [ ] drawerOpen 刷新后恢复

---

## 四、Phase 3：Execution Log 胶囊 + 增强（1.5-2 天）

**前置**：Phase 1、Phase 2 完成  
**产出**：日志按 subagent 分胶囊、可折叠、半屏可调高度、按钮常显

### 4.1 工程师 A：LogCapsule 组件

| 序号 | 任务 | 说明 | 产出物 |
|------|------|------|--------|
| A3.1 | 新增 LogCapsule.tsx | 接收 capsuleId、displayName、isMain、logs、isExpanded、onToggleExpand 等 | LogCapsule.tsx |
| A3.2 | LogCapsuleHeader | 图标、名称、条数、状态（运行中/失败）、折叠按钮 | LogCapsule.tsx |
| A3.3 | LogCapsuleContent | 渲染 LogCard 列表，传入 expandedLogs、onToggleLogExpand | LogCapsule.tsx |
| A3.4 | 主 Agent / subagent 视觉区分 | 主 Agent `border-l-blue-500/50`，subagent `border-l-violet-500/50` | LogCapsule.tsx |
| A3.5 | 胶囊样式 | rounded-xl、border、bg-nb-surface/80 | LogCapsule.tsx |

**依赖**：无  
**被依赖**：B3（ExecutionLog 使用）

---

### 4.2 工程师 B：ExecutionLog 分组与胶囊渲染

| 序号 | 任务 | 说明 | 产出物 |
|------|------|------|--------|
| B3.1 | groupLogsBySubagent | 实现分组函数，key 为 'main' \| subagent_id | ExecutionLog.tsx |
| B3.2 | 胶囊排序 | 主 Agent 第一，subagent 按首条 log timestamp 升序 | ExecutionLog.tsx |
| B3.3 | 渲染胶囊列表 | 遍历分组结果，为每个胶囊渲染 LogCapsule | ExecutionLog.tsx |
| B3.4 | logSubagentId 过滤 | 选中某 subagent Tab 时只渲染该胶囊 | ExecutionLog.tsx |
| B3.5 | expandedCapsules 状态 | 本地 state 或从 store 读取，默认全展开 | ExecutionLog.tsx |
| B3.6 | Tab 与胶囊联动 | 单胶囊时 Tab 可隐藏或简化 | ExecutionLog.tsx |

**依赖**：A3（LogCapsule）  
**被依赖**：无

---

### 4.3 工程师 C：CollapsibleExecutionLog 增强

| 序号 | 任务 | 说明 | 产出物 |
|------|------|------|--------|
| C3.1 | 按钮常显 | 展开、全屏按钮移除 isHovered 依赖，始终可见 | CollapsibleExecutionLog.tsx |
| C3.2 | 预览条胶囊标识 | 每条 log 前加 `[主]` 或 `[A]`（subagent 缩写） | CollapsibleExecutionLog.tsx |
| C3.3 | 胶囊缩写逻辑 | main→`[主]`，subagent_id→取首字符或短 id | CollapsibleExecutionLog.tsx |
| C3.4 | 全屏 Modal 使用胶囊 | FullLogModal 内 ExecutionLog 已支持胶囊，无需额外改动 | CollapsibleExecutionLog.tsx |

**依赖**：B3（ExecutionLog 已有胶囊结构）  
**被依赖**：无

---

### 4.4 工程师 D：ChatPanel 半屏 Resizer 与胶囊持久化

| 序号 | 任务 | 说明 | 产出物 |
|------|------|------|--------|
| D3.1 | 半屏垂直 Resizer | 在 MessageList 与 ExecutionLog 之间插入垂直 Resizer | ChatPanel.tsx |
| D3.2 | logHeightRatio 状态 | 0.3~0.7，默认 0.5，拖拽更新 | ChatPanel.tsx |
| D3.3 | logHeightRatio 持久化 | 存入 LayoutPersistence，load 时恢复 | store/index.ts |
| D3.4 | 双击 Resizer 恢复 50% | onDoubleClick 重置 logHeightRatio | ChatPanel.tsx |
| D3.5 | 胶囊折叠持久化（可选） | expandedCapsules 存入 LayoutPersistence | store/index.ts、ExecutionLog.tsx |

**依赖**：A1（Resizer 垂直）、D1（LayoutPersistence）  
**被依赖**：无

---

### Phase 3 验收标准

- [ ] 日志按 subagent 分胶囊展示，主 Agent 胶囊在前
- [ ] 胶囊可折叠/展开
- [ ] 选中 subagent Tab 时只显示该胶囊
- [ ] CollapsibleExecutionLog 展开、全屏按钮始终可见
- [ ] 预览条每条 log 前有 `[主]` 或 subagent 缩写
- [ ] 半屏 Log 与 MessageList 之间可拖拽调整高度，刷新后保持

---

## 五、Phase 4：DeviceSidebar + 响应式（1 天）

**前置**：Phase 1、2、3 完成  
**产出**：DeviceSidebar 可折叠、小屏布局正常

### 4.1 工程师 A：useBreakpoint Hook

| 序号 | 任务 | 说明 | 产出物 |
|------|------|------|--------|
| A4.1 | 新增 useBreakpoint | 监听 window.resize，返回 'xl' \| 'lg' \| 'md' \| 'sm' | hooks/useBreakpoint.ts |
| A4.2 | 断点定义 | xl≥1280, lg≥1024, md≥768, sm<768 | hooks/useBreakpoint.ts |
| A4.3 | 防抖/节流 | resize 时避免频繁计算 | hooks/useBreakpoint.ts |

**依赖**：无  
**被依赖**：B4、C4、D4

---

### 4.2 工程师 B：DeviceSidebar 标题与档位

| 序号 | 任务 | 说明 | 产出物 |
|------|------|------|--------|
| B4.1 | 标题显示 Agent 名 | `{currentAgent?.name ?? '当前'} 的设备` | DeviceSidebar.tsx |
| B4.2 | 预设档位状态 | expanded / collapsed / hidden，collapsed 时 48px | DeviceSidebar.tsx |
| B4.3 | 档位切换按钮 | 标题栏右侧折叠、隐藏按钮（小屏显示隐藏） | DeviceSidebar.tsx |
| B4.4 | 无设备时收缩 | 无设备时默认 collapsed，显示「+ 添加设备」 | DeviceSidebar.tsx |

**依赖**：A4（useBreakpoint，用于判断是否显示隐藏按钮）  
**被依赖**：无

---

### 4.3 工程师 C：md 断点布局

| 序号 | 任务 | 说明 | 产出物 |
|------|------|------|--------|
| C4.1 | md 以下 Drawer overlay | 使用 fixed/absolute 浮层，带遮罩，点击遮罩关闭 | App.tsx / LayoutContainer |
| C4.2 | md 以下 Sidebar 默认折叠 | breakpoint 为 md/sm 时 sidebarCollapsed 默认 true | LayoutContainer / store |
| C4.3 | Sidebar 折叠态 UI | 48px 宽，仅显示图标，点击展开 | DeviceSidebar.tsx |

**依赖**：A4、B4  
**被依赖**：无

---

### 4.4 工程师 D：sm 断点布局

| 序号 | 任务 | 说明 | 产出物 |
|------|------|------|--------|
| D4.1 | sm 以下单栏 | 只显示 ChatPanel，Drawer 和 Sidebar 均为 overlay | App.tsx / LayoutContainer |
| D4.2 | Sidebar overlay | sm 时 Sidebar 从右侧滑入，全屏宽或大部分宽 | DeviceSidebar.tsx |
| D4.3 | 小屏禁用拖拽 | sm/md 时 Resizer 不渲染或禁用 | LayoutContainer.tsx |
| D4.4 | 触摸友好 | overlay 关闭区域足够大，避免误触 | 相关组件 |

**依赖**：A4、C4  
**被依赖**：无

---

### Phase 4 验收标准

- [ ] useBreakpoint 正确返回 xl/lg/md/sm
- [ ] DeviceSidebar 标题显示「{Agent} 的设备」
- [ ] DeviceSidebar 可折叠为 48px 图标栏
- [ ] md 以下 Drawer 为 overlay，Sidebar 默认折叠
- [ ] sm 以下单栏，Drawer/Sidebar 均为 overlay

---

## 六、Phase 5：优化与收尾（可选）

**前置**：Phase 1~4 完成  
**产出**：LayoutMode 处理、快速切换、虚拟列表、无障碍

### 6.1 工程师 A：LayoutMode 整合或移除

| 序号 | 任务 | 说明 | 产出物 |
|------|------|------|--------|
| A5.1 | 评估 LayoutMode 使用 | 检查 layoutMode、LayoutToggle 是否被引用 | - |
| A5.2 | 决策：整合或移除 | 若保留，将 full/normal/mini 与当前布局打通；若移除，删除相关代码 | store、LayoutToggle、相关组件 |
| A5.3 | 清理未用状态 | 移除或标记 deprecated | store/index.ts |

**依赖**：Phase 2~4  
**被依赖**：无

---

### 6.2 工程师 B：Header 快速切换 Agent

| 序号 | 任务 | 说明 | 产出物 |
|------|------|------|--------|
| B5.1 | Header 下拉/左右箭头 | 当前 Agent 名称旁增加切换控件 | Header.tsx |
| B5.2 | 最近 Agent 列表 | 从 store.agents 取最近使用的 3~5 个 | Header.tsx |
| B5.3 | 点击切换 | 调用 selectAgent，无需打开 Drawer | Header.tsx |

**依赖**：无  
**被依赖**：无

---

### 6.3 工程师 C：胶囊内虚拟列表

| 序号 | 任务 | 说明 | 产出物 |
|------|------|------|--------|
| C5.1 | 判断条件 | 单胶囊 log 数 > 50 时启用 | LogCapsule.tsx |
| C5.2 | 胶囊内 useVirtualList | LogCapsuleContent 内对 logs 做虚拟化 | LogCapsule.tsx |
| C5.3 | 高度估算 | LOG_ESTIMATE_SIZE 复用或调整 | constants/scroll.ts |

**依赖**：A3、B3  
**被依赖**：无

---

### 6.4 工程师 D：无障碍

| 序号 | 任务 | 说明 | 产出物 |
|------|------|------|--------|
| D5.1 | Resizer 键盘支持 | 方向键微调宽度/高度，Enter 确认 | Resizer.tsx |
| D5.2 | ARIA 标签 | 按钮 aria-label，状态 aria-live | Resizer、LogCapsule、DeviceSidebar |
| D5.3 | 焦点 trap | Modal 打开时 trap focus，关闭回退 | CollapsibleExecutionLog FullLogModal |
| D5.4 | 对比度检查 | text-nb-text-muted 等与背景对比度满足 WCAG AA | tailwind / 组件 |

**依赖**：Phase 1~4  
**被依赖**：无

---

### Phase 5 验收标准

- [ ] LayoutMode 已整合或移除，无死代码
- [ ] Header 可快速切换 Agent
- [ ] 单胶囊 >50 条时使用虚拟列表
- [ ] Resizer 支持键盘，ARIA 完善，Modal 焦点正确

---

## 七、依赖关系与协作点

### 7.1 跨 Phase 依赖

```
Phase 1
  A(Resizer) ──┬──> Phase 2: B(Sidebar Resizer), A(Drawer Resizer)
  D(持久化) ───┼──> Phase 2: A,B,C,D
               └──> Phase 3: D(半屏 Resizer, 胶囊持久化)

Phase 2
  A(LayoutContainer) ──> Phase 3: D(ChatPanel 半屏)
  A(Resizer) ─────────> Phase 3: D(垂直 Resizer)

Phase 3
  A(LogCapsule) ──────> Phase 3: B(ExecutionLog 渲染)
  B(ExecutionLog) ────> Phase 3: C(CollapsibleExecutionLog 预览)

Phase 4
  A(useBreakpoint) ───> Phase 4: B,C,D(断点布局)
```

### 7.2 需联调的场景

| 场景 | 负责人 | 协作方 |
|------|--------|--------|
| Resizer 接入 LayoutContainer | A | B |
| Store 布局状态与 LayoutContainer 打通 | D | A |
| ChatPanel 半屏 Resizer 与 logHeightRatio | D | A（Resizer） |
| 断点变化时 Drawer/Sidebar 行为 | C, D | A, B |

### 7.3 代码评审建议

- Phase 1 结束：A 的 Resizer、D 的持久化由 B/C 做 CR
- Phase 2 结束：A 的 LayoutContainer 由 B/C/D 做 CR
- Phase 3 结束：B 的 ExecutionLog 分组逻辑由 A/C 做 CR
- Phase 4 结束：C/D 的断点布局由 A/B 做 CR

---

## 八、时间与里程碑

| 里程碑 | 目标日期 | 验收 |
|--------|----------|------|
| M1：Phase 1 完成 | Day 1 | Resizer、token、持久化、Header 统一 |
| M2：Phase 2 完成 | Day 2~3 | 三栏可拖拽、刷新保持 |
| M3：Phase 3 完成 | Day 4~5 | 胶囊、半屏 Resizer、按钮常显 |
| M4：Phase 4 完成 | Day 6 | DeviceSidebar 档位、响应式 |
| M5：Phase 5 完成 | Day 7~8（可选） | 优化与收尾 |

---

## 九、附录：任务-人员矩阵

| Phase | 工程师 A | 工程师 B | 工程师 C | 工程师 D |
|-------|----------|----------|----------|----------|
| 1 | Resizer 扩展 | Tailwind token | Header/Footer 统一 | 布局状态与持久化 |
| 2 | LayoutContainer、Drawer Resizer | Sidebar Resizer、DeviceSidebar 宽度 | drawerOpen 持久化 | Store 持久化打通 |
| 3 | LogCapsule | ExecutionLog 分组与胶囊 | CollapsibleExecutionLog 增强 | ChatPanel 半屏 Resizer |
| 4 | useBreakpoint | DeviceSidebar 标题与档位 | md 断点布局 | sm 断点布局 |
| 5 | LayoutMode | Header 快速切换 | 胶囊内虚拟列表 | 无障碍 |
