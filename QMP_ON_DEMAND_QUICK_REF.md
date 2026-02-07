# QMP 按需连接模式 - 快速参考

## 一句话总结
QMP 从长连接改为按需连接，解决 "Broken pipe" 问题，提升稳定性。

## 关键变化

### Before (长连接)
```rust
pub struct VmManager {
    qmp: QmpClient,  // 保存长连接
}

vm.qmp.execute("stop", None).await?;  // 直接使用
```

### After (按需连接)
```rust
pub struct VmManager {
    qmp_socket: String,  // 只保存路径
}

let mut qmp = vm.create_qmp_client().await?;  // 临时连接
qmp.execute("stop", None).await?;
// 自动关闭
```

## 修改的文件

| 文件 | 主要变化 |
|------|---------|
| `api/routes/vm.rs` | VmManager 结构 + pause/resume/shutdown/register |
| `api/routes/screen.rs` | screenshot() |
| `api/routes/input.rs` | keyboard_input() + mouse_input() |
| `main.rs` | auto_register_running_vms() |

## 优势

✅ 无 "Broken pipe" 错误  
✅ QEMU 重启自动恢复  
✅ 无需维护连接状态  
✅ 更好的并发性能（read lock）  
✅ API 完全兼容  

## 编译验证

```bash
cd novaic-app/src-tauri
cargo check --manifest-path vmcontrol/Cargo.toml
# ✅ 成功，无错误
```

## 快速测试

```bash
# 1. 启动 VM（如果未启动）
# 2. 测试暂停/恢复
curl -X POST http://localhost:8080/api/vms/1/pause
curl -X POST http://localhost:8080/api/vms/1/resume

# 3. 重启 QEMU
# 4. 再次测试 - 应该自动恢复
curl -X POST http://localhost:8080/api/vms/1/pause
```

## 完整文档

详见 `QMP_ON_DEMAND_CONNECTION_REFACTOR.md`
