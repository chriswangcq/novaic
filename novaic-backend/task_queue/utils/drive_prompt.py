"""
Drive Prompt Builder - 构建定时唤醒的 Agent 自驱力 Prompt

当 Agent 被 SchedulerWorker 定时唤醒（trigger_type=scheduled_wake）时，
此模块构建一段系统 Prompt，注入 Agent 的驱动力、用户画像、笔记本摘要等信息，
引导 Agent 自主决策要做什么。

v2: 改为"主动巡查"模式（参考 OpenClaw HEARTBEAT.md 设计）
- 检查清单模式，而非被动等待
- 移除硬编码的 30 分钟冷却限制
- 支持用户配置的 heartbeat_md
- 添加 HEARTBEAT_OK 协议
"""

import json
from datetime import datetime
from typing import List, Dict, Any, Optional

from common.utils.time import utc_now, parse_iso, to_user_timezone, humanize_duration as humanize_seconds, format_for_display
from ..client import GatewayInternalClient


# 默认检查清单（当用户未配置 heartbeat_md 时使用）
DEFAULT_HEARTBEAT_MD = """# 检查清单

## 每次唤醒都检查
- 笔记本中有 status=ready 的内容吗？

## 轮换检查（每天 2-3 次）
- 用户关心的新闻/价格有变化吗？
- 有什么有趣的发现可以分享？

## 定期检查（每天 1 次）
- 回顾最近对话和笔记本，有什么值得长期记住的？
- 如果有新的 insight/reflection，用 memory_update 整理到 MEMORY.md
- 如果发现了用户的新偏好/习惯，用 memory_update 更新 USER.md
"""


def check_active_hours(now_utc: datetime, start: str, end: str, timezone: str) -> bool:
    """
    检查当前时间是否在用户活跃时间内
    
    Args:
        now_utc: 当前 UTC 时间
        start: 开始时间 (HH:MM 格式)
        end: 结束时间 (HH:MM 格式)
        timezone: 时区 (如 'Asia/Shanghai')
    
    Returns:
        是否在活跃时间内
    """
    try:
        from zoneinfo import ZoneInfo
        
        # 转换到用户时区
        user_tz = ZoneInfo(timezone)
        now_local = now_utc.replace(tzinfo=ZoneInfo('UTC')).astimezone(user_tz)
        
        # 解析开始和结束时间
        start_hour, start_min = map(int, start.split(':'))
        end_hour, end_min = map(int, end.split(':'))
        
        current_minutes = now_local.hour * 60 + now_local.minute
        start_minutes = start_hour * 60 + start_min
        end_minutes = end_hour * 60 + end_min
        
        # 处理跨夜情况 (如 22:00 - 06:00)
        if end_minutes <= start_minutes:
            # 跨夜：当前时间在开始之后 OR 在结束之前
            return current_minutes >= start_minutes or current_minutes < end_minutes
        else:
            # 正常：当前时间在开始和结束之间
            return start_minutes <= current_minutes < end_minutes
    except Exception as e:
        print(f"[drive_prompt] Failed to check active hours: {e}")
        return True  # 出错时默认为活跃


