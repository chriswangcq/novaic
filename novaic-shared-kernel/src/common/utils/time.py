"""时间工具模块 - 统一的 UTC 时间处理"""

from datetime import datetime, timezone


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def parse_iso(timestamp: str) -> datetime:
    if not timestamp:
        raise ValueError("Empty timestamp")
    ts = timestamp.strip()
    if ts.endswith("Z"):
        ts = ts[:-1] + "+00:00"
    dt = datetime.fromisoformat(ts)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def to_user_timezone(dt: datetime, user_timezone: str) -> datetime:
    from zoneinfo import ZoneInfo

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(ZoneInfo(user_timezone))


def format_for_display(dt: datetime, user_timezone: str, format_str: str = "%Y-%m-%d %H:%M") -> str:
    return to_user_timezone(dt, user_timezone).strftime(format_str)


def humanize_duration(seconds: float) -> str:
    total_seconds = abs(int(seconds))
    if total_seconds < 60:
        return f"{total_seconds}秒"
    minutes = total_seconds // 60
    if minutes < 60:
        return f"{minutes}分钟"
    hours = minutes // 60
    remaining_minutes = minutes % 60
    if hours < 24:
        return f"{hours}小时{remaining_minutes}分钟" if remaining_minutes > 0 else f"{hours}小时"
    days = hours // 24
    remaining_hours = hours % 24
    return f"{days}天{remaining_hours}小时" if remaining_hours > 0 else f"{days}天"


def time_since(timestamp: str) -> str:
    try:
        then = parse_iso(timestamp)
        now = utc_now()
        return humanize_duration((now - then).total_seconds())
    except (ValueError, TypeError):
        return "未知"
