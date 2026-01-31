"""
MCP Execution Repository

Handles mcp_executions database operations for idempotency guarantee.
Prevents duplicate execution of non-reentrant MCP tools by tracking
execution status via idempotency keys.

v11: Created for multi-process architecture.
"""

import json
from typing import Optional, List, Dict, Any
from datetime import datetime

from ..database import Database


class MCPExecutionRepository:
    """Repository for MCP execution records (idempotency tracking)."""
    
    def __init__(self, db: Database):
        self.db = db
    
    # ==================== Execution Creation ====================
    
    async def create(
        self,
        idempotency_key: str,
        agent_id: str,
        subagent_id: str,
        round_id: str,
        mcpcall_id: str,
        tool_name: str,
        args: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Create a new MCP execution record.
        
        Args:
            idempotency_key: Combined key (agent_id-subagent_id-round_id-mcpcall_id)
            agent_id: Agent ID
            subagent_id: Runtime instance ID
            round_id: Round ID
            mcpcall_id: MCP call ID
            tool_name: MCP tool name
            args: Tool arguments
        
        Returns:
            The created execution record
        """
        created_at = datetime.now().isoformat()
        
        await self.db.execute(
            """INSERT INTO mcp_executions 
               (idempotency_key, agent_id, subagent_id, round_id, mcpcall_id,
                tool_name, args, status, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, 'executing', ?)""",
            (
                idempotency_key,
                agent_id,
                subagent_id,
                round_id,
                mcpcall_id,
                tool_name,
                json.dumps(args or {}),
                created_at,
            )
        )
        await self.db.commit()
        
        return await self.get(idempotency_key)
    
    async def get_or_create(
        self,
        idempotency_key: str,
        agent_id: str,
        subagent_id: str,
        round_id: str,
        mcpcall_id: str,
        tool_name: str,
        args: Optional[Dict[str, Any]] = None,
    ) -> tuple[Dict[str, Any], bool]:
        """
        Get existing execution or create new one.
        
        Returns:
            Tuple of (execution_record, was_created)
        """
        existing = await self.get(idempotency_key)
        if existing:
            return existing, False
        
        execution = await self.create(
            idempotency_key=idempotency_key,
            agent_id=agent_id,
            subagent_id=subagent_id,
            round_id=round_id,
            mcpcall_id=mcpcall_id,
            tool_name=tool_name,
            args=args,
        )
        return execution, True
    
    # ==================== Execution Retrieval ====================
    
    async def get(self, idempotency_key: str) -> Optional[Dict[str, Any]]:
        """Get an execution record by idempotency key."""
        row = await self.db.fetchone(
            "SELECT * FROM mcp_executions WHERE idempotency_key = ?",
            (idempotency_key,)
        )
        if row:
            return self._row_to_execution(row)
        return None
    
    async def get_by_agent(
        self,
        agent_id: str,
        subagent_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get execution records for an agent."""
        query = "SELECT * FROM mcp_executions WHERE agent_id = ?"
        params: List[Any] = [agent_id]
        
        if subagent_id:
            query += " AND subagent_id = ?"
            params.append(subagent_id)
        
        if status:
            query += " AND status = ?"
            params.append(status)
        
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        
        rows = await self.db.fetchall(query, tuple(params))
        return [self._row_to_execution(row) for row in rows]
    
    async def get_executing(
        self,
        timeout_minutes: int = 10,
    ) -> List[Dict[str, Any]]:
        """Get executions that have been executing for too long."""
        rows = await self.db.fetchall(
            """SELECT * FROM mcp_executions 
               WHERE status = 'executing'
               AND created_at < datetime('now', '-' || ? || ' minutes')""",
            (timeout_minutes,)
        )
        return [self._row_to_execution(row) for row in rows]
    
    # ==================== Execution Updates ====================
    
    async def complete(
        self,
        idempotency_key: str,
        result: Any,
    ) -> bool:
        """
        Mark an execution as done.
        
        Args:
            idempotency_key: Execution key
            result: Execution result
        
        Returns:
            True if updated
        """
        executed_at = datetime.now().isoformat()
        
        cursor = await self.db.execute(
            """UPDATE mcp_executions 
               SET status = 'done', result = ?, executed_at = ?
               WHERE idempotency_key = ?""",
            (json.dumps(result) if result is not None else None, executed_at, idempotency_key)
        )
        await self.db.commit()
        
        return cursor.rowcount > 0
    
    async def fail(
        self,
        idempotency_key: str,
        error: str,
    ) -> bool:
        """
        Mark an execution as failed.
        
        Args:
            idempotency_key: Execution key
            error: Error message
        
        Returns:
            True if updated
        """
        executed_at = datetime.now().isoformat()
        
        cursor = await self.db.execute(
            """UPDATE mcp_executions 
               SET status = 'failed', error = ?, executed_at = ?
               WHERE idempotency_key = ?""",
            (error, executed_at, idempotency_key)
        )
        await self.db.commit()
        
        return cursor.rowcount > 0
    
    async def timeout(self, idempotency_key: str) -> bool:
        """
        Mark an execution as timed out.
        
        Note: The actual result may arrive later via callback.
        Use get() to check for late results.
        
        Args:
            idempotency_key: Execution key
        
        Returns:
            True if updated
        """
        executed_at = datetime.now().isoformat()
        
        cursor = await self.db.execute(
            """UPDATE mcp_executions 
               SET status = 'timeout', executed_at = ?
               WHERE idempotency_key = ? AND status = 'executing'""",
            (executed_at, idempotency_key)
        )
        await self.db.commit()
        
        return cursor.rowcount > 0
    
    async def update_late_result(
        self,
        idempotency_key: str,
        result: Any,
    ) -> bool:
        """
        Update result for a timed-out execution.
        
        This handles the case where MCP completes after we timed out.
        
        Args:
            idempotency_key: Execution key
            result: Late-arriving result
        
        Returns:
            True if updated
        """
        executed_at = datetime.now().isoformat()
        
        cursor = await self.db.execute(
            """UPDATE mcp_executions 
               SET status = 'done', result = ?, executed_at = ?
               WHERE idempotency_key = ? AND status = 'timeout'""",
            (json.dumps(result) if result is not None else None, executed_at, idempotency_key)
        )
        await self.db.commit()
        
        return cursor.rowcount > 0
    
    # ==================== Idempotency Check ====================
    
    async def check_idempotent(
        self,
        idempotency_key: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Check if an execution has already completed.
        
        Used for idempotent execution:
        - If status='done': return cached result
        - If status='failed': return cached error
        - If status='executing': wait or return status
        - If not found: proceed with execution
        
        Args:
            idempotency_key: Execution key
        
        Returns:
            Execution record if exists, None if should proceed
        """
        return await self.get(idempotency_key)
    
    async def is_done(self, idempotency_key: str) -> bool:
        """Check if an execution is done (success or failure)."""
        row = await self.db.fetchone(
            """SELECT status FROM mcp_executions 
               WHERE idempotency_key = ? AND status IN ('done', 'failed')""",
            (idempotency_key,)
        )
        return row is not None
    
    async def is_executing(self, idempotency_key: str) -> bool:
        """Check if an execution is currently in progress."""
        row = await self.db.fetchone(
            """SELECT status FROM mcp_executions 
               WHERE idempotency_key = ? AND status = 'executing'""",
            (idempotency_key,)
        )
        return row is not None
    
    # ==================== Recovery ====================
    
    async def mark_stale_as_timeout(
        self,
        timeout_minutes: int = 10,
    ) -> int:
        """
        Mark old executing records as timed out.
        
        Args:
            timeout_minutes: Timeout threshold
        
        Returns:
            Number of records marked as timeout
        """
        executed_at = datetime.now().isoformat()
        
        cursor = await self.db.execute(
            """UPDATE mcp_executions 
               SET status = 'timeout', executed_at = ?
               WHERE status = 'executing'
               AND created_at < datetime('now', '-' || ? || ' minutes')""",
            (executed_at, timeout_minutes)
        )
        await self.db.commit()
        
        return cursor.rowcount
    
    # ==================== Cleanup ====================
    
    async def cleanup_old_executions(
        self,
        agent_id: str,
        keep_count: int = 1000,
    ) -> int:
        """Delete old execution records, keeping the most recent ones."""
        cursor = await self.db.execute(
            """DELETE FROM mcp_executions 
               WHERE agent_id = ? 
               AND idempotency_key NOT IN (
                   SELECT idempotency_key FROM mcp_executions 
                   WHERE agent_id = ?
                   ORDER BY created_at DESC 
                   LIMIT ?
               )""",
            (agent_id, agent_id, keep_count)
        )
        await self.db.commit()
        return cursor.rowcount
    
    # ==================== Helper Methods ====================
    
    def _row_to_execution(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """Convert a database row to an execution dict."""
        args = {}
        if row.get("args"):
            try:
                args = json.loads(row["args"])
            except json.JSONDecodeError:
                pass
        
        result = None
        if row.get("result"):
            try:
                result = json.loads(row["result"])
            except json.JSONDecodeError:
                result = row["result"]
        
        return {
            "idempotency_key": row["idempotency_key"],
            "agent_id": row["agent_id"],
            "subagent_id": row["subagent_id"],
            "round_id": row["round_id"],
            "mcpcall_id": row["mcpcall_id"],
            "tool_name": row["tool_name"],
            "args": args,
            "status": row["status"],
            "result": result,
            "error": row.get("error"),
            "created_at": row["created_at"],
            "executed_at": row.get("executed_at"),
        }