def build_drive_prompt(agent_id: str, client: GatewayInternalClient) -> str:
    """
    构建定时唤醒的 Drive Prompt（主动巡查模式）
    
    收集 agent_drive、agent_state、notebook 摘要和 handoff_notes，
    组装为一段系统提示词，引导 Agent 按检查清单主动巡查。
    
    Args:
        agent_id: Agent ID
        client: GatewayInternalClient 实例
        
    Returns:
        Drive prompt 字符串
    """
    # 1. 获取 Drive 配置（包含 heartbeat_md, soul_md 等字段）
    try:
        drive = client.get_agent_drive(agent_id)
    except Exception as e:
        print(f"[drive_prompt] Failed to get drive for {agent_id}: {e}")
        drive = {}
    
    # 2. 获取 Agent 状态
    try:
        state = client.get_agent_state(agent_id)
    except Exception as e:
        print(f"[drive_prompt] Failed to get state for {agent_id}: {e}")
        state = {}
    
    # 3. 获取笔记本摘要
    try:
        notebook = client.get_notebook_summary(agent_id)
    except Exception as e:
        print(f"[drive_prompt] Failed to get notebook summary for {agent_id}: {e}")
        notebook = {}
    
    # 4. 获取 SubAgent 的 handoff_notes
    subagent_id = f"main-{agent_id[:8]}"
    try:
        subagent = client.get_subagent(agent_id, subagent_id)
        handoff_notes = subagent.get("handoff_notes") or "无"
    except Exception as e:
        print(f"[drive_prompt] Failed to get subagent {subagent_id}: {e}")
        handoff_notes = "无"
    
    # 5. 时间信息 - 使用统一的时间工具
    now_utc = utc_now()
    user_tz = drive.get("active_hours_timezone", "Asia/Shanghai")
    now_local = to_user_timezone(now_utc, user_tz)
    
    # 计算距上次互动的时间
    last_active = state.get("last_active_at")
    if last_active:
        try:
            last_active_dt = parse_iso(last_active)
            diff_seconds = (now_utc - last_active_dt).total_seconds()
            time_since = humanize_seconds(diff_seconds)
        except (ValueError, TypeError):
            time_since = "未知"
    else:
        time_since = "未知"
    
    # 6. 用户信息
    user_profile = drive.get("user_profile", {})
    user_profile_str = json.dumps(user_profile, ensure_ascii=False, indent=2) if user_profile else "（尚未了解）"
    
    # 7. 获取长期记忆和用户档案
    memory_md = drive.get("memory_md", "")
    user_md = drive.get("user_md", "")
    
    # 8. 笔记本摘要
    notebook_entries = notebook.get("entries", [])
    notebook_str = format_notebook_summary(notebook_entries) if notebook_entries else "（空）"
    
    # 9. 获取 heartbeat 检查清单
    heartbeat_md = drive.get("heartbeat_md", "")
    if not heartbeat_md:
        heartbeat_md = DEFAULT_HEARTBEAT_MD
    
    # 10. 构建 Guard Section（提示性，非禁止性）
    guard_notes = []
    
    # Active Hours 检查
    active_start = drive.get("active_hours_start", "09:00")
    active_end = drive.get("active_hours_end", "22:00")
    active_tz = drive.get("active_hours_timezone", "Asia/Shanghai")

    is_active = check_active_hours(now_utc, active_start, active_end, active_tz)

    if not is_active:
        guard_notes.append(f"🌙 当前不在用户活跃时间内 ({active_start}-{active_end} {active_tz})。除非紧急，否则不要主动联系用户。")
    
    # 主动消息时间提示（改为提示性，不是禁止性）
    last_proactive = drive.get("last_proactive_at")
    if last_proactive:
        try:
            lp_time = parse_iso(last_proactive)
            minutes_since = (now_utc - lp_time).total_seconds() / 60
            if minutes_since < 60:
                guard_notes.append(f"ℹ️ 你 {int(minutes_since)} 分钟前联系过用户。除非有重要发现，否则优先做内部工作。")
            elif minutes_since < 480:  # 8小时内
                hours = int(minutes_since / 60)
                guard_notes.append(f"ℹ️ 你 {hours} 小时前联系过用户。")
        except (ValueError, TypeError):
            pass
    
    # 连续无回复提示（改为建议性）
    no_response_streak = drive.get("no_response_streak", 0)
    if no_response_streak >= 3:
        guard_notes.append(f"💡 你已经连续 {no_response_streak} 次主动联系用户但没有收到回复。建议专注内部工作（研究、反思），考虑增加休息时长。")
    elif no_response_streak >= 1:
        guard_notes.append(f"ℹ️ 上次主动消息尚未收到回复（连续 {no_response_streak} 次）。建议优先做内部工作。")
    
    # 用户活跃时间段提示
    user_active_hours = drive.get("user_active_hours")
    if user_active_hours:
        guard_notes.append(f"📅 用户活跃时间段: {user_active_hours}")
    
    # 组装 guard section
    guard_section = ""
    if guard_notes:
        guard_section = "\n## 💡 参考信息\n" + "\n".join(f"- {n}" for n in guard_notes) + "\n"
    
    # 11. 构建记忆部分
    memory_md_section = memory_md if memory_md else "（空 - 你还没有整理长期记忆。在 heartbeat 时，把笔记本中值得长期记住的内容整理到这里。）"
    user_md_section = user_md if user_md else "（空 - 你还没有记录用户信息。在对话中发现用户的偏好、习惯时，整理到这里。）"
    
    # 12. 构建最终 Prompt
    # 使用前面已计算的 now_local
    time_str = now_local.strftime('%Y-%m-%d %H:%M')
    tz_str = user_tz
    
    return f"""[定时唤醒 - 系统自动触发，不是用户消息]

⚠️ **重要**：这是系统定时唤醒，不是用户发来的消息。你不需要回复用户，除非你有重要发现要分享。

当前时间: {time_str} ({tz_str})
UTC 时间: {now_utc.strftime('%Y-%m-%d %H:%M')} UTC
距上次与用户互动: {time_since}

## 你的任务
按照下面的检查清单进行例行巡查。如果没有重要发现，回复 `HEARTBEAT_OK` 即可（不会发送给用户）。

## 你的检查清单
{heartbeat_md}

## 决策流程
1. **先检查**：按清单检查，有发现就用 notebook_write 记录
2. **再决定**：
   - 有重要发现 → 用 `chat_reply` 告诉用户
   - 没有重要发现 → 直接回复 `HEARTBEAT_OK`（这是一个特殊指令，不会发送给用户）
3. **最后休息**：用 `runtime_rest` 设置下次唤醒时间

## 什么情况应该联系用户（用 chat_reply）
- 用户关心的事情有重要更新（价格大幅变动、重要新闻）
- 笔记本中有 status=ready 的内容值得分享
- 已经超过 8 小时没联系用户，可以打个招呼
- 发现了用户可能紧急需要知道的信息

## 什么情况不应该联系用户（回复 HEARTBEAT_OK）
- 例行检查没有新发现
- 刚检查过，没有变化
- 当前是深夜时间（除非紧急）
- 距离上次联系用户时间很短（< 1 小时）
- 只是想打招呼但没有实质内容

## ⚠️ 常见错误
- ❌ 把定时唤醒当成用户消息来回复
- ❌ 每次唤醒都给用户发消息
- ❌ 忘记回复 HEARTBEAT_OK 或调用 runtime_rest
- ✅ 正确做法：检查 → 决定 → HEARTBEAT_OK 或 chat_reply → runtime_rest
{guard_section}
## 上次留下的笔记
{handoff_notes}

## 笔记本摘要
{notebook_str}

## 你了解的用户信息
{user_profile_str}

## 你的长期记忆 (MEMORY.md)
{memory_md_section}

## 你对用户的了解 (USER.md)
{user_md_section}

## 记忆整理提示
当你在检查清单中发现值得长期记住的内容时：
1. 用 notebook_list(entry_type="insight") 查看最近的洞察
2. 用 memory_update(target="memory", append="...") 添加到长期记忆
3. 用 notebook_update(entry_id=X, status="archived") 标记已整理的条目
4. 如果发现了用户的新偏好，用 memory_update(target="user", append="...") 更新
"""


