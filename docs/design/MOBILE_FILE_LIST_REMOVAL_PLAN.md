# mobile_file_list 删除方案

## 背景

`mobile_file_list` 工具因返回格式与 TRS 不兼容（`files` 含 `{name, path, is_dir, size}` 无 `url`），导致 TRS 422、无 `result_id`、Saga 失败。经讨论决定**删除该工具**，避免修复带来的熵增，确保无遗留代码。

---

## 一、影响范围清单

### 1. 工具定义（需删除 mobile_file_list 条目）

| 文件 | 说明 |
|------|------|
| `novaic-gateway/common/tools/definitions.py` | Gateway 工具发现，MOBILE_TOOLS 列表 |
| `novaic-shared-runtime-common/shared_runtime_common/common/tools/definitions.py` | Tools Server 使用（经 common  re-export） |
| `novaic-shared-kernel/src/common/tools/definitions.py` | 共享定义（需确认是否被引用，若有则同步删除） |

### 2. Tools Server 执行器

| 文件 | 修改内容 |
|------|----------|
| `novaic-tools-server/tools_server/executor.py` | ① MOBILE_TOOL_MAPPING 删除 `"mobile_file_list": ("file/list", None)`<br>② MOBILE_TOOLS_SET 删除 `"mobile_file_list"`<br>③ GET 方法条件：`("mobile_app_list", "mobile_file_list")` → `("mobile_app_list",)` |

### 3. vmcontrol（Android API）

| 文件 | 修改内容 |
|------|----------|
| `novaic-app/src-tauri/vmcontrol/src/api/routes/mod.rs` | 删除 `.route("/:serial/file/list", get(mobile::file_list))` |
| `novaic-app/src-tauri/vmcontrol/src/api/routes/mobile.rs` | 删除：① `FileListQuery`/`FileInfo`/`FileListResponse` 结构体（约 2953-2980 行）<br>② `file_list` 函数（约 3440-3499 行）<br>③ `parse_ls_output` 函数（约 3500-3567 行） |

**注意**：上述类型与函数仅被 `file_list` 使用，删除时一并移除，避免死代码。

### 4. mcp-vmuse（VM 内 file_list，一并删除）

| 文件 | 修改内容 |
|------|----------|
| `novaic-mcp-vmuse/src/novaic_mcp_vmuse/http_server.py` | ① 删除 `add_post('/api/file/list', self.file_list)`<br>② 删除 `file_list` 方法 |
| `novaic-mcp-vmuse/src/novaic_mcp_vmuse/main.py` | ① 删除 `list_files` MCP 工具<br>② 文档表删除 `file_list` 行 |
| `novaic-mcp-vmuse/src/novaic_mcp_vmuse/tools/files.py` | 删除 `FileTools.list_files` 方法 |
| `novaic-app/.../novaic-mcp-vmuse/` | 同上（resources 内副本需同步修改） |
| `novaic-tools-server/mcp_client/skills/files/SKILL.md` | 删除 `list_files` 章节及用例 |
| `novaic-mcp-vmuse/README.md` | File Tools 表删除 `list_files` 行 |

### 5. 文档

| 文件 | 修改内容 |
|------|----------|
| `docs/TOOL_ERRORS_ANALYSIS.md` | 删除或重写 mobile_file_list 章节，保留 subagent_cancel |
| `docs/TOOL_ERRORS_TROUBLESHOOTING.md` | 删除 mobile_file_list 相关引用 |
| `novaic-control-plane/docs/CONTEXT_SUMMARY.md` | 删除 6.1 mobile_file_list 及相关引用 |

---

## 二、执行顺序

1. **工具定义**：从 3 处 definitions 删除 mobile_file_list 条目
2. **executor**：删除映射、集合、GET 条件
3. **vmcontrol**：删除路由 + mobile.rs 中全部相关代码
4. **mcp-vmuse**：删除 http_server 路由/方法、main.py MCP 工具、FileTools.list_files、SKILL/README
5. **文档**：更新/删除相关说明

---

## 三、验证清单

- [ ] `rg "mobile_file_list"` 无匹配（除文档中的“已删除”说明）
- [ ] `rg "file/list"|"file_list"|"list_files"` 无匹配（mcp-vmuse、vmcontrol 均已删除）
- [ ] `rg "FileListQuery|FileListResponse|FileInfo"` 在 vmcontrol 无匹配
- [ ] Tools Server 启动无报错
- [ ] vmcontrol 编译通过
- [ ] mcp-vmuse 启动无报错
- [ ] 新建对话，Agent 不再出现 mobile_file_list、list_files 工具

---

## 四、回滚

若需恢复，按上述清单反向操作即可。建议删除前打 tag 或保留分支。
