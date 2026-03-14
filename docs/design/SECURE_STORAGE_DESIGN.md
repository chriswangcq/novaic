# SecureStorage 设计说明

> 目标：跨平台安全存储 JWT、api_key 等敏感数据  
> 桌面：localStorage 或加密文件；移动端：Keychain（iOS）/ Keystore（Android）

---

## 一、需求

| 数据类型 | 用途 | 当前存储 | 安全要求 |
|----------|------|----------|----------|
| **用户 JWT** | Gateway 认证、Cloud Bridge | localStorage + CloudTokenState | 高 |
| **设备 api_key** | 本地 Gateway 设备认证 | data_dir/api_key.txt 明文 | 中 |
| **LLM API keys** | 模型调用 | Gateway /api/config | 中 |

---

## 二、平台方案

| 平台 | 推荐实现 | 说明 |
|------|----------|------|
| **macOS** | Keychain | `Security.framework` 或 `tauri-plugin-store` 加密 |
| **Windows** | DPAPI / Credential Manager | 或 `tauri-plugin-store` 加密 |
| **Linux** | 加密文件或 libsecret | `secret-tool` 或 gnome-keyring |
| **Android** | EncryptedSharedPreferences / Keystore | 需 Kotlin 插件 |
| **iOS** | Keychain | 需 Swift 插件 |

---

## 三、实现路径

### 3.1 方案 A：Tauri 插件

- **tauri-plugin-store**：SQLite，不推荐存敏感数据
- **tauri-plugin-store** + 加密：可对 value 做 AES 加密后存储
- **社区插件**：搜索 `tauri-plugin-secure-storage`、`tauri-plugin-keychain` 等

### 3.2 方案 B：自定义插件

新建 `tauri-plugin-secure-storage` 或项目内 Kotlin/Swift 模块：

- **Android**：`EncryptedSharedPreferences`（KeyStore 后端）
- **iOS**：`KeychainServices`（kSecClassGenericPassword）

### 3.3 方案 C：前端抽象 + 平台注入

```
frontend/
  SecureStorage.ts     # 接口：get(key), set(key, value), delete(key)
  tauriSecureStorage.ts # 实现：invoke('secure_storage_get', {key}) 等
  mobileSecureStorage.ts # 实现：React Native 或 Capacitor 原生模块
```

Rust 侧新增命令：

- `secure_storage_get(key: String) -> Result<Option<String>, String>`
- `secure_storage_set(key: String, value: String) -> Result<(), String>`
- `secure_storage_delete(key: String) -> Result<(), String>`

---

## 四、建议实施顺序

1. **短期**：保持现状，文档注明「移动端 JWT 建议用 SecureStorage」
2. **中期**：实现 `secure_storage_*` 命令，桌面用加密文件（如 AES-256-GCM + 设备 key）
3. **长期**：Android/iOS 原生插件（Kotlin/Swift）接入 Keychain/Keystore

---

## 五、相关文档

- `TAURI2_MOBILE_MODULARIZATION_PLAN.md`：5.3 凭证与认证
- `CROSS_PLATFORM_ARCHITECTURE.md`：Storage 抽象
