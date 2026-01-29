"""
Result Cache - 结果缓存与分段查询

解决长结果撑爆上下文的问题：
1. 自动截断超长结果，保留首尾
2. 缓存完整结果，提供分段查询
3. 支持按行数或字符数分段
"""

import hashlib
import time
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
from collections import OrderedDict


class ResultCache:
    """结果缓存管理器"""
    
    # 默认配置
    MAX_RESULT_LENGTH = 4000  # 最大返回字符数
    HEAD_LENGTH = 1500        # 截断时保留的头部字符数
    TAIL_LENGTH = 1500        # 截断时保留的尾部字符数
    MAX_CACHE_SIZE = 100      # 最大缓存条目数
    CACHE_TTL = 3600          # 缓存过期时间（秒）
    
    def __init__(self):
        # 使用 OrderedDict 实现 LRU 缓存
        self._cache: OrderedDict[str, Dict[str, Any]] = OrderedDict()
    
    def _generate_id(self, content: str) -> str:
        """生成结果 ID"""
        # 使用内容哈希 + 时间戳生成唯一 ID
        hash_part = hashlib.md5(content.encode()).hexdigest()[:8]
        time_part = hex(int(time.time() * 1000))[-6:]
        return f"r_{hash_part}_{time_part}"
    
    def _cleanup_expired(self):
        """清理过期缓存"""
        now = time.time()
        expired_keys = [
            k for k, v in self._cache.items()
            if now - v["created_at"] > self.CACHE_TTL
        ]
        for k in expired_keys:
            del self._cache[k]
    
    def _enforce_size_limit(self):
        """强制缓存大小限制"""
        while len(self._cache) > self.MAX_CACHE_SIZE:
            self._cache.popitem(last=False)  # 移除最旧的
    
    def store_and_truncate(
        self,
        content: str,
        max_length: Optional[int] = None,
        head_length: Optional[int] = None,
        tail_length: Optional[int] = None
    ) -> Tuple[str, Optional[str], Optional[Dict[str, Any]]]:
        """
        存储内容并在需要时截断
        
        Args:
            content: 原始内容
            max_length: 最大长度（可选，默认 4000）
            head_length: 头部保留长度（可选）
            tail_length: 尾部保留长度（可选）
        
        Returns:
            (处理后的内容, 结果ID或None, 缓存元信息或None)
        """
        max_len = max_length or self.MAX_RESULT_LENGTH
        head_len = head_length or self.HEAD_LENGTH
        tail_len = tail_length or self.TAIL_LENGTH
        
        # 如果内容不超长，直接返回
        if len(content) <= max_len:
            return content, None, None
        
        # 生成 ID 并缓存
        result_id = self._generate_id(content)
        
        # 计算行数
        lines = content.split('\n')
        total_lines = len(lines)
        total_chars = len(content)
        
        # 缓存完整内容
        self._cache[result_id] = {
            "content": content,
            "lines": lines,
            "total_lines": total_lines,
            "total_chars": total_chars,
            "created_at": time.time(),
            "created_time": datetime.now().isoformat()
        }
        
        # 清理和限制
        self._cleanup_expired()
        self._enforce_size_limit()
        
        # 截断内容
        truncated = self._truncate_content(content, head_len, tail_len, result_id, total_lines, total_chars)
        
        meta = {
            "result_id": result_id,
            "total_lines": total_lines,
            "total_chars": total_chars,
            "truncated": True,
            "hint": f"结果已截断。使用 result_get(result_id='{result_id}', ...) 查询完整内容"
        }
        
        return truncated, result_id, meta
    
    def _truncate_content(
        self,
        content: str,
        head_len: int,
        tail_len: int,
        result_id: str,
        total_lines: int,
        total_chars: int
    ) -> str:
        """截断内容，保留首尾"""
        head = content[:head_len]
        tail = content[-tail_len:]
        
        # 尝试在换行处截断，使输出更整洁
        if '\n' in head[head_len//2:]:
            head = head[:head.rfind('\n', head_len//2) + 1]
        if '\n' in tail[:tail_len//2]:
            tail = tail[tail.find('\n', 0) + 1:]
        
        omitted_chars = total_chars - len(head) - len(tail)
        
        separator = f"""

... [已省略 {omitted_chars} 字符 / 约 {total_lines - head.count(chr(10)) - tail.count(chr(10))} 行] ...
... [结果ID: {result_id}] ...
... [使用 result_get(result_id='{result_id}', start_line=N, end_line=M) 查询完整内容] ...

"""
        return head + separator + tail
    
    def get_by_lines(
        self,
        result_id: str,
        start_line: int = 1,
        end_line: Optional[int] = None,
        max_lines: int = 100
    ) -> Dict[str, Any]:
        """
        按行数范围获取缓存内容
        
        Args:
            result_id: 结果 ID
            start_line: 起始行（从 1 开始）
            end_line: 结束行（包含），None 表示到末尾
            max_lines: 最大返回行数
        """
        if result_id not in self._cache:
            return {
                "success": False,
                "error": f"结果 ID 不存在或已过期: {result_id}"
            }
        
        cached = self._cache[result_id]
        lines = cached["lines"]
        total_lines = cached["total_lines"]
        
        # 调整索引（用户使用 1-based）
        start_idx = max(0, start_line - 1)
        
        if end_line is None:
            end_idx = min(start_idx + max_lines, total_lines)
        else:
            end_idx = min(end_line, total_lines, start_idx + max_lines)
        
        selected_lines = lines[start_idx:end_idx]
        
        # 移动到最近使用
        self._cache.move_to_end(result_id)
        
        return {
            "success": True,
            "result_id": result_id,
            "content": '\n'.join(selected_lines),
            "lines_returned": len(selected_lines),
            "line_range": f"{start_idx + 1}-{end_idx}",
            "total_lines": total_lines,
            "has_more": end_idx < total_lines,
            "next_start": end_idx + 1 if end_idx < total_lines else None
        }
    
    def get_by_chars(
        self,
        result_id: str,
        start_char: int = 0,
        length: Optional[int] = None,
        max_length: int = 4000
    ) -> Dict[str, Any]:
        """
        按字符范围获取缓存内容
        
        Args:
            result_id: 结果 ID
            start_char: 起始字符位置（从 0 开始）
            length: 获取长度，None 表示使用 max_length
            max_length: 最大返回字符数
        """
        if result_id not in self._cache:
            return {
                "success": False,
                "error": f"结果 ID 不存在或已过期: {result_id}"
            }
        
        cached = self._cache[result_id]
        content = cached["content"]
        total_chars = cached["total_chars"]
        
        # 计算范围
        start = max(0, start_char)
        actual_length = min(length or max_length, max_length)
        end = min(start + actual_length, total_chars)
        
        selected = content[start:end]
        
        # 移动到最近使用
        self._cache.move_to_end(result_id)
        
        return {
            "success": True,
            "result_id": result_id,
            "content": selected,
            "chars_returned": len(selected),
            "char_range": f"{start}-{end}",
            "total_chars": total_chars,
            "has_more": end < total_chars,
            "next_start": end if end < total_chars else None
        }
    
    def get_info(self, result_id: str) -> Dict[str, Any]:
        """获取缓存结果的元信息"""
        if result_id not in self._cache:
            return {
                "success": False,
                "error": f"结果 ID 不存在或已过期: {result_id}"
            }
        
        cached = self._cache[result_id]
        
        return {
            "success": True,
            "result_id": result_id,
            "total_lines": cached["total_lines"],
            "total_chars": cached["total_chars"],
            "created_time": cached["created_time"],
            "preview_head": cached["content"][:200] + "..." if len(cached["content"]) > 200 else cached["content"],
            "preview_tail": "..." + cached["content"][-200:] if len(cached["content"]) > 200 else ""
        }
    
    def list_cached(self) -> Dict[str, Any]:
        """列出所有缓存的结果"""
        self._cleanup_expired()
        
        items = []
        for result_id, cached in self._cache.items():
            items.append({
                "result_id": result_id,
                "total_lines": cached["total_lines"],
                "total_chars": cached["total_chars"],
                "created_time": cached["created_time"]
            })
        
        return {
            "success": True,
            "cached_results": items,
            "count": len(items)
        }
    
    def delete(self, result_id: str) -> Dict[str, Any]:
        """删除缓存结果"""
        if result_id in self._cache:
            del self._cache[result_id]
            return {"success": True, "message": f"已删除: {result_id}"}
        return {"success": False, "error": f"结果 ID 不存在: {result_id}"}


# 单例实例
_result_cache = None

def get_result_cache() -> ResultCache:
    """获取 ResultCache 单例"""
    global _result_cache
    if _result_cache is None:
        _result_cache = ResultCache()
    return _result_cache


def truncate_if_needed(content: str, max_length: int = 4000) -> Tuple[str, Optional[Dict[str, Any]]]:
    """
    便捷函数：如果内容超长则截断并缓存
    
    Returns:
        (处理后的内容, 元信息或None)
    """
    cache = get_result_cache()
    truncated, result_id, meta = cache.store_and_truncate(content, max_length)
    return truncated, meta
