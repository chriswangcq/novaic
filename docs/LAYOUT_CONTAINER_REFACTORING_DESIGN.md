# LayoutContainer 接入重构设计方案

> 将 App 主布局迁移至 LayoutContainer，确保效果一致或更好。基于 4 名 subagent 调研结论汇总。

---

## 一、目标与原则

| 目标 | 说明 |
|------|------|
| **效果一致** | 重构后布局、拖拽、响应式行为与当前实现完全一致 |
| **效果更好** | 布局逻辑集中、职责清晰、易维护扩展 |
| **零破坏** | Setup 页面、Header、Footer、SettingsModal 不受影响 |

---

## 二、调研结论汇总

### 2.1 调研员 1：App 与 LayoutContainer 接入点

| 结论 | 详情 |
|------|------|
| App 当前 DOM | `Header` → `div(AgentDrawer \| main(ChatPanel \| Resizer \| DeviceSidebar))` → `SettingsModal` → `footer` |
| LayoutContainer DOM | `div(AgentDrawer \| Resizer \| main(ChatPanel \| Resizer \| DeviceSidebar))`，不含 Header/Footer |
| 需传入 props | drawerWidth, sidebarWidth, drawerOpen, sidebarMode, onDrawerResize, onSidebarResize, onDrawerClose, onDrawerDoubleClick, onSidebarDoubleClick, onSelectAgent, onCreateNew |
| 代码量变化 | 净减少约 10 行（迁移后验证：App 主内容区从约 30 行减至约 15 行） |
| Setup 页面 | 不受影响，仍独立渲染 SetupWorkspace + AgentDrawer |

### 2.2 调研员 2：AgentDrawer Resizer 去重

| 结论 | 详情 |
|------|------|
| 重复问题 | AgentDrawer 在 lg 以上且 isOpen 时渲染内部 Resizer；LayoutContainer 也在 Drawer 与 main 之间渲染 Resizer，会重复 |
| 推荐方案 | **方案 A**：给 AgentDrawer 增加 `resizerPlacement?: 'internal' \| 'external'`，默认 `'internal'` |
| 实现要点 | `resizerPlacement === 'external'` 时不渲染内部 Resizer，由 LayoutContainer 提供 |
| Setup 页面 | 保持默认 `internal`，lg 以上仍可拖拽 Drawer |
| Drawer Resizer 条件 | LayoutContainer 的 Drawer Resizer 应增加 `useIsLgOrAbove()` 判断，与 overlay 逻辑一致 |

### 2.3 调研员 3：DeviceSidebar 与 Sidebar Resizer

| 结论 | 详情 |
|------|------|
| overlay 判断 | `isOverlay = !useIsLgOrAbove()`，lg 以下为 overlay |
| overlay 时 Resizer | DeviceSidebar 为 fixed 浮层，不占 flex 流，Resizer 拖拽无意义 |
| 当前 LayoutContainer 问题 | 只判断 `sidebarMode !== 'hidden'`，缺少 `isLgOrAbove`，lg 以下会错误渲染 Resizer |
| 推荐实现 | LayoutContainer 内部使用 `useIsLgOrAbove()`，条件改为 `isLgOrAbove && sidebarMode !== 'hidden'` |
| hidden 时 | 0px 占位 + 浮动按钮，不应渲染 Resizer |

### 2.4 调研员 4：Store、状态流与边界情况

| 结论 | 详情 |
|------|------|
| onDrawerResize | `(delta) => setDrawerWidth(useAppStore.getState().drawerWidth + delta)`，store 已做 clamp |
| onSidebarResize | 同上，用 setSidebarWidth |
| onDrawerDoubleClick | `() => setDrawerWidth(LAYOUT_CONFIG.DRAWER_WIDTH)` |
| onSidebarDoubleClick | `() => setSidebarWidth(LAYOUT_CONFIG.SIDEBAR_WIDTH)` |
| persistLayout | 无需改动，仍由 setDrawerWidth/setSidebarWidth 触发 |
| drawerOpen=false | Drawer 宽度 0，Resizer 不渲染，行为正确 |

---

## 三、改动清单

### 3.1 文件级改动

| 文件 | 改动类型 | 说明 |
|------|----------|------|
| `App.tsx` | 修改 | 用 LayoutContainer 替换主内容区，补充 store 解构与 props |
| `LayoutContainer.tsx` | 修改 | 增加 useIsLgOrAbove、Drawer Resizer 的 lg 条件、Sidebar Resizer 的 lg 条件 |
| `AgentDrawer.tsx` | 修改 | 增加 resizerPlacement prop，external 时不渲染内部 Resizer |
| `store/index.ts` | 无 | 已有 drawerWidth、setDrawerWidth 及持久化 |
| `config/index.ts` | 无 | LAYOUT_CONFIG 已满足需求 |