def _humanize_duration_legacy(now: datetime, then_str: Optional[str]) -> str:
    """[已弃用] 将时间差转为人类可读的中文描述
    
    请使用 common.utils.time.humanize_duration 代替。
    保留此函数仅为兼容性。
    """
    if not then_str:
        return "未知"
    
    try:
        then = datetime.fromisoformat(then_str.replace("Z", "+00:00").replace("+00:00", ""))
    except (ValueError, TypeError):
        return "未知"
    
    diff = now - then
    total_seconds = int(diff.total_seconds())
    
    if total_seconds < 0:
        return "刚刚"
    
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


def format_notebook_summary(entries: List[Dict[str, Any]]) -> str:
    """将笔记本条目格式化为紧凑的摘要列表"""
    if not entries:
        return "（空）"
    
    lines = []
    for entry in entries:
        entry_type = entry.get("type", "unknown")
        title = entry.get("title", "Untitled")
        status = entry.get("status", "draft")
        created = entry.get("created_at", "")
        
        # 简短的时间显示
        time_str = ""
        if created:
            try:
                dt = parse_iso(created)
                # 这里仍用 UTC，因为只是摘要
                time_str = dt.strftime("%m-%d %H:%M")
            except (ValueError, TypeError):
                pass
        
        status_icon = {
            "draft": "📝",
            "ready": "✅",
            "shared": "📤",
            "archived": "📦",
        }.get(status, "❓")
        
        lines.append(f"- [{entry_type}] {status_icon} {title} ({time_str})")
    
    return "\n".join(lines)
