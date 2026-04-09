> **文档状态（2026-04）**：本文为过程稿、调研快照或子模块镜像，**非**仓库唯一现行架构来源。权威总览见仓库根 `docs/backend-architecture.md`；与代码/部署对齐的核查见 `docs/architecture-verification-2026-04.md`。

# 前端热更新部署步骤（relay.gradievo.com/resource/frontend/）

## 构建说明（VITE_BASE）

- **tauri build**：不设置 `VITE_BASE`，产出 `base='/'`，资源路径为 `/assets/xxx`，用于本地 bundled 兜底
- **CDN 部署**：必须设置 `VITE_BASE=/resource/frontend/v{version}/`，产出路径为 `/resource/frontend/v{version}/assets/xxx`
- `deploy-frontend.sh` 自动设置 `VITE_BASE`，勿用错误 base 构建 CDN 产物

---

## 一、部署前端到 Relay

### 前置：Relay 服务器配置（首次部署时执行）

1. **证书**：relay.gradievo.com 证书已存在（relay+stun 同证），无需额外域名或扩证
2. **Nginx 静态服务**：

```bash
ssh root@relay.gradievo.com "bash -s" < novaic-quic-service/deploy/setup-cnd-frontend-nginx.sh
```

3. **DNS**：确认 `relay.gradievo.com` 已解析到 relay 服务器 IP

### 部署

```bash
cd novaic-app
# deploy-frontend.sh 第三参为 SSH 端口，默认 52222（见脚本）；若主机用 22，请传第三参 22
./scripts/deploy-frontend.sh root@relay.gradievo.com 0.3.0
```

验证：访问 https://relay.gradievo.com/resource/frontend/v0.3.0/ 应能看到前端页面。

---

## 二、更新 Gateway 配置

在服务器 **`/opt/novaic/jwt_secret.env`**（或等价环境）中增加（可选，有默认值）：

```bash
export FRONTEND_CDN_URL=https://relay.gradievo.com/resource/frontend/v0.3.0/
export FRONTEND_VERSION=0.3.0
```

部署 Gateway 并重启：

```bash
cd novaic-gateway
git add -A && git commit -m "feat: frontend OTA relay.gradievo.com" && git push
./scripts/deploy-gateway.sh root@api.gradievo.com
```

或仅重启：**`restart_gw.sh` 已删除**（见根目录 `HANDOVER.md`）；请用 **`/opt/novaic/start.sh`** 或团队现行运维脚本，勿照抄已移除路径

---

## 三、手机端构建（采用 HANDOVER.md 方式）

### iOS 一键构建并安装到真机

```bash
cd novaic-app
./scripts/build-and-install-ios.sh
```

或手动分步：

```bash
# 1. 确保 gen/apple 存在（首次需 tauri ios init）
test -d src-tauri/gen/apple || env -u CI tauri ios init

# 2. 打补丁（修复 Xcode 构建脚本）
bash scripts/patch-ios-xcode.sh

# 3. 构建 debug IPA
npm run tauri:build:ios:debug

# 4. 安装到已连接设备
IPA_PATH="src-tauri/gen/apple/build/arm64/NovAIC.ipa"
DEVICE=$(xcrun devicectl list devices 2>/dev/null | awk '/connected/ && !/Simulator/ {for(i=1;i<=NF;i++) if($i~/^[0-9A-F]{8}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{12}$/) {print $i;break}}' | head -1)
xcrun devicectl device install app --device "$DEVICE" "$IPA_PATH"
```

### Android

```bash
cd novaic-app
npm run tauri:build:android   # 或 tauri:dev:android
```

产出在 `src-tauri/gen/android/app/build/outputs/apk/`。

### 前置条件

- **iOS**：Xcode、Apple Developer 账号；首次需 `tauri ios init`；`tauri.ios.conf.json` 中填写 `developmentTeam`
- **Android**：Android Studio、NDK、`ANDROID_HOME`；首次需 `tauri android init`

详见根目录 `HANDOVER.md` **第五「构建与发布」**（§5.2 iOS / §5.3 Android）及「iOS 部署流程（完整）」。

---

## 四、后续热更新

1. 修改前端代码
2. 执行 `./scripts/deploy-frontend.sh root@relay.gradievo.com 0.3.1`（版本号按需调整）
3. 更新 Gateway 环境变量 `FRONTEND_CDN_URL`、`FRONTEND_VERSION` 并重启
4. 用户下次启动 App 时会自动加载新版本（桌面+手机均生效）

---

## 五、回滚

将 Gateway 的 `FRONTEND_CDN_URL` 改回旧版本路径（如 `/resource/frontend/v0.3.0/`），重启 Gateway 即可。
