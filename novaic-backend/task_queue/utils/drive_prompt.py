"""
Drive Prompt Builder - 构建定时唤醒的 Agent 自驱力 Prompt

当 Agent 被 SchedulerWorker 定时唤醒（trigger_type=scheduled_wake）时，
此模块构建一段系统 Prompt，注入 Agent 的驱动力、用户画像、笔记本摘要等信息，
引导 Agent 自主决策要做什么。
"""

import json
from datetime import datetime
from typing import List, Dict, Any, Optional

from ..client import GatewayInternalClient


def build_drive_prompt(agent_id: str, client: GatewayInternalClient) -> str:
    """
    构建定时唤醒的 Drive Prompt
    
    收集 agent_drive、agent_state、notebook 摘要和 handoff_notes，
    组装为一段系统提示词。
    
    Args:
        agent_id: Agent ID
        client: GatewayInternalClient 实例
        
    Returns:
        Drive prompt 字符串
    """
    # 1. 获取 Drive 配置
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
    
    # 5. 组装 Prompt
    now = datetime.utcnow()
    last_active = state.get("last_active_at")
    time_since = humanize_duration(now, last_active) if last_active else "未知"
    
    user_profile = drive.get("user_profile", {})
    user_profile_str = json.dumps(user_profile, ensure_ascii=False, indent=2) if user_profile else "（尚未了解）"
    
    notebook_entries = notebook.get("entries", [])
    notebook_str = format_notebook_summary(notebook_entries) if notebook_entries else "（空）"
    
    relationship_level = drive.get("relationship_level", 0)
    proactiveness = drive.get("proactiveness", 0.5)
    last_proactive = drive.get("last_proactive_at")
    last_proactive_str = ""
    if last_proactive:
        last_proactive_str = f"\n上次主动联系用户: {humanize_duration(now, last_proactive)}前"
    
    # Guard Rails — 动态行为约束
    guard_notes = []
    
    # 1. 主动消息冷却（30 分钟内发过就不再发）
    if last_proactive:
        try:
            lp_time = datetime.fromisoformat(last_proactive.replace("Z", "+00:00").replace("+00:00", ""))
            minutes_since = (now - lp_time).total_seconds() / 60
            if minutes_since < 30:
                guard_notes.append(f"⚠️ 你 {int(minutes_since)} 分钟前刚发过主动消息，现在不要再发。做内向型活动或继续休息。")
        except (ValueError, TypeError):
            pass
    
    # 2. 连续无回复抑制
    no_response_streak = drive.get("no_response_streak", 0)
    if no_response_streak >= 3:
        guard_notes.append(f"⚠️ 你已经连续 {no_response_streak} 次主动联系用户但没有收到回复。停止外向型活动，专注内向型活动（研究、反思）。考虑增加休息时长。")
    elif no_response_streak >= 1:
        guard_notes.append(f"ℹ️ 上次主动消息尚未收到回复（连续 {no_response_streak} 次）。优先做内向型活动。")
    
    # 3. 用户活跃时间段提示
    user_active_hours = drive.get("user_active_hours")
    if user_active_hours:
        guard_notes.append(f"用户活跃时间段: {user_active_hours}")
    
    # 组装 guard section
    guard_section = ""
    if guard_notes:
        guard_section = "\n## ⚡ 行为约束\n" + "\n".join(f"- {n}" for n in guard_notes) + "\n"
    
    return f"""[自动唤醒 - 定时任务]
你刚从休息中醒来。当前时间: {now.strftime('%Y-%m-%d %H:%M UTC')}。
距上次与用户互动已过: {time_since}。
亲密度: {relationship_level}/100 | 主动性: {proactiveness:.1f}{last_proactive_str}

## 上次留下的笔记
{handoff_notes}

## 你的笔记本摘要
{notebook_str}

## 你了解的用户信息
{user_profile_str}
{guard_section}
## 你的行为选择
你被定时唤醒，没有来自用户的新消息。根据情况选择活动：

### 内向型（不打扰用户）
- **信息采集**: 用 web_search 查查用户关心的话题，用 notebook_write 记录
- **反思复盘**: 回顾过去对话，用 notebook_write(type=reflection/insight) 记录
- **环境观察**: 用 desktop_screenshot 看看用户桌面变化，用 notebook_write(type=observation) 记录
- **知识准备**: 整理笔记本中 draft 状态的内容，notebook_update(status=ready)

### 外向型（与用户互动）
- **分享发现**: 笔记本中有 status=ready 的有价值内容，用 chat_reply 自然地分享
- **主动关心**: 距上次互动较久且有合适话题时，用 chat_reply 打招呼

### 继续休息
- 直接调用 runtime_rest(rest_duration_minutes=N) 设置合适时长
- 刚做完采集 → 短休息 (10-15min)
- 发了消息没回复 → 长休息 (60-120min)
- 深夜/无事 → 很长休息

## 决策原则
- 大部分时候做内向型活动，积累再输出
- 外向型活动要有真正价值才做
- 用 drive_update_profile 记住学到的用户偏好
- 用 drive_update_relationship 根据互动质量调整亲密度和主动性
- 根据用户反应调整休息时长
"""


def humanize_duration(now: datetime, then_str: Optional[str]) -> str:
    """将时间差转为人类可读的中文描述"""
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
                dt = datetime.fromisoformat(created.replace("Z", ""))
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
