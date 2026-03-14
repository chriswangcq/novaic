# NovAIC iOS 黑屏问题报告

## 改动总结（给大哥看的）

### 一、构建流程改动（`package.json`）

**之前**（自定义脚本）：
```json
"tauri:build:ios": "npm run build && ... && cp dist/* src-tauri/gen/apple/ && cp -r dist/assets/* ... && (cd ... && xcodegen generate) && tauri ios build -- --no-default-features --features custom-protocol,mobile"
```
- 手动复制 dist 到 gen/apple
- 用 xcodegen 重新生成 Xcode 项目
- 使用 `--no-default-features`

**现在**（标准 Tauri 流程 + mobile features）：
```json
"tauri:build:ios": "... tauri ios build -- --no-default-features --features custom-protocol,mobile",
"tauri:build:ios:debug": "... tauri ios build --debug -- --no-default-features --features custom-protocol,mobile",
"tauri:open:ios": "open src-tauri/gen/apple/novaic.xcodeproj"
```
- **关键**：与 Android 一致，使用 `--no-default-features --features custom-protocol,mobile`，避免 desktop feature 在 iOS 上干扰
- 不再手动复制，不再用 xcodegen
- 使用标准 `tauri ios build`，由 Tauri 从 `frontendDist` 嵌入前端
- 增加 init 后 `scripts/patch-ios-xcode.sh`：修复 FORCE_COLOR、以及 **Build Rust Code 需 cd 到 novaic-app**（否则 Xcode 直接 Run 会 PhaseScriptExecution failed）
- **debug 构建**：`npm run tauri:build:ios:debug` 产出可被 Safari Web Inspector 调试的 IPA
- **Xcode 运行**：`npm run tauri:open:ios` 打开工程，在 Xcode 中 Run 可看 Console 日志

### 二、配置已还原（2025-03 更新）

以下改动已**撤销**，恢复默认值，减少干扰：

| 文件 | 已移除 |
|------|--------|
| `tauri.ios.conf.json` | `assetProtocol`、`csp: null` |
| `index.html` | `<base href="./" />` |
| `vite.config.ts` | `base: './'`（改回默认 `'/'`） |
| `Info.plist` | `NSAppTransportSecurity`（Tauri 用自定义协议，ATS 不适用） |

### 三、当前现象

- 构建成功，IPA 可安装
- 真机启动后**黑屏**
- Safari 开发菜单能识别 iPhone，但**找不到 NovAIC 应用**，无法用 Web Inspector 调试
- **原因**：release build 的 WKWebView 默认不暴露给 Safari；需用 debug build 或从 Xcode 运行

---

## 问题描述

- **现象**：在真机 iPhone 上安装 NovAIC Tauri iOS 应用后，启动显示黑屏，无任何内容
- **环境**：Tauri 2、Vite + React、iOS 15.0+
- **设备**：iPhone 真机（ID: 00008130-000602411AB8001C）
- **构建**：`npm run tauri:build:ios` 可成功完成，生成 IPA 并安装

---

## 根因分析（2025-03 更新）

经排查，**黑屏的根本原因是自定义构建脚本破坏了 Tauri 的标准 iOS 构建流程**：

1. **Tauri iOS 不通过文件系统路径加载前端**：使用 `WKURLSchemeHandler` 注册 `tauri://localhost/`，资源由 `frontendDist` 在编译期嵌入 Rust 二进制
2. **手动复制 + xcodegen 覆盖了 Tauri 的 Xcode 配置**：`xcodegen generate` 会丢弃 Tauri 的 build phases、脚本和资源引用
3. **`--no-default-features` 可能剥离关键功能**：需谨慎使用

### 已实施的修复

- 移除自定义构建逻辑，改用标准 `tauri ios build`
- 移除 `xcodegen`，不再手动复制 dist 到 gen/apple
- 修复 Tauri 生成的 `project.yml` / `project.pbxproj` 中 `${FORCE_COLOR}` 被错误展开为 `0` 导致 ARCHS 解析失败的问题

---

## 已排除的问题

1. **构建失败**：已解决（swift-rs 无法访问 GitHub，通过本地 bare 仓库 + git insteadOf 解决）
2. **ARCHS 解析错误**：已解决（移除 `${FORCE_COLOR}` 避免被当作 arch 参数）
3. **`tauri ios run` export 失败**：Tauri CLI 在 `ios run` 的 export 阶段会创建临时 ExportOptions.plist，但传给 xcodebuild 的是相对路径（如 `.tmpXXXX`），xcodebuild 在 `gen/apple` 下执行时找不到该文件。**workaround**：使用 `tauri ios build`（成功）+ `xcrun devicectl device install app` 安装。`npm run tauri:run:ios` 已改为调用 `scripts/build-and-install-ios.sh` 实现此流程。
4. **黑屏根因**：`tauri.ios.conf.json` 中 `"app": { "windows": [] }` 覆盖了主配置，导致 iOS 不创建任何 WebView 窗口。已改为配置 `main` 窗口。

## 已尝试的修复（历史记录）

