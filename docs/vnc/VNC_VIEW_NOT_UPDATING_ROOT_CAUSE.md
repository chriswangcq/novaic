# VNC 画面不更新根因分析报告

## 现象

1. **同一 device 切换 subuser / maindesk**：VNC 画面不变
2. **不同 device 切换**：VNC 画面也不变

## 根因分析（4 个维度）

### 1. useVnc 过早返回，不响应 transport 变化

**位置**：`novaic-app/src/hooks/useVnc.ts` 第 86-91 行

```javascript
if (rfbRef.current) {
  rfbRef.current.viewOnly = viewOnly;
  rfbRef.current.scaleViewport = scaleViewport;
  rfbRef.current.clipViewport = clipViewport;
  return;  // ← 问题：已有 RFB 时直接返回，不检查 transport 是否变化
}
```

**原因**：当 `transport` 从 A 变为 B 时，`doConnect` 被调用，但若 `rfbRef.current` 已存在（上一次连接），会直接更新 options 并返回，**不会**关闭旧 RFB、创建新 RFB 连接新 transport。

**触发场景**：
- 同一 device 切换 subuser（subuser A → subuser B）：同一 `DeviceDesktopView` 实例，props 更新，transport 变化
- 不同 device 切换：同一 `DeviceDesktopView` 实例，`device`/`deviceId` 变化，transport 变化

### 2. 组件复用导致不 unmount

**位置**：`DeviceManagerPage.tsx` 第 864-885 行

```jsx
{effectiveSelectedDevice.type === 'linux' ? (
  selectedVmUser ? (
    <DeviceDesktopView subjectType="vm_user" ... />
  ) : (
    <DeviceDesktopView subjectType="main" ... />
  )
) : ...}
```

- **main ↔ subuser**：条件渲染不同分支，会 unmount/remount，理论上会重新连接
- **subuser A ↔ subuser B**：同一 `vm_user` 分支，仅 `username` 变化，**React 复用同一实例**，不 unmount
- **device A ↔ device B**：同一分支（main 或 vm_user），仅 `device`/`deviceId` 变化，**React 复用同一实例**，不 unmount

**结论**：在 device 切换、subuser 切换时，`DeviceDesktopView` 和 `VncCanvas`/`useVnc` 不会 unmount，`rfbRef` 保持旧实例。

### 3. vncTransport 缓存不会导致此问题

**位置**：`vncTransport.ts` 第 24-26 行

```javascript
function cacheKey(target: VncTarget): string {
  return `${target.resourceId}|${target.username}|${target.pcClientId ?? ''}`;
}
```

- maindesk：`username=''`
- subuser：`username='alice'`
- 不同 device：`resourceId` 不同

cacheKey 不同，不会复用错误 transport。问题不在缓存。

### 4. DeviceFloatingPanel 的 DeviceCard 行为

**位置**：`DeviceFloatingPanel.tsx` DeviceCard

每个 subject（main 或 vm_user）一个 DeviceCard，展开时渲染 `DeviceDesktopView`。切换展开的卡片时，会 unmount 上一个、mount 下一个，理论上会重新连接。但若 Agent 只有一个 binding，则只有一个 DeviceCard，不存在“切换 subuser”的场景。

**结论**：DeviceFloatingPanel 中，切换不同卡片会 unmount/remount，理论上正常。问题主要在 DeviceManagerPage 的 device/subuser 切换。

---

## 修复方案

**核心**：在 `useVnc` 的 `doConnect` 中，当 `transport` 变化时，必须断开旧连接并建立新连接。

**修改**：在 `useVnc.ts` 中，当 `transport !== lastTransportRef.current` 时，不执行“已有 RFB 则只更新 options”的 early return，而是先 disconnect 再 connect。
