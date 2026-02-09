"""
MessageRepository - 消息仓库

简化的消息操作，只管已读/未读状态。
消息是 Agent 环境的一部分，不是"任务"。

v18: Event-driven Monitor
- 添加 status 字段：sending (待处理) / sent (已确认)
- Monitor 服务消费 sending 队列
"""

import json
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from uuid import uuid4

from common.config import ServiceConfig
from common.utils.time import utc_now_iso


class MessageRepository:
    """
    消息仓库 - 管理消息状态
    
    消息存储在 chat_messages 表中：
    - read: 0=未读, 1=已读（用于 Agent 消费）
    - status: sending/sent（用于 Monitor 消费队列）
    """
    
    def __init__(self, db):
        self.db = db
    
    def add_message(
        self,
        agent_id: str,
        type: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        id: Optional[str] = None,
        timestamp: Optional[str] = None,
        status: str = "sending",  # v18: 默认 sending，Monitor 会改成 sent
    ) -> Dict[str, Any]:
        """
        添加消息（默认未读，状态为 sending）
        
        Args:
            agent_id: Agent ID
            type: 消息类型 (USER_MESSAGE, AGENT_REPLY, SYSTEM_MESSAGE)
            content: 消息内容
            metadata: 元数据
            id: 可选的消息 ID（不提供则自动生成）
            timestamp: 可选的时间戳（不提供则使用当前时间）
            status: 消息状态 (sending/sent)，用户消息默认 sending
        
        Returns:
            创建的消息
        """
        msg_id = id or str(uuid4())[:12]
        timestamp = timestamp or utc_now_iso()
        
        with self.db.transaction("message", resource_id=msg_id):
            self.db.execute(
                """INSERT INTO chat_messages 
                   (id, agent_id, type, content, read, metadata, timestamp, created_at, status)
                   VALUES (?, ?, ?, ?, 0, ?, ?, ?, ?)""",
                (msg_id, agent_id, type, content, json.dumps(metadata or {}), timestamp, timestamp, status)
            )
        
        return {
            "id": msg_id,
            "agent_id": agent_id,
            "type": type,
            "content": content,
            "read": 0,
            "status": status,
            "metadata": metadata or {},
            "timestamp": timestamp,
        }
    
    # ========================================
    # Monitor Queue Operations (v18)
    # ========================================
    
    def claim_sending(self) -> Optional[Dict[str, Any]]:
        """
        CAS 认领一条 sending 状态的消息。
        
        原子操作：sending → sent
        
        Returns:
            认领成功的消息，或 None（队列为空）
        """
        # 全局锁：因为需要先查询再更新，涉及多条记录的竞争
        with self.db.transaction("global") as conn:
            # 1. 查找一条 sending 消息
            cursor = conn.execute(
                """SELECT id, agent_id, type, content, metadata, timestamp
                   FROM chat_messages 
                   WHERE status = 'sending' 
                   ORDER BY created_at ASC 
                   LIMIT 1"""
            )
            row = cursor.fetchone()
            
            if not row:
                return None
            
            msg_id = row[0]
            
            # 2. CAS 更新：sending → sent
            now = utc_now_iso()
            cursor = conn.execute(
                """UPDATE chat_messages 
                   SET status = 'sent', claimed_at = ?
                   WHERE id = ? AND status = 'sending'""",
                (now, msg_id)
            )
            # transaction 自动 commit
            
            # 3. 检查是否成功认领
            if cursor.rowcount == 0:
                return None  # 被其他 worker 抢走了
            
            return {
                "id": msg_id,
                "agent_id": row[1],
                "type": row[2],
                "content": row[3],
                "metadata": json.loads(row[4] or "{}"),
                "timestamp": row[5],
            }
    
    def get_sending_count(self) -> int:
        """获取 sending 状态的消息数量（用于监控）。"""
        result = self.db.fetchone(
            "SELECT COUNT(*) as count FROM chat_messages WHERE status = 'sending'"
        )
        return result["count"] if result else 0
    
    def reset_stuck_sending(self, timeout_seconds: int = 60) -> int:
        """
        重置卡住的 sending 消息（用于 Health 恢复）。
        
        如果消息在 sending 状态超过 timeout_seconds 秒，可能是处理失败，
        这里不重置，而是由 Health 监控并告警。
        
        Returns:
            卡住的消息数量
        """
        # 只统计，不自动重置（sending 消息应该很快被处理）
        result = self.db.fetchone(
            """SELECT COUNT(*) as count FROM chat_messages 
               WHERE status = 'sending' 
               AND datetime(created_at, '+' || ? || ' seconds') < datetime('now')""",
            (timeout_seconds,)
        )
        return result["count"] if result else 0
    
    def get_unread(self, agent_id: str) -> List[Dict[str, Any]]:
        """
        获取未读消息（只返回已确认 sent 的消息）
        
        Args:
            agent_id: Agent ID
        
        Returns:
            未读消息列表（按时间排序）
        """
        rows = self.db.fetchall(
            """SELECT * FROM chat_messages 
               WHERE agent_id = ? AND read = 0 AND status = 'sent'
               ORDER BY timestamp ASC""",
            (agent_id,)
        )
        
        return [
            {
                "id": row["id"],
                "agent_id": row["agent_id"],
                "type": row["type"],
                "content": row["content"],
                "read": row["read"],
                "status": row.get("status", "sent"),
                "metadata": json.loads(row["metadata"] or "{}"),
                "timestamp": row["timestamp"],
            }
            for row in rows
        ]

    def get_pending_unclaimed(
        self,
        agent_id: str,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        获取未认领且未读的消息（用于 Inbox 汇总）
        """
        rows = self.db.fetchall(
            """SELECT id, type, content, timestamp
               FROM chat_messages
               WHERE agent_id = ? AND claimed_by IS NULL AND read = 0
               ORDER BY timestamp DESC LIMIT ?""",
            (agent_id, limit),
        )

        return [
            {
                "id": row["id"],
                "type": row["type"],
                "content": row["content"],
                "timestamp": row["timestamp"],
            }
            for row in rows
        ]
    
    def mark_read(self, message_id: str):
        """
        标记消息为已读
        
        Args:
            message_id: 消息 ID
        """
        with self.db.transaction("message", resource_id=message_id):
            self.db.execute(
                "UPDATE chat_messages SET read = 1 WHERE id = ?",
                (message_id,)
            )
    
    def mark_all_read(self, agent_id: str):
        """
        标记所有消息为已读
        
        Args:
            agent_id: Agent ID
        """
        # 批量操作使用 agent 级别锁
        with self.db.transaction("agent", resource_id=agent_id):
            self.db.execute(
                "UPDATE chat_messages SET read = 1 WHERE agent_id = ? AND read = 0",
                (agent_id,)
            )
    
    def get_unread_count(self, agent_id: str) -> int:
        """
        获取未读消息数量
        
        Args:
            agent_id: Agent ID
        
        Returns:
            未读消息数量
        """
        result = self.db.fetchone(
            "SELECT COUNT(*) as count FROM chat_messages WHERE agent_id = ? AND read = 0",
            (agent_id,)
        )
        return result["count"] if result else 0
    
    def get_history(
        self,
        agent_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        获取历史消息（用于 UI 显示）
        
        Args:
            agent_id: Agent ID
            limit: 最大数量
            offset: 偏移量
        
        Returns:
            消息列表（按时间倒序）
        """
        rows = self.db.fetchall(
            """SELECT * FROM chat_messages 
               WHERE agent_id = ? AND type != 'SYSTEM_WAKE'
               ORDER BY timestamp DESC 
               LIMIT ? OFFSET ?""",
            (agent_id, limit, offset)
        )
        
        return [
            {
                "id": row["id"],
                "agent_id": row["agent_id"],
                "type": row["type"],
                "content": row["content"],
                "read": row["read"],
                "status": row.get("status", "sent"),
                "metadata": json.loads(row["metadata"] or "{}"),
                "timestamp": row["timestamp"],
            }
            for row in rows
        ]
    
    def get_message(self, message_id: str) -> Optional[Dict[str, Any]]:
        """
        获取单条消息
        
        Args:
            message_id: 消息 ID
        
        Returns:
            消息或 None
        """
        row = self.db.fetchone(
            "SELECT * FROM chat_messages WHERE id = ?",
            (message_id,)
        )
        
        if not row:
            return None
        
        return {
            "id": row["id"],
            "agent_id": row["agent_id"],
            "type": row["type"],
            "content": row["content"],
            "read": row["read"],
            "status": row.get("status", "sent"),
            "metadata": json.loads(row["metadata"] or "{}"),
            "timestamp": row["timestamp"],
        }
    
    def claim_by_id(self, message_id: str) -> bool:
        """
        按 ID 认领消息（CAS 操作）
        
        原子操作：sending → sent
        
        Args:
            message_id: 消息 ID
        
        Returns:
            True 如果认领成功，False 如果消息不存在或已被认领
        """
        with self.db.transaction("message", resource_id=message_id, timeout=ServiceConfig.DB_TRANSACTION_TIMEOUT):
            cursor = self.db.execute(
                """UPDATE chat_messages
                   SET status = 'sent'
                   WHERE id = ? AND status = 'sending'""",
                (message_id,)
            )
        
        return cursor.rowcount > 0
    
    def batch_mark_read(
        self,
        message_ids: List[str],
        agent_id: Optional[str] = None,
    ) -> int:
        """
        批量标记消息为已读
        
        Args:
            message_ids: 消息 ID 列表
            agent_id: 可选的 Agent ID（用于确定锁范围，如果不提供则使用全局锁）
        
        Returns:
            更新的消息数量
        """
        if not message_ids:
            return 0
        
        placeholders = ",".join(["?"] * len(message_ids))
        
        # 批量更新使用全局锁以保证原子性
        with self.db.transaction("global", timeout=ServiceConfig.DB_TRANSACTION_TIMEOUT_LONG):
            cursor = self.db.execute(
                f"UPDATE chat_messages SET read = 1 WHERE id IN ({placeholders})",
                tuple(message_ids)
            )
        
        return cursor.rowcount
    
    def get_unread_user_message_count(self, agent_id: str) -> int:
        """
        统计未读用户消息数量
        
        Args:
            agent_id: Agent ID
        
        Returns:
            未读 USER_MESSAGE 类型消息的数量
        """
        result = self.db.fetchone(
            """SELECT COUNT(*) as count FROM chat_messages 
               WHERE agent_id = ? AND read = 0 AND type = 'USER_MESSAGE'""",
            (agent_id,)
        )
        return result["count"] if result else 0
    
    def get_pending_count(self, agent_id: str) -> int:
        """
        统计待处理消息数量（已发送但未读的用户消息）
        
        Args:
            agent_id: Agent ID
        
        Returns:
            待处理消息数量
        """
        result = self.db.fetchone(
            """SELECT COUNT(*) as count FROM chat_messages
               WHERE agent_id = ? AND type = 'USER_MESSAGE' AND status = 'sent' AND read = 0""",
            (agent_id,)
        )
        return result["count"] if result else 0