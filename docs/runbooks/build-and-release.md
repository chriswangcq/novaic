# 构建与发布（客户端）

> 与当前代码一致；对应原 **`HANDOVER.md` §五**。命令以 **`novaic-app/package.json`** 为准。

## 环境

- Node ≥ 18、npm ≥ 9；Rust stable；macOS 需 Xcode 工具链。

## 桌面 App

```bash
cd novaic-app
npm run tauri:build -- --bundles app
# 输出: src-tauri/target/release/bundle/macos/NovAIC.app（名称以实际 bundle 为准）
cp -r src-tauri/target/release/bundle/macos/NovAIC.app /Applications/NovAIC.app
```

勿用 `npm run tauri build --ci`；正确命令：`npm run tauri:build -- --bundles app`。

## iOS 部署流程（完整）

**一键构建安装**：`cd novaic-app && ./scripts/build-and-install-ios.sh`

**手动分步**：

```bash
test -d src-tauri/gen/apple || env -u CI tauri ios init
bash scripts/patch-ios-xcode.sh
npm run tauri:build:ios:debug
IPA_PATH="src-tauri/gen/apple/build/arm64/NovAIC.ipa"
DEVICE=$(xcrun devicectl list devices 2>/dev/null | awk '/connected/ && !/Simulator/ {for(i=1;i<=NF;i++) if($i~/^[0-9A-F]{8}/) {print $i;break}}' | head -1)
xcrun devicectl device install app --device "$DEVICE" "$IPA_PATH"
```

**为何不用 `tauri ios run`**：`-exportOptionsPlist` 传相对路径 bug，xcodebuild 找不到临时文件。

**iOS 关键脚本**：

| 脚本 | 用途 |
|------|------|
| `scripts/patch-ios-xcode.sh` | 移除 FORCE_COLOR（导致 arch 参数错误）；改用 `run-ios-xcode-script.sh` |
| `scripts/run-ios-xcode-script.sh` | Xcode 构建阶段 cd 到项目根执行 npm |
| `scripts/build-and-install-ios.sh` | 完整流程 |

**iOS 黑屏修复**：

1. iOS 构建使用 `--features mobile` 而非 `custom-protocol,mobile`（WKWebView 黑屏）
2. `config/index.ts` 未设置 `VITE_GATEWAY_URL` 时兜底 `https://api.gradievo.com`
3. `tauri.ios.conf.json` 覆盖桌面配置

**iOS 键盘原生修复（main.mm）**：

- 移除 WKWebView 键盘通知观察者 → 阻止 iOS 自动滚动
- 注册自定义监听 → 精确键盘高度 → 注入 CSS `--keyboard-height`
- `LayoutContainer.tsx` 移动端用 `position: fixed; bottom: var(--keyboard-height, 0px)`
- `ffi::start_app()` 启动 UIKit run loop 且永不返回，所有 `dispatch_after` 必须在它之前调用
- `index.html` viewport **不含** `interactive-widget=`（WebKit 忽略该 token）；键盘与视口以 **main.mm + `LayoutContainer`** 为准

**Xcode 26.x 与 `aws-lc-sys`**：`aws-lc-sys` 在 Xcode 26.3 beta 下可能因 SDKROOT 指向 iPhoneOS 而非 macOS SDK 导致交叉编译失败。推荐正式版 Xcode 或手动注入 CFLAGS。

## Android

```bash
npm run tauri:build:android
```

使用 **custom-protocol**（与 iOS 的 feature 组合不同）。

## OTA 前端与生产部署

见 [**`deploy.md`**](deploy.md)、[**`cloud-production.md`**](cloud-production.md)：CDN 三处同步（`src/config/index.ts` 的 `OTA_ORIGINS`、`src-tauri/capabilities/remote-frontend.json`、`src-tauri/src/setup.rs`）、`scripts/check-ota-sync.sh`。
