-- ============================================
-- 验证 subagent_id 一致性修复
-- ============================================
-- 
-- 使用方法：
-- sqlite3 <your-database-path> < verify_subagent_id_fix.sql
--
-- 或者在应用中通过 SQLite 客户端执行
-- ============================================

-- 1. 查看最近的 think 和 tool 事件
SELECT 
    event_key,
    kind,
    subagent_id,
    status,
    datetime(created_at/1000, 'unixepoch') as created_time
FROM execution_logs
WHERE event_key LIKE 'think:%' OR event_key LIKE 'tool:%'
ORDER BY created_at DESC
LIMIT 20;

-- 2. 按 runtime_id 分组，检查同一个 runtime 的事件是否有一致的 subagent_id
-- 提取 runtime_id（从 event_key 中解析）
SELECT 
    CASE 
        WHEN event_key LIKE 'think:%' THEN substr(event_key, 7)
        WHEN event_key LIKE 'tool:%' THEN substr(event_key, 6, instr(substr(event_key, 6), ':') - 1)
        ELSE 'unknown'
    END as runtime_id,
    kind,
    subagent_id,
    COUNT(*) as event_count
FROM execution_logs
WHERE event_key LIKE 'think:%' OR event_key LIKE 'tool:%'
GROUP BY runtime_id, kind, subagent_id
ORDER BY MAX(created_at) DESC
LIMIT 30;

-- 3. 查找可能的不一致情况（同一个 runtime 有多个不同的 subagent_id）
WITH runtime_subagents AS (
    SELECT 
        CASE 
            WHEN event_key LIKE 'think:%' THEN substr(event_key, 7)
            WHEN event_key LIKE 'tool:%' THEN substr(event_key, 6, instr(substr(event_key, 6), ':') - 1)
            ELSE 'unknown'
        END as runtime_id,
        subagent_id,
        COUNT(*) as event_count
    FROM execution_logs
    WHERE (event_key LIKE 'think:%' OR event_key LIKE 'tool:%')
    GROUP BY runtime_id, subagent_id
)
SELECT 
    runtime_id,
    COUNT(DISTINCT subagent_id) as unique_subagent_count,
    GROUP_CONCAT(DISTINCT subagent_id) as subagent_ids
FROM runtime_subagents
GROUP BY runtime_id
HAVING COUNT(DISTINCT subagent_id) > 1
ORDER BY unique_subagent_count DESC;

-- 4. 统计修复前后的数据（如果有时间戳可以区分）
-- 假设修复时间点是 <timestamp>，你需要替换为实际时间
-- SELECT 
--     CASE 
--         WHEN created_at < <timestamp> THEN 'before_fix'
--         ELSE 'after_fix'
--     END as period,
--     COUNT(DISTINCT subagent_id) as unique_subagent_ids,
--     COUNT(*) as total_events
-- FROM execution_logs
-- WHERE event_key LIKE 'think:%' OR event_key LIKE 'tool:%'
-- GROUP BY period;
