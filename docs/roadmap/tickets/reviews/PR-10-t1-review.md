# PR-10 T1 Review（DispatchAssembler）

| 字段 | 值 |
| --- | --- |
| Reviewer | senior |
| Verdict | **REJECT — production latent bug** |
| 核心问题 | `assembler.py` 用了 **sync** `internal_client` 但 `dispatch()` 里 `await` 它，production 必炸 TypeError |
| 27 绿为何抓不到 | 所有 `test_assembler_*` 都在 fixture 里直接 `asm._client = MockClient()`，完全绕过 `internal_client` 返回值的真实签名 |

---

## §A  Bug 定位

- `novaic-common/common/wake/assembler.py:11` `from common.http.clients import internal_client`
- `common/http/clients.py:78` `internal_client = internal_sync_client`（alias 指向同步客户端）
- `assembler.py:52` `self._client = internal_client(...)` → 返回 `httpx.Client`（sync）
- `assembler.py:82` `resp = await self._client.post(...)` → `httpx.Client.post()` 返回 `Response`（非协程）→ `await Response` = `TypeError`

### 本地实测
```
$ python -c "from common.wake.assembler import DispatchAssembler; ..."
_client type: Client    ← 同步
post failed: RemoteProtocolError   ← sync post 立即发起连接
```

Sync `post()` 不加 `await` 就立刻执行 HTTP = 绝对不是协程。

## §B  为什么 27 绿零作用

```python
# test_assembler.py:38
@pytest.fixture
def assembler():
    resolver = MockResolver()
    asm = DispatchAssembler(resolver, "http://queue")
    asm._client = MockClient()   # <-- 替换了整个 _client
    return asm
```

所有 9 条 `test_assembler_*` 都走这个 fixture → `internal_client` 的真实返回值签名**一次都没被 await 过**。contract test 只覆盖字段对齐，也没触达 HTTP 层。

## §C  返工清单

### C.1（必做）换 async client
```python
# assembler.py:11
from common.http.clients import internal_async_client

# assembler.py:52
self._client = internal_async_client(service_name=service_name, base_url=queue_base_url)
```

### C.2（必做）加 transport-level mock 的集成测试
不替换 `asm._client`，只替换它的 transport：
```python
@pytest.mark.asyncio
async def test_dispatch_uses_async_client():
    import httpx
    captured = []
    def handler(request):
        captured.append(request)
        return httpx.Response(200, json={"session_id": "s-1", "buffered": False})

    resolver = MockResolver()
    asm = DispatchAssembler(resolver, "http://mock-queue")
    asm._client = httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="http://mock-queue")

    req = DispatchRequest("a-1", "u-1", "s-1", TriggerType.USER_MESSAGE)
    res = await asm.dispatch(req)
    assert res.session_id == "s-1"
    assert captured[0].url.path == "/api/queue/dispatch"
```

如果 C.1 没换，这条测试会 TypeError 当场暴露。

### C.3（选做，强烈建议至少记 TD）
`clients.py:78` 的 `internal_client = internal_sync_client` alias 是命名陷阱。两种处理：

- 立刻删 alias（跑 `rg "internal_client\b"` 看谁在用，强制所有调用方显式选 async/sync）
- 或在 `technical-debt.md` 记一笔：`internal_client` alias 是命名陷阱，PR-10 已经被它咬过，建议后续删除。

## §D  其他都没问题

- `DispatchError` dataclass + `Literal` ✅
- `get_resolver()` 回归 sync + PR-08 TD 从 technical-debt.md 划掉 ✅
- 结构化日志格式正确 ✅
- DI 构造器强制注入 ✅
- contract test alias 写法正确 ✅
- 3 个 commit 拆分干净 ✅

## §E  教训（第 2 次同类问题）

第 1 次：PR-08 5xx 只 mock 了 `httpx.ConnectTimeout`，漏了 `HTTPStatusError`。
第 2 次：PR-10 `_client` 被整体 mock，漏了 sync vs async 签名。

**规律**：如果测试 mock 了整个 `_client` 或对等 abstraction，就等于绕过了"这个 abstraction 的真实签名/行为"。真实签名问题必须在 **transport 层 / response 层 / socket 层** 打 mock 才能暴露。

写集成对象测试前自问：**"我 mock 的这层，是不是我要验证契约的那一层？"** 如果是，就换一层更底层的 mock。

C.1 + C.2 改完跑绿 + C.3 选一个动作落实后直接 declare done，不再 review 一轮。
