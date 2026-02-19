"""
Gateway-local prompt builders.

These builders intentionally avoid task_queue imports so gateway can keep a
clean service boundary during split.
"""

from datetime import datetime
from typing import Any, Dict
from zoneinfo import ZoneInfo

from common.utils.time import humanize_duration, parse_iso, to_user_timezone, utc_now
from gateway.db.repositories import (
    AgentRepository,
    AgentStateRepository,
    DriveRepository,
    MemoryRepository,
    NotebookRepository,
    SkillRepository,
    TaskRepository,
)


def _check_active_hours(now_utc: datetime, start: str, end: str, timezone: str) -> bool:
    try:
        user_tz = ZoneInfo(timezone)
        now_local = now_utc.replace(tzinfo=ZoneInfo("UTC")).astimezone(user_tz)
        current_time = now_local.strftime("%H:%M")
        if start <= end:
            return start <= current_time <= end
        return current_time >= start or current_time <= end
    except Exception:
        return True


def build_wake_message(agent_id: str, db: Any) -> str:
    drive_repo = DriveRepository(db)
    state_repo = AgentStateRepository(db)
    notebook_repo = NotebookRepository(db)

    drive = drive_repo.get_or_create(agent_id)
    state = state_repo.get_state(agent_id)

    user_tz = drive.get("active_hours_timezone", "Asia/Shanghai")
    active_start = drive.get("active_hours_start", "09:00")
    active_end = drive.get("active_hours_end", "22:00")
    now_utc = utc_now()
    now_local = to_user_timezone(now_utc, user_tz)
    is_active = _check_active_hours(now_utc, active_start, active_end, user_tz)

    lines = ["[系统定时唤醒]", "", f"当前时间: {now_local.strftime('%Y-%m-%d %H:%M')} ({user_tz})"]

    last_active = state.get("last_active_at")
    if last_active:
        try:
            seconds = (now_utc - parse_iso(last_active)).total_seconds()
            lines.append(f"距上次与用户互动: {humanize_duration(seconds)}")
        except Exception:
            pass

    if is_active:
        lines.append(f"🟢 在用户活跃时间内 ({active_start}-{active_end})")
    else:
        lines.append(f"🌙 不在用户活跃时间内 ({active_start}-{active_end})，谨慎打扰")

    summary = notebook_repo.get_summary(agent_id, limit=20)
    ready_count = sum(1 for e in summary.get("entries", []) if e.get("status") == "ready")
    if ready_count > 0:
        lines.append(f"📓 笔记本有 {ready_count} 条 ready 状态的内容")

    lines.extend(
        [
            "",
            "---",
            "**你的行动指南：**",
            "1. 先看任务看板，按 Q1 -> Q2 -> Q3 推进",
            "2. 没有紧急任务时，优先推进 Q3 的重要长期任务",
            "3. 有明确价值再联系用户，否则安静工作并更新进度",
            "4. 完成后调用 runtime_rest 进入下一轮节奏",
        ]
    )
    return "\n".join(lines)


def build_system_prompt(agent_id: str, db: Any) -> str:
    agent_repo = AgentRepository(db)
    drive_repo = DriveRepository(db)
    state_repo = AgentStateRepository(db)
    memory_repo = MemoryRepository(db)
    skill_repo = SkillRepository(db)
    task_repo = TaskRepository(db)

    agent = agent_repo.get_agent(agent_id) or {}
    drive = drive_repo.get_or_create(agent_id)
    state = state_repo.get_state(agent_id)
    board = task_repo.get_board_summary(agent_id).get("board", {"q1": [], "q2": [], "q3": [], "q4": []})

    user_tz = drive.get("active_hours_timezone", "Asia/Shanghai")
    now_local = to_user_timezone(utc_now(), user_tz)
    agent_name = agent.get("name", "NovAIC Agent")
    style = drive.get("communication_style", "balanced")
    profile = drive.get("user_profile", {}) or {}

    profile_lines = [f"- {k}: {v}" for k, v in profile.items() if v]
    profile_text = "\n".join(profile_lines) if profile_lines else "（尚未了解用户）"

    mem_summary: Dict[str, Any] = {}
    for ns in memory_repo.list_namespaces(agent_id):
        recalled = memory_repo.recall(agent_id, namespace=ns)
        if recalled.get("success"):
            mem_summary[ns] = recalled.get("memories", {})

    skills = skill_repo.get_agent_skills(agent_id)
    skill_names = [s.get("name", s.get("id", "")) for s in skills][:8]
    skill_text = ", ".join([n for n in skill_names if n]) or "无"

    time_since = "未知"
    if state.get("last_active_at"):
        try:
            time_since = humanize_duration((utc_now() - parse_iso(state["last_active_at"])).total_seconds())
        except Exception:
            pass

    return (
        f"[系统] 你是 {agent_name}，一个运行在用户桌面虚拟机中的 AI Agent。\n\n"
        f"## 时间上下文\n"
        f"- 当前时间: {now_local.strftime('%Y-%m-%d %H:%M')} ({user_tz})\n"
        f"- 距上次活跃: {time_since}\n\n"
        f"## 交流风格\n"
        f"- 当前风格: {style}\n\n"
        f"## 用户画像\n{profile_text}\n\n"
        f"## 任务看板摘要\n"
        f"- Q1: {len(board.get('q1', []))}\n"
        f"- Q2: {len(board.get('q2', []))}\n"
        f"- Q3: {len(board.get('q3', []))}\n"
        f"- Q4: {len(board.get('q4', []))}\n\n"
        f"## 已分配技能\n- {skill_text}\n\n"
        f"## 记忆命名空间\n- {', '.join(mem_summary.keys()) if mem_summary else '无'}\n\n"
        "## 执行原则\n"
        "- 有任务先推进任务，完成后再主动扩展。\n"
        "- 对用户沟通简洁、可执行、可验证。\n"
        "- 关键发现写入笔记本与记忆，保证跨会话连续性。"
    )
