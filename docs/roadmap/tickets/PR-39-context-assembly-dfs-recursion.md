# PR-39  Context assembly 真·DFS：scope_id 索引匹配 + 递归折叠嵌套 closed 子 scope

| 字段 | 值 |
| --- | --- |
| **Phase** | hotfix（Cortex context assembly 四连击 #4/4 — 改动最大） |
| **Milestone** | — |
| **承诺** | 架构原则：**显式 > 隐式** + **一致性 > 便利** |
| **Status** | `[x]` 2026-04-22 完成 — StepTree.get_scope_index 递归 + engine 用 scope_id 匹配 + 10 unit tests |
| **Depends on** | — |
| **Blocks** | — |
| **估时** | 0.5 d |
| **Owner** | wangchaoqun |

## 事件摘要

Context assembly 声称是 "DFS Step Tree based"（见 `engine.py:1` docstring），**实际不是 DFS**。当嵌套 skill 结构里有"开放的父 scope 包含已归档的子 scope"时，子 scope 不会被 fold，它的 raw 消息泄漏进父 context，LLM 看到折叠逻辑只对**顶层** scope 生效。

## 根因（两条）

### 问题 A：`scope_nodes` 只取顶层

```74:76:novaic-cortex/novaic_cortex/context_stack/step_tree.py
    def get_scope_nodes(self) -> List[StepNode]:
        """Top-level scope nodes in order (for matching with skill_begin calls)."""
        return [n for n in self.nodes if n.is_scope]
```

深层嵌套的 scope 节点不在返回列表里。

### 问题 B：skill_begin ↔ scope_node 配对靠**序数**

```131:139:novaic-cortex/novaic_cortex/context_stack/engine.py
        if _has_tool_call_named(msg, "skill_begin"):
            if scope_idx < len(scope_nodes):
                scope_node = scope_nodes[scope_idx]
                scope_idx += 1
```

在父开放的嵌套场景下会走偏：

- 父 scope A **open**（fall through），
- 在 A 内 LLM 调 `skill_begin(scope_id="B")`，B **closed**。
- Engine 看到 B 的 `skill_begin`，想 fold —— 但 `scope_nodes[1]` 根本不存在（只有 A 在顶层 `scope_nodes` 里）。
- 于是 B 不 fold，B 里的 assistant 消息全部泄漏给主 LLM。

更糟：一旦 context.jsonl 和 `_index.jsonl` 顺序因 CLAIM/RETRY 有错位（PR-22+ 的 message lifecycle 是 idempotent，但 writer 的幂等不代表 reader 的排序恒等），序数配对会把 A 的 skill_begin 匹配到错误的 scope_node。

## 修复方案

### A. `StepTree` 新增递归 scope_id → StepNode 索引

```python
# novaic-cortex/novaic_cortex/context_stack/step_tree.py

def get_scope_index(self) -> Dict[str, "StepNode"]:
    """Recursive map: scope_id (== step_id for scope nodes) → StepNode.

    Used by ContextEngine to match `skill_begin(scope_id=X)` in context.jsonl
    against the correct scope node regardless of nesting depth. Replaces the
    old ordinal-based `get_scope_nodes()` matching, which broke when an open
    parent contained a closed child.
    """
    out: Dict[str, "StepNode"] = {}
    _collect_scope_index(self.nodes, out)
    return out


def _collect_scope_index(nodes: list[StepNode], out: Dict[str, StepNode]) -> None:
    for node in nodes:
        if node.is_scope:
            if node.step_id:
                out[node.step_id] = node
            # Recurse into open scopes; closed scopes are folded at their
            # boundary so their grandchildren are irrelevant to parent context.
            if not node.closed:
                _collect_scope_index(node.children, out)
```

保留旧的 `get_scope_nodes()` 不动（防止其他调用方回归）—— 但在 engine.py 里替换成新的 index-based 匹配。

### B. Engine `_merge_context_and_steps` 改用 scope_id 匹配

关键逻辑改写：

