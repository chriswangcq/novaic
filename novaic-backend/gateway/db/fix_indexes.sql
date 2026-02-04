-- Fix Missing Indexes for Performance
-- Date: 2026-02-04
-- Issue: message.route tasks getting stuck due to missing indexes

-- ========================================
-- 1. Add composite index for subagent lookups
-- ========================================
-- Used by: SubAgentRepository.get_by_id() 
-- Query: WHERE subagent_id = ? AND agent_id = ?
CREATE INDEX IF NOT EXISTS idx_subagents_id_agent 
ON subagents(subagent_id, agent_id);

-- ========================================
-- 2. Improve agent_runtimes index to include agent_id
-- ========================================
-- Used by: RuntimeRepository.get_active_runtime()
-- Query: WHERE subagent_id = ? AND agent_id = ? AND status IN ('active', 'resting')
-- 
-- Drop old index and create better one
DROP INDEX IF EXISTS idx_runtimes_subagent;
CREATE INDEX IF NOT EXISTS idx_runtimes_subagent_agent 
ON agent_runtimes(subagent_id, agent_id, status);

-- Alternative: Add agent_id to existing index (more specific)
-- CREATE INDEX IF NOT EXISTS idx_runtimes_subagent_full
-- ON agent_runtimes(subagent_id, agent_id, status, created_at DESC);

-- ========================================
-- Analyze tables to update statistics
-- ========================================
ANALYZE subagents;
ANALYZE agent_runtimes;
