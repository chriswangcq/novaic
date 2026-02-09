"""
时间工具模块 - 统一的 UTC 时间处理

原则：
1. 数据库统一存储 UTC，带时区标识（ISO 8601 with 'Z'）
2. 后端统一使用 UTC aware datetime
3. 仅在需要时转换为用户时区
"""

from datetime import datetime, timezone
from typing import Optional


def utc_now() -> datetime:
    """获取当前 UTC 时间（aware datetime）"""
    return datetime.now(timezone.utc)


def utc_now_iso() -> str:
    """生成带时区标识的 UTC 时间戳字符串
    
    格式: 2026-02-09T10:30:45.123456Z
    """
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'


def parse_iso(timestamp: str) -> datetime:
    """解析 ISO 时间戳（兼容无时区标识的旧数据）
    
    支持格式:
    - 2026-02-09T10:30:45.123456Z (带 Z)
    - 2026-02-09T10:30:45.123456+00:00 (带时区偏移)
    - 2026-02-09T10:30:45.123456 (无时区，假设 UTC)
    
    Returns:
        UTC aware datetime
    """
    if not timestamp:
        raise ValueError("Empty timestamp")
    
    # 标准化时区标识
    ts = timestamp.strip()
    if ts.endswith('Z'):
        ts = ts[:-1] + '+00:00'
    
    try:
        dt = datetime.fromisoformat(ts)
    except ValueError:
        # 尝试处理更多格式
        dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
    
    # 如果是 naive datetime，假设是 UTC
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    
    # 转换为 UTC
    return dt.astimezone(timezone.utc)


def to_user_timezone(dt: datetime, user_timezone: str) -> datetime:
    """将 datetime 转换为用户时区
    
    Args:
        dt: UTC datetime (aware)
        user_timezone: 时区名称，如 'Asia/Shanghai'
    
    Returns:
        用户时区的 aware datetime
    """
    from zoneinfo import ZoneInfo
    
    # 确保输入是 aware datetime
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    
    return dt.astimezone(ZoneInfo(user_timezone))


def format_for_display(dt: datetime, user_timezone: str, format_str: str = '%Y-%m-%d %H:%M') -> str:
    """格式化时间用于显示
    
    Args:
        dt: datetime (可以是 UTC 或任何时区)
        user_timezone: 用户时区
        format_str: 格式化字符串
    
    Returns:
        格式化后的时间字符串
    """
    local_dt = to_user_timezone(dt, user_timezone)
    return local_dt.strftime(format_str)


def humanize_duration(seconds: float) -> str:
    """将秒数转为人类可读的中文描述
    
    Args:
        seconds: 秒数（可以是负数，会取绝对值）
    
    Returns:
        中文描述，如 "5分钟", "2小时30分钟", "3天"
    """
    total_seconds = abs(int(seconds))
    
    if total_seconds < 60:
        return f"{total_seconds}秒"
    
    minutes = total_seconds // 60
    if minutes < 60:
        return f"{minutes}分钟"
    
    hours = minutes // 60
    remaining_minutes = minutes % 60
    if hours < 24:
        if remaining_minutes > 0:
            return f"{hours}小时{remaining_minutes}分钟"
        return f"{hours}小时"
    
    days = hours // 24
    remaining_hours = hours % 24
    if remaining_hours > 0:
        return f"{days}天{remaining_hours}小时"
    return f"{days}天"


def time_since(timestamp: str) -> str:
    """计算从某个时间戳到现在的时间差，返回人类可读描述
    
    Args:
        timestamp: ISO 格式时间戳
    
    Returns:
        中文描述，如 "5分钟前", "2小时前"
    """
    try:
        then = parse_iso(timestamp)
        now = utc_now()
        diff = (now - then).total_seconds()
        return humanize_duration(diff)
    except (ValueError, TypeError):
        return "未知"
