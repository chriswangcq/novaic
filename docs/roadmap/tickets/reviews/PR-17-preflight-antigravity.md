# PR-17 Preflight Report (Canary & Deployment)

## §F Discovery 实地勘测结果

1. **生产当前 Business 代码版本**：
   - 勘测命令：`ssh root@api.gradievo.com "ls -la /opt/novaic/services/novaic-business/business/subscribers"`
   - **结果**：生产机器上的 `/opt/novaic/services/novaic-business` 不是一个 git 仓库（`git log` 会报错），且不存在 `subscribers/dispatch_subscriber.py` 文件。
   - **结论**：生产代码版本仍早于 PR-15/16。在执行 PR-17 的测试前，**必须先做一次完整的三子仓库（Entangled/novaic-common/novaic-business）同步部署**。

2. **生产 message_outbox 表是否存在**：
   - 勘测命令：`ssh root@api.gradievo.com "sqlite3 /opt/novaic/data/entangled.db '.schema message_outbox'"`
   - **结果**：输出为空。
   - **结论**：`message_outbox` 表尚未在生产创建，意味着 Entangled 侧也没跑过 PR-14 以后的更新。需要一同 rsync 并重启触发 schema 创建。

3. **当前 outbox 积压量**：
   - **结论**：由于表尚不存在，积压量为 0。

4. **生产 Business 日志的格式**：
   - 勘测命令：提取最新 business log 的前 20 行。
   - **结果**：日志为纯 ASCII 文本（例如 `2026-04-17 10:42:01,015 [INFO] business: Ready`）。
   - **结论**：可以完美被 `rg` 解析。

5. **`deploy-gateway.sh` 的同步范围**：
   - 勘测：查看源码。
   - **结果**：它目前通过 `GATEWAY_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"` 只同步了网关或特定的外层包，并不会自动完整同步 `novaic-common` 和 `Entangled` 到生产预期的全部位置。
   - **结论**：`deploy-business.sh` **需要独立编写，并明确 rsync `novaic-business/`、`Entangled/` 和 `novaic-common/` 三个子仓库**。

6. **压测脚本的隔离账号策略**：
   - 勘测命令：`sqlite3 ... "SELECT id FROM users WHERE id LIKE 'canary_u_%'"`
   - **结果**：输出为空，生产没有现成的隔离账号。
   - **结论**：Canary traffic 脚本在发压前需要包含一个引导（bootstrap）步骤。
   - **Bootstrap 方案**：
     通过脚本使用 `novaic-common` 中的 Entity/Internal API，在发压前动态注入 1 个 User Entity (`canary_u_fixed`) 和 5 个 Agent Entity (`canary_a_1` ~ `canary_a_5`)。并在压测结束后提供清理选项或保留以供后续使用。

7. **回滚 SLO 测量方法**：
   - **方法**：
     1. 在本地或测试机执行：
        ```bash
        time (
            NOVAIC_ENABLE_SUBSCRIBER="" bash scripts/start.sh --stop && \
            bash scripts/start.sh
        )
        ```
     2. 同时，开启另一个 terminal 追踪 `runtime` 和 `business` 日志：
        ```bash
        tail -F /opt/novaic/data/logs/business-$(date +%Y%m%d).log /opt/novaic/data/logs/runtime/health-worker-$(date +%Y%m%d).log | rg -e 'dispatch_subscriber disabled' -e 'event=health_fallback'
        ```
     3. 观察从 `time` 开始执行，到看到 `dispatch_subscriber disabled` 且 `health-worker` 出现第一条 `event=health_fallback`（成功接管）的总耗时是否 ≤ 30s。

---

## §阶段 0 演练预案

我理解必须获得此阶段预案批准后才能进行开发。开发完成并在本地验证 SLO 后，再次找你批复，之后才可进入生产。

1. **开发 B.1 和 B.2**：实现 `--enable-subscriber` 纯 CLI 控制，并确保可以按需传参给 Business。
2. **开发 B.3**：编写 `scripts/deploy-business.sh` 并使用 rsync 跨 3 个子仓库同步。
3. **开发 B.4**：实现 `scripts/canary/traffic.py` 压测脚本，并在逻辑前置加入账号 bootstrap 功能。
4. **撰写 B.5**：将四阶段的实施、回滚细则写入 `docs/runbooks/subscriber-canary.md`。

请确认以上调查报告与演练计划无误，批复后我即可进入 T1 开发与阶段 0 演练验证！