| 修改项 | 说明 | 状态 |
|--------|------|------|
| `tauri.ios.conf.json` | 添加 `assetProtocol`、`csp: null` | 已还原 |
| `Info.plist` | 添加 `NSAppTransportSecurity` | 已还原 |
| `index.html` | 添加 `<base href="./" />` | 已还原 |
| `vite.config.ts` | `base: './'` | 已还原为默认 |
| **构建流程** | **改用标准 Tauri 流程，移除 xcodegen 和手动复制** | 保留 |
| **debug 构建** | `tauri:build:ios:debug`、`tauri:open:ios` | 已添加 |

## 当前配置摘要

### 构建脚本 (`package.json`)

```json
"tauri:clean:ios": "rm -rf src-tauri/gen/apple",
"tauri:build:ios": "... tauri ios build",
"tauri:build:ios:debug": "... tauri ios build --debug",
"tauri:run:ios": "bash scripts/build-and-install-ios.sh",
"tauri:open:ios": "open src-tauri/gen/apple/novaic.xcodeproj"
```

`tauri:run:ios` 使用 build + devicectl install 的 workaround，避免 `tauri ios run` 的 exportOptionsPlist 临时文件 bug。

### Tauri iOS 配置 (`tauri.ios.conf.json`)

已还原为最小配置：仅保留 `windows`、`bundle.resources`、`bundle.iOS`，移除 `assetProtocol`、`csp`。

## 可能原因（待验证）

1. **Asset 协议在 iOS 上的实现**：Tauri 使用 `https://asset.localhost/` 或 `asset:` 协议加载前端，iOS WKWebView 可能对自定义协议或 localhost 有特殊限制
2. **资源路径解析**：`resource_dir` 在 iOS 上解析为 `${exe_dir}/assets`，与当前 bundle 结构是否一致需确认
3. **WKWebView 加载方式**：是否应使用 `loadFileURL` + `allowingReadAccessTo` 而非 asset 协议，需查 Tauri 源码
4. **前端嵌入方式**：Tauri 可能将 frontend 嵌入二进制，而非使用 bundle 中的资源，需确认 iOS 的 frontend 加载逻辑

## 最新状态（2025-03 更新）

- **现象**：最小化 HTML 测试仍黑屏，Safari 仍无法调试
- **已修复**：iOS 构建改为 `--no-default-features --features custom-protocol,mobile`（与 Android 一致），之前使用 default features（含 desktop）可能导致 iOS 加载异常
- **根因已定位**：`tauri.ios.conf.json` 中 `"windows": []` 覆盖了主配置，导致 iOS 不创建任何 WebView 窗口 = 黑屏。已改为配置 `main` 窗口。
- **请重新安装**：`npm run tauri:run:ios` 构建并安装后测试

## 建议的排查步骤（按优先级）

### 1. 用 Xcode 运行并查看 Console（最有效）

```bash
cd novaic-app && npm run tauri:open:ios
```

在 Xcode 中选择真机，点击 Run（▶）。**Console 面板**会输出 WKWebView 加载错误、Rust panic、资源路径等。即使 Safari 看不到 WebView，Xcode Console 也能看到。

### 2. Debug 构建 + Safari Web Inspector

```bash
cd novaic-app && npm run tauri:build:ios:debug
```

安装 debug IPA 后，Safari 应能识别 NovAIC。需确认：
- iPhone：设置 → Safari → 高级 → 打开「网页检查器」
- iPhone：设置 → 隐私与安全 → 开发者模式（若启用）
- Mac：Safari → 开发 → 选择 iPhone → 选择 NovAIC

### 3. 确认 frontendDist 配置

`tauri.conf.json` 中应为：
```json
"build": {
  "beforeBuildCommand": "npm run build",
  "frontendDist": "../dist"
}
```
路径相对于 `src-tauri/`，即 `novaic-app/dist/`。

### 4. 若仍黑屏：获取 Console 日志

**⚠️ 禁止从 Xcode 点 Run 构建！** 会报 `Connection refused` / `failed to build WebSocket client`，因为 `tauri ios xcode-script` 需连接 Tauri CLI 启动的 WebSocket 服务。

**正确方式：用终端构建并运行**

```bash
cd novaic-app && npm run tauri:run:ios
```

或只构建：

```bash
npm run tauri:build:ios:debug
```

安装 IPA 后，用 Xcode 附加调试器看 Console：**Debug → Attach to Process by PID or Name** → 输入 `NovAIC`。

### 5. 模拟器验证

```bash
npm run tauri:dev:ios
```
若模拟器正常、真机黑屏，则更可能是设备/网络相关配置。

## 相关链接

- [Tauri iOS asset 协议 #6962](https://github.com/tauri-apps/tauri/issues/6962)
- [Tauri iOS 白屏 #13356](https://github.com/tauri-apps/tauri/issues/13356)
- [Tauri iOS resource_dir #10070](https://github.com/tauri-apps/tauri/issues/10070)
- [Adimac93/tauri-mobile-alpha-template](https://github.com/Adimac93/tauri-mobile-alpha-template)（可参考的 Tauri iOS 模板）

## 版本信息

- Tauri: 2.x
- @tauri-apps/cli: 2.9.6
- Vite: 5.x
- React: 18.x
- Xcode: 26.x
- iOS 部署目标: 15.0
