# PR-05 调研 v2 批准

> 被审对象：[`PR-05-preflight-antigravity.md`](PR-05-preflight-antigravity.md) (v2)
> 上游 review：[`PR-05-preflight-review.md`](PR-05-preflight-review.md)
> 状态：**✅ 批准，可进入 T1**

---

## 核验结果

| # | 要求（来自 review §5） | 状态 |
| --- | --- | --- |
| 1 | SDK 实例化方迁移表 | ✅ §2 表 23 行完整 |
| 2 | 修正"跨服务 SDK"用语 | ✅ §2 开头明确更正 |
| 3 | §范围收窄决议 | ✅ §5，与 review §2 裁决表一致 |
| 4 | 命名表 7 行采纳 | ✅ §6 完全一致 |
| 5 | §提交顺序约定 | ✅ §7 四步流程清楚 |
| 6 | Q4 KEEP 加永久保留理由 | ✅ 四行 KEEP 全部注明 |

**附加确认**：`technical-debt.md` 末尾新增"内部 Key 未统一"条目，回溯链接到本目录 §2，符合预期。

**Spot-check**：`novaic-device/device/gateway_signaling.py` 归为 DELETE 是正确的（文件内 `httpx.AsyncClient` 打的是 gateway 内部 endpoint）。

---

## T1 阶段工作许可

允许进入实施。提醒四条硬约束（不要忘）：

1. **`service_name=None` 直接 `raise ValueError`**，不要兜底 `"unknown"`
2. **不搞 `service_name` 可选 overload**，一次性必填
3. **每个仓一个 commit**：
   - `refactor(common): internal_client requires service_name (PR-05)` — 只动 `clients.py` + tests
   - `refactor(runtime): adopt internal_client(service_name=...) (PR-05)` — 改 runtime call sites
   - `refactor(business): adopt internal_client(service_name=...) (PR-05)` — 改 business call sites（包括 11 处 `EntangledServiceClient`）
   - `refactor(gateway): adopt internal_client(service_name=...) (PR-05)`
   - `refactor(device): adopt internal_client(service_name=...) (PR-05)`
   然后主仓 commit bump 所有 submodule pointer
4. **Push 前本地跑一遍 `bash scripts/ci/lint_httpx.sh`**，必须 green

---

## 验收时我会看什么

PR 描述里请粘：

```bash
# 1. 全仓无 service_name 漏传
rg "internal_client\(|internal_(sync_|async_)?client\(" novaic-*/ --type py \
  | rg -v "service_name=" \
  | rg -v "novaic-common/common/http/clients.py"
# 预期：空（除 clients.py 本体定义和 tests/）

# 2. CI lint 通过
bash scripts/ci/lint_httpx.sh
bash scripts/ci/lint_dispatch.sh
# 预期：两条 OK

# 3. 单测
pytest novaic-common/tests/test_internal_client.py -v
# 预期：3 条用例全 pass（无 service_name → ValueError；注入 X-Internal-Service；NOVAIC_INTERNAL_KEY 未设置 → WARN 不 raise）
```

---

## 最后一句

v1 → v2 是一次干净的返工，没有重复犯错、没有讨价还价，这是非常好的迭代节奏。**按同样标准做 T1。**

— Reviewer