### 3.2 不改动的部分

| 部分 | 说明 |
|------|------|
| Setup 页面 | 仍渲染 SetupWorkspace + AgentDrawer，不经过 LayoutContainer |
| Header | 仍由 App 渲染，props 不变 |
| Footer | 仍由 App 渲染 |
| SettingsModal | 仍由 App 控制 |
| ChatPanel | 无改动 |
| DeviceSidebar | 无改动 |
| Resizer | 无改动 |

---

## 四、详细设计

### 4.1 AgentDrawer 改动

**文件**：`novaic-app/src/components/Layout/AgentDrawer.tsx`

**新增 prop**：

```typescript
interface AgentDrawerProps {
  // ... 现有 props
  /** Resizer 由谁提供：internal=组件内部，external=由父组件（如 LayoutContainer）提供。默认 internal */
  resizerPlacement?: 'internal' | 'external';
}
```

**修改逻辑**：

- 挤占式分支（lg 以上）中，原 `{isOpen && <Resizer ... />}` 改为：
  ```tsx
  {resizerPlacement !== 'external' && isOpen && <Resizer ... />}
  ```
- 默认值：`resizerPlacement = 'internal'`

**调用点**：

| 调用点 | resizerPlacement | 说明 |
|--------|------------------|------|
| App.tsx Setup | 不传（默认 internal） | Setup 页面保留 Drawer 拖拽 |
| LayoutContainer | `resizerPlacement="external"` | 由 LayoutContainer 提供 Resizer |

---

### 4.2 LayoutContainer 改动

**文件**：`novaic-app/src/components/Layout/LayoutContainer.tsx`

**新增**：

1. 引入 `useIsLgOrAbove`
2. Drawer Resizer 条件：`drawerOpen && isLgOrAbove`（lg 以下 Drawer 为 overlay，无需 Resizer）
3. Sidebar Resizer 条件：`isLgOrAbove && sidebarMode !== 'hidden'`
4. AgentDrawer 传入 `resizerPlacement="external"`

**修改后结构**：

```tsx
export function LayoutContainer({ ... }) {
  const isLgOrAbove = useIsLgOrAbove();

  return (
    <div className="flex-1 flex overflow-hidden" style={{ ... }}>
      <AgentDrawer
        resizerPlacement="external"
        isOpen={drawerOpen}
        onClose={onDrawerClose}
        onSelectAgent={onSelectAgent}
        onCreateNew={onCreateNew}
      />

      {drawerOpen && isLgOrAbove && (
        <Resizer
          axis="horizontal"
          onResize={onDrawerResize}
          onDoubleClick={onDrawerDoubleClick ?? (() => {})}
        />
      )}

      <main className="flex-1 flex overflow-hidden min-w-0">
        <div className="flex-1 flex flex-col overflow-hidden min-w-0">
          <ChatPanel />
        </div>

        {isLgOrAbove && sidebarMode !== 'hidden' && (
          <Resizer
            axis="horizontal"
            onResize={onSidebarResize}
            onDoubleClick={onSidebarDoubleClick ?? (() => {})}
          />
        )}

        <DeviceSidebar sidebarWidth={sidebarWidth} />
      </main>
    </div>
  );
}
```

---

### 4.3 App.tsx 改动

**文件**：`novaic-app/src/App.tsx`

**解构补充**：

```tsx
const {
  // ... 现有
  drawerWidth,
  setDrawerWidth,
  drawerOpen,
  setDrawerOpen,
  sidebarWidth,
  setSidebarWidth,
  sidebarMode,
} = useAppStore();
```

**主内容区替换**：

原：

```tsx
<div className="flex-1 flex overflow-hidden">
  <AgentDrawer ... />
  <main className="flex-1 flex overflow-hidden">
    <div><ChatPanel /></div>
    {isLgOrAbove && sidebarMode !== 'hidden' && <Resizer ... />}
    <DeviceSidebar ... />
  </main>
</div>
```

改为：

