"""
MessageRepository - 消息仓库

简化的消息操作，只管已读/未读状态。
消息是 Agent 环境的一部分，不是"任务"。
"""

import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import uuid4


class MessageRepository:
    """
    消息仓库 - 只管已读/未读
    
    消息存储在 chat_messages 表中，只有 read 字段表示状态。
    """
    
    def __init__(self, db):
        self.db = db
    
    async def add_message(
        self,
        agent_id: str,
        type: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        id: Optional[str] = None,
        timestamp: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        添加消息（默认未读）
        
        Args:
            agent_id: Agent ID
            type: 消息类型 (USER_MESSAGE, AGENT_REPLY, SYSTEM_MESSAGE)
            content: 消息内容
            metadata: 元数据
            id: 可选的消息 ID（不提供则自动生成）
            timestamp: 可选的时间戳（不提供则使用当前时间）
        
        Returns:
            创建的消息
        """
        msg_id = id or str(uuid4())[:12]
        timestamp = timestamp or datetime.now().isoformat()
        
        await self.db.execute(
            """INSERT INTO chat_messages 
               (id, agent_id, type, content, read, metadata, timestamp, created_at)
               VALUES (?, ?, ?, ?, 0, ?, ?, ?)""",
            (msg_id, agent_id, type, content, json.dumps(metadata or {}), timestamp, timestamp)
        )
        await self.db.commit()
        
        return {
            "id": msg_id,
            "agent_id": agent_id,
            "type": type,
            "content": content,
            "read": 0,
            "metadata": metadata or {},
            "timestamp": timestamp,
        }
    
    async def get_unread(self, agent_id: str) -> List[Dict[str, Any]]:
        """
        获取未读消息
        
        Args:
            agent_id: Agent ID
        
        Returns:
            未读消息列表（按时间排序）
        """
        rows = await self.db.fetchall(
            """SELECT * FROM chat_messages 
               WHERE agent_id = ? AND read = 0 
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
                "metadata": json.loads(row["metadata"] or "{}"),
                "timestamp": row["timestamp"],
            }
            for row in rows
        ]
    
    async def mark_read(self, message_id: str):
        """
        标记消息为已读
        
        Args:
            message_id: 消息 ID
        """
        await self.db.execute(
            "UPDATE chat_messages SET read = 1 WHERE id = ?",
            (message_id,)
        )
        await self.db.commit()
    
    async def mark_all_read(self, agent_id: str):
        """
        标记所有消息为已读
        
        Args:
            agent_id: Agent ID
        """
        await self.db.execute(
            "UPDATE chat_messages SET read = 1 WHERE agent_id = ? AND read = 0",
            (agent_id,)
        )
        await self.db.commit()
    
    async def get_unread_count(self, agent_id: str) -> int:
        """
        获取未读消息数量
        
        Args:
            agent_id: Agent ID
        
        Returns:
            未读消息数量
        """
        result = await self.db.fetchone(
            "SELECT COUNT(*) as count FROM chat_messages WHERE agent_id = ? AND read = 0",
            (agent_id,)
        )
        return result["count"] if result else 0
    
    async def get_history(
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
        rows = await self.db.fetchall(
            """SELECT * FROM chat_messages 
               WHERE agent_id = ? 
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
                "metadata": json.loads(row["metadata"] or "{}"),
                "timestamp": row["timestamp"],
            }
            for row in rows
        ]
    
    async def get_message(self, message_id: str) -> Optional[Dict[str, Any]]:
        """
        获取单条消息
        
        Args:
            message_id: 消息 ID
        
        Returns:
            消息或 None
        """
        row = await self.db.fetchone(
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
            "metadata": json.loads(row["metadata"] or "{}"),
            "timestamp": row["timestamp"],
        }
