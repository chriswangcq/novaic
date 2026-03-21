# ByClaw 图标生成与打包指南 (App Icon Generation Guide)

由于 Apple 对 macOS 和 iOS 的图标规范存在**根本性的互斥**，我们在使用 Tauri 打包多平台应用时，必须对桌面端和移动端的图标进行**物理分离**的管理和生成。

本指南记录了图标渲染的关键坑点，以及未来如何安全地更新应用图标。

---

## 1. 核心大坑与跨平台规范

### 1.1 macOS (桌面端 `.icns` 格式)
- **核心要求**：必须是 **带有圆角和透明内边距 (Padding) 的 Squircle（松鼠角矩形）**。
- **为什么**：Tauri 打包 macOS 时生成的是本地的 `.icns` 格式文件。从 macOS Big Sur (11.0) 开始，苹果不会自动为本地 `.icns` 图标切割圆角。
- **神坑警告 (Launchpad 嵌套套娃盒子)**：如果你提供的 1024x1024 图标**内边距太大，或者阴影的高斯模糊包含了半透明像素接触到了 1024 全尺寸的边缘**，macOS 就会将其判定为“不合规的 Legacy / iOS 移植图标”，并**强行在它的底层塞一个灰黑色的深色小底座进行嵌套包装！**
- **黄金尺寸**：在 1024x1024 的画布中，主体截取为约 `824x824` ~ `921x921`（约放缩 80%~90%），四角裁切为完美的 Squircle，并放置于 1024 的正中心，周围保留绝对干净透明的像素。

### 1.2 iOS / iPadOS (移动端 `.xcassets` 格式)
- **核心要求**：必须是 **实心、绝对 100% 不留白（Full-Bleed）、不包含任何透明度通道（Alpha）的直角大正方形**。
- **为什么**：iOS 系统会在安装你的 App 时，利用专门的硬件遮罩强制切掉边缘。
- **神坑警告 (White Ring 白圈 Bug)**：如果你像 macOS 一样给 iOS 提供了带有透明留白底的圆角图标，iOS 打包系统（Xcode）会自动把你所有透明（Transparent）的像素**全部填满为纯白色**。导致你的图标安装在手机上变成一个刺眼的白色正方形！

---

## 2. 文件分布结构

为了完美适配上述两个极端的平台规范，我们的代码库采用了**双管齐下**分离式的管理结构，**千万不要随意运行全程的 `tauri icon`** 否则必定打破这种平衡！

* **macOS 独立专用层**：
  - 文件：`novaic-app/src-tauri/icons/icon.icns` 及周边的 `.png`。
  - 特征：这一套图全都是切好了透明圆角的优美形态，专供 `./deploy desktop` 构建。

* **iOS / Xcode 独立专用层**：
  - 文件：`novaic-app/src-tauri/gen/apple/Assets.xcassets/AppIcon.appiconset/`
  - 特征：这里面的上百张小图，全部都是**绝对死直角的纯正方形**。专供 `./deploy ios` 读取。

---

## 3. 未来如何更新应用图标？

如果你更换了新的品牌 Logo，请**必须严格按照以下两段式（Two-Step）流程进行更新**，切忌单步全自动覆盖。

### 第一步：制作并更新 macOS 版本 (留白圆角)
1. 准备一张高精度的透明底圆角 Logo。
2. 将其放缩进 `1024x1024` 的画布内，主体保证在 `921x921` 左右（推荐缩放 90%）。
3. 保证周围的所有像素为空局，不带任何溢出的模糊黑阴影或杂边。
4. 将该图放在根目录，并运行 tauri 官方指令生成桌面的 icns：
   ```bash
   cd novaic-app
   npx tauri icon <你的透明圆角源图.png>
   ```
5. 这条指令会成功覆盖并生成 `src-tauri/icons/` 下的所有 macOS 和 Windows 图标。**但是它同时把你 iOS 的 `xcassets` 给全毁成了含有透明通道的残次品！**

### 第二步：制作并特供覆盖 iOS 版本 (满屏直角)
1. 准备另一张同款 Logo 的**大直角满屏正方形源图**（例如 `icon_fullbleed.png`），里面是完全铺满背景色的实心。
2. 再次执行 Tauri 图标指令进行二次覆盖（目的是专供 iOS 使用这段输出）：
   ```bash
   cd novaic-app
   npx tauri icon <你的实心直角源图.png>
   ```
3. 这一步把 iOS 所需要的所有满屏正方形都生成并且落到了 `src-tauri/gen/apple/Assets.xcassets` 里。**但是它同时又把你刚刚辛辛苦苦做好的 macOS `.icns` 全弄成了巨大的直角大方块！**

### 第三步：使用 Git 还原 macOS 的那一部分 (拼接融合)
既然此时 iOS 的目录是对的，而 macOS 的目录是错的，我们用 git 将 macOS 的那一套独立恢复成第一步生成的最终成果：
```bash
# 假设你在第一步做完之后，进行了一次 git commit 保存过了 macOS 的那一套！
# 或者你使用底层工具将 iOS 输出完之后，再把原来的 macOS .icns 复制覆写回来。

# 最终你的代码提交记录（git status）应该呈现：
# - src-tauri/icons/ 里面留着带透明边的 png 和 icns (macOS 专属)
# - src-tauri/gen/apple/.../AppIcon.appiconset/ 里面留着实心大方块 (iOS 专属)
```

> **最佳实践**：我们目前的 Git 记录（`b53273c` 的 `.icns` + `6f3dfca` 的 `xcassets`）就是靠以上的拼接术最终合并出的一套黄金标准模板。在任何情况下，请通过 Git Checkout 保证它们各司其职，千万别用一张图同时去打包双端。

---
**附：关于开发时的图标缓存清理**
macOS 对于 Dock 栏及 Launchpad 里应用程序图标的缓存可谓“顽固至极”。
当你成功编译了完美的 `./deploy desktop` 却发现启动台里的截图依然错误时，它可能是旧版的幻影：
```bash
# 清空 macOS Dock 图标缓存的快速指令
killall Dock
```
如果是 Launchpad，你可以试着把它从应用里拖出去再拖回来，或者通过终端清除 `com.apple.dock.iconcache`。