```tsx
<LayoutContainer
  drawerWidth={drawerWidth}
  sidebarWidth={sidebarWidth}
  drawerOpen={drawerOpen}
  sidebarMode={sidebarMode}
  onDrawerResize={(delta) => setDrawerWidth(useAppStore.getState().drawerWidth + delta)}
  onSidebarResize={(delta) => setSidebarWidth(useAppStore.getState().sidebarWidth + delta)}
  onDrawerClose={() => setDrawerOpen(false)}
  onDrawerDoubleClick={() => setDrawerWidth(LAYOUT_CONFIG.DRAWER_WIDTH)}
  onSidebarDoubleClick={() => setSidebarWidth(LAYOUT_CONFIG.SIDEBAR_WIDTH)}
  onSelectAgent={handleSelectAgent}
  onCreateNew={() => setCreateAgentModalOpen(true)}
/>
```

**import 变更**：

- 新增：`LayoutContainer`、`LAYOUT_CONFIG`
- 移除：`Resizer`（若不再直接使用）
- 保留或移除：`useIsLgOrAbove`（App 若不再需要可移除，LayoutContainer 内部使用）

---

## 五、效果一致性检查表

| 场景 | 当前行为 | 重构后行为 | 一致性 |
|------|----------|------------|--------|
| lg 以上，Drawer 打开 | Drawer 可拖拽，有 Resizer | LayoutContainer 提供 Resizer，AgentDrawer 不渲染内部 | ✓ |
| lg 以上，Drawer 关闭 | Drawer 宽度 0，无 Resizer | 同上 | ✓ |
| lg 以下，Drawer | overlay 浮层，无 Resizer | overlay 不变，LayoutContainer 不渲染 Drawer Resizer | ✓ |
| lg 以上，Sidebar 非 hidden | Sidebar 可拖拽 | LayoutContainer 渲染 Resizer | ✓ |
| lg 以下，Sidebar | overlay，无 Resizer | LayoutContainer 不渲染 Resizer | ✓ |
| sidebarMode=hidden | 无 Resizer | LayoutContainer 不渲染 Resizer | ✓ |
| Setup 页面 | AgentDrawer 独立，lg 以上可拖拽 | 不变，resizerPlacement 默认 internal | ✓ |
| 双击恢复 | Drawer/Sidebar 恢复默认宽度 | onDrawerDoubleClick/onSidebarDoubleClick 传入 | ✓ |
| 持久化 | 300ms 防抖 + beforeunload | 不变，仍由 store 触发 | ✓ |

---

## 六、注意事项

### 6.1 必须注意

| 项 | 说明 |
|----|------|
| getState() 获取最新值 | onDrawerResize、onSidebarResize 必须用 `useAppStore.getState().drawerWidth` 等，避免闭包陈旧 |
| Setup 页面不传 resizerPlacement | 保持默认 internal，否则 Setup 页面 lg 以上无法拖拽 Drawer |
| LayoutContainer 的 Drawer Resizer 条件 | 必须同时满足 `drawerOpen && isLgOrAbove`，否则 lg 以下会出现无意义 Resizer |

### 6.2 可选优化

| 项 | 说明 |
|----|------|
| onDrawerDoubleClick 默认值 | LayoutContainer 可提供默认实现 `() => setDrawerWidth(LAYOUT_CONFIG.DRAWER_WIDTH)`，减少 App 传参 |
| 文档注释 | 在 LayoutContainer、AgentDrawer 中补充 resizerPlacement、isLgOrAbove 的说明 |

---

## 七、实施顺序

1. **Step 1**：修改 AgentDrawer，增加 `resizerPlacement` prop
2. **Step 2**：修改 LayoutContainer，增加 useIsLgOrAbove、条件判断、resizerPlacement="external"
3. **Step 3**：修改 App.tsx，用 LayoutContainer 替换主内容区
4. **Step 4**：手动验证：lg 以上/以下、Drawer 开/关、Sidebar 各档位、Setup 页面
5. **Step 5**：运行 `npm run build` 确保构建通过

---

## 八、回滚方案

若重构后发现问题，可快速回滚：

1. App.tsx 恢复为内联布局（保留 LayoutContainer 的改动或还原）
2. AgentDrawer 的 resizerPlacement 默认 internal，不影响现有调用
3. LayoutContainer 可保留作为备用，不影响运行

---

## 九、附录：关键代码引用

| 内容 | 文件:行号 |
|------|-----------|
| App 主布局 | App.tsx:304-334 |
| AgentDrawer 挤占式 + Resizer | AgentDrawer.tsx:213-230 |
| LayoutContainer 结构 | LayoutContainer.tsx:41-84 |
| setDrawerWidth clamp | store/index.ts:734-738 |
| setSidebarWidth clamp | store/index.ts:541-545 |
| DeviceSidebar isOverlay | DeviceSidebar.tsx:318-319 |
| useIsLgOrAbove | useMediaQuery.ts:39-41 |