```python
# novaic-cortex/novaic_cortex/context_stack/engine.py

def _merge_context_and_steps(
    context_messages: list[dict],
    tool_results: Dict[str, str],
    scope_index: Dict[str, StepNode],  # ← 改这里
) -> list[dict]:
    result: list[dict] = []
    skip_depth = 0
    used_tool_call_ids: set[str] = set()

    for msg in context_messages:
        role = msg.get("role", "")

        if skip_depth > 0:
            if _has_tool_call_named(msg, "skill_end"):
                skip_depth -= 1
            elif _has_tool_call_named(msg, "skill_begin"):
                skip_depth += 1
            continue

        # Match skill_begin against scope_index by scope_id argument
        begin_scope_id = _extract_skill_begin_scope_id(msg)
        if begin_scope_id is not None:
            scope_node = scope_index.get(begin_scope_id)
            if scope_node is not None and scope_node.closed:
                result.append(render_scope_fold(scope_node))
                skip_depth = 1
                continue
            # Unknown scope_id (index missing) OR open scope: fall through,
            # include the message normally. Fall-through for unknown is
            # defensive: if _index.jsonl is stale vs context.jsonl, we'd
            # rather leak than drop. Log a warning so drift is visible.
            if scope_node is None:
                logger.warning(
                    "[ContextEngine] skill_begin(scope_id=%s) has no "
                    "matching scope_node in step tree; falling through "
                    "(possible index drift)", begin_scope_id,
                )

        # ... existing tool message dedup + assistant tool_call injection ...

def _extract_skill_begin_scope_id(msg: dict) -> Optional[str]:
    """Parse skill_begin tool_call arguments to get scope_id."""
    if msg.get("role") != "assistant":
        return None
    for tc in msg.get("tool_calls") or []:
        fn = tc.get("function") or {}
        if fn.get("name") != "skill_begin":
            continue
        args_raw = fn.get("arguments", "{}")
        try:
            args = json.loads(args_raw) if isinstance(args_raw, str) else args_raw
        except (json.JSONDecodeError, TypeError):
            return None
        sid = args.get("scope_id")
        if isinstance(sid, str) and sid:
            return sid
    return None
```

### C. Observability

- 日志 `event=scope_fold scope_id=... depth=... name=...` 每次折叠时打。
- 日志 `event=scope_index_drift scope_id=...` 命中 fall-through 警告时打。
- 测试场景覆盖 drift 检测（见下）。

### D. 回归测试

`novaic-cortex/tests/test_context_engine_dfs.py` 新增（或在现有 `test_v2.py` 扩展）：

1. **顶层 closed scope fold**（baseline，已被现有覆盖）。
2. **嵌套 closed 子 scope 在开放父下**（修复焦点）：root 有开放子 scope A，A 内有 closed 孙 scope B → assembly 应该 fold B，不泄漏 B 的内部消息。
3. **嵌套 open 子 scope**：root 有开放子 A，A 内有 open 孙 B → B 不 fold，B 里的 tool_call 结果通过 `tool_results` flat map 正常显示。
4. **scope_id drift**：context.jsonl 有 `skill_begin(scope_id="ghost")` 但 step tree 没有对应 node → fall through + warning log。
5. **二级 closed scope（兄弟）**：root 有两个顶层 child A 和 C，A open、C closed（不同时间发生）→ C 被 fold，A 不动。

### E. 兼容性

- `StepTree.get_scope_nodes()` 保留（未来 trace / 分析路径可能在用）。
- `_merge_context_and_steps` 签名改变（`scope_nodes: List[StepNode]` → `scope_index: Dict[str, StepNode]`）—— 内部函数，grep 确认无外部 caller。

## 子 PR

| # | Repo | Branch | 内容 |
|---|---|---|---|
| 1 | `novaic-cortex` | `hotfix/context-assembly-dfs-recursion` | A + B + C + D（step_tree + engine + tests） |
| — | 主仓 | `fix/cortex-context-assembly-36-39` | submodule bumps |

## 验收

- 5 个新 test 全绿。
- 手动验证：造一条 session 里有嵌套 skill (A open → B closed → A continue) → `/v1/context/prepare_for_llm` 返回的 messages 不含 B 内部消息，只有一条 `[Skill 'B' completed]` fold 系统消息。
- 日志里新增的 `event=scope_fold` 能在 ops grep 命中每次嵌套 fold 事件。

## 回滚

`git revert <commit>` —— 回到序数匹配。嵌套 closed fold 再次失效，但主路径不破坏。

## 架构判定沉淀

- **内部标识符配对优先用语义键、不用序数**：`tool_call_id`、`scope_id`、`message_id` —— 所有跨 data source 的配对（context.jsonl ↔ `_index.jsonl`、message_outbox ↔ chat_messages 等）都应该用语义键。序数隐式假设两侧顺序恒等，一旦任何一侧重试 / 幂等重写，序数就跪。
- **index drift 是真实风险**：即便幂等写 + 单体 writer，仍可能因并发 flush / crash 恢复导致 `_index.jsonl` 和 `context.jsonl` 不同步。Reader 路径对 drift 的态度应该是 "显式降级 + 显式告警"，不是 "静默接受"。
