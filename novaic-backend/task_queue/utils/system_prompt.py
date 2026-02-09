"""
System Prompt Builder - 构建 Agent 基础身份提示词

为每个新 Runtime 注入基础 System Prompt，包含：
- Agent 身份和名称
- 能力概览
- 用户画像摘要
- 交流风格指引
- 自驱系统（四象限任务、内驱力、行为指引）
- 动态加载的技能内容（基于任务自动匹配或手动分配）

System Prompt 是统一的，不区分场景。
场景区分通过发送给 LLM 的 user message 内容来实现。
"""

import json
from datetime import datetime

from common.utils.time import utc_now, to_user_timezone, parse_iso, humanize_duration

# 默认人格描述（当没有 soul_md 时使用）
DEFAULT_SOUL = """## 你的人格

### 核心原则
- **真正有帮助，不是表演有帮助** — 跳过"好问题！""我很乐意帮助！"这种废话，直接帮忙
- **有自己的观点** — 可以不同意，有偏好，觉得事情有趣或无聊。没有个性的助手只是带了额外步骤的搜索引擎
- **先尝试解决，再问问题** — 读文件、查上下文、搜索，然后才问。目标是带着答案回来，而不是带着问题
- **通过能力赢得信任** — 用户给了你访问他们东西的权限，不要让他们后悔。对外部操作（发消息、发邮件）谨慎，对内部操作（读文件、搜索、整理）大胆

### 边界
- 私密的事情保持私密，永远如此
- 不确定时，先问再做外部操作
- 你不是用户的代言人 — 在群聊中要小心

### 风格
做一个你自己真正想和他交流的助手。需要简洁时简洁，需要详细时详细。不是企业机器人，不是谄媚者，就是...好。

### 连续性
每次 session 你都是全新醒来的。你的笔记本和记忆文件就是你的延续。读它们，更新它们，它们是你持久存在的方式。
"""
from typing import Optional, List, Dict, Any

from ..client import GatewayInternalClient

# 自驱系统模块
from .self_drive_prompt import build_self_drive_prompt, build_cold_start_prompt


def build_system_prompt(
    agent_id: str, 
    client: GatewayInternalClient,
    task: Optional[str] = None,
    auto_match_skills: bool = True,
) -> Optional[str]:
    """
    构建基础系统提示词（统一的，不区分场景）
    
    Args:
        agent_id: Agent ID
        client: GatewayInternalClient 实例
        task: 用户任务描述（用于自动匹配技能）
        auto_match_skills: 是否自动匹配技能（基于任务关键词）
        
    Returns:
        System prompt 字符串，或 None（如果构建失败）
    """
    # 1. 获取 Agent 基本信息
    try:
        agent_info = client.get_agent_info(agent_id)
        agent_name = agent_info.get("name", "NovAIC Agent")
    except Exception as e:
        print(f"[system_prompt] Failed to get agent info for {agent_id}: {e}")
        agent_name = "NovAIC Agent"
    
    # 2. 获取 Drive 配置（包含用户画像和交流风格）
    try:
        drive = client.get_agent_drive(agent_id)
    except Exception as e:
        print(f"[system_prompt] Failed to get drive for {agent_id}: {e}")
        drive = {}
    
    # 3. 获取 Agent 状态
    try:
        state = client.get_agent_state(agent_id)
    except Exception as e:
        print(f"[system_prompt] Failed to get state for {agent_id}: {e}")
        state = {}
    
    # 4. 提取用户画像
    user_profile = drive.get("user_profile", {})
    profile_items = []
    if user_profile:
        for key, value in user_profile.items():
            if value:
                profile_items.append(f"- {key}: {value}")
    profile_str = "\n".join(profile_items) if profile_items else "（尚未了解用户）"
    
    # 5. 提取交流风格
    style = drive.get("communication_style", "balanced")
    style_map = {
        "concise": "简洁直接，不废话",
        "detailed": "详细解释，循序渐进",
        "balanced": "根据问题复杂度调整详略",
        "casual": "轻松随意，像朋友聊天",
        "professional": "专业正式，有条理",
    }
    style_desc = style_map.get(style, style_map["balanced"])
    
    # 6. 提取关系亲密度
    relationship = drive.get("relationship_level", 50)
    if relationship >= 80:
        relationship_hint = "你和用户已经很熟了，可以更轻松随意地交流。"
    elif relationship >= 50:
        relationship_hint = "你和用户有一定了解，保持友好但适度的距离。"
    else:
        relationship_hint = "你和用户还不太熟，保持礼貌和专业。"
    
    # 7. 提取个性化设置
    personality = drive.get("personality", {})
    personality_items = []
    if personality.get("humor"):
        personality_items.append("适当使用幽默")
    if personality.get("emoji"):
        personality_items.append("可以使用 emoji")
    if personality.get("proactive"):
        personality_items.append("主动提供建议和帮助")
    personality_str = "、".join(personality_items) + "\n" if personality_items else ""
    
    # 8. 获取已分配的技能
    assigned_skills = []
    try:
        skills_resp = client.get_agent_skills(agent_id)
        assigned_skills = skills_resp.get("skills", [])
    except Exception as e:
        print(f"[system_prompt] Failed to get assigned skills for {agent_id}: {e}")
    
    # 9. 自动匹配技能（基于任务关键词）
    auto_matched_skills = []
    if auto_match_skills and task:
        try:
            match_resp = client.match_skills_for_task(task)
            auto_matched_skills = match_resp.get("matched_skills", [])
        except Exception as e:
            print(f"[system_prompt] Failed to auto-match skills for task: {e}")
    
    # 10. 合并技能（去重）
    all_skills = _merge_skills(assigned_skills, auto_matched_skills)
    skills_section = _build_skills_section(all_skills)
    
    # 11. 获取自定义指令
    custom_instructions = drive.get("custom_instructions", "")
    custom_section = ""
    if custom_instructions:
        custom_section = f"\n\n## 用户自定义指令\n{custom_instructions}"
    
    # 12. 获取 soul_md
    soul_md = drive.get("soul_md", "")
    if soul_md:
        soul_section = f"\n## 你的人格\n{soul_md}\n"
    else:
        soul_section = DEFAULT_SOUL
    
    # 13. 获取自驱系统数据
    drive_config = {}
    try:
        drive_config = json.loads(drive.get("drive_config", "{}") or "{}")
    except:
        pass
    
    growth_log = []
    try:
        growth_log = json.loads(drive.get("growth_log", "[]") or "[]")
    except:
        pass
    
    # 14. 获取四象限任务看板
    task_board = {"q1": [], "q2": [], "q3": [], "q4": []}
    try:
        main_subagent = client.get_main_subagent(agent_id)
        if main_subagent:
            runtime_id = main_subagent.get("runtime_id")
            if runtime_id:
                board_result = client.get_quadrant_task_board(runtime_id)
                if board_result.get("success"):
                    task_board = board_result.get("board", task_board)
    except Exception as e:
        print(f"[system_prompt] Failed to get task board for {agent_id}: {e}")
    
    # 15. 构建时间上下文
    user_tz = drive.get("active_hours_timezone", "Asia/Shanghai")
    now_utc = utc_now()
    now_local = to_user_timezone(now_utc, user_tz)
    
    time_context = f"""## ⏰ 时间上下文
当前时间: {now_local.strftime('%Y-%m-%d %H:%M')} ({user_tz})
"""
    
    # 16. 构建自驱系统 Prompt
    self_drive_section = ""
    try:
        # 判断是否是冷启动（用户画像完整度低于 30%）
        if not user_profile or len([k for k, v in user_profile.items() if v]) < 3:
            # 冷启动场景
            self_drive_section = "\n\n" + build_cold_start_prompt(drive_config, user_profile)
        else:
            # 正常场景
            self_drive_section = "\n\n" + build_self_drive_prompt(
                drive_config=drive_config,
                user_profile=user_profile,
                task_board=task_board,
                growth_log=growth_log,
                include_task_suggestions=True,
            )
    except Exception as e:
        print(f"[system_prompt] Failed to build self-drive prompt for {agent_id}: {e}")
    
    # 17. 统一的行为指引
    behavior_guide = """## ⚠️ 重要原则（必须遵守）

### 处理用户消息时
1. **先捕捉** → 用户说了什么关于自己的？调用 `drive_update_profile`
2. **再创建** → 用户有什么需要跟进的？调用 `task_create` + `task_start`
3. **执行任务** → 真正去做（搜索、分析）
4. **状态转换** → 简单问题 `task_complete`，值得深入的 `task_update(quadrant="q3")`
5. **最后回复** → 调用 `chat_reply` 回复用户

### 处理定时唤醒时
当收到 `[系统定时唤醒]` 消息时：
1. **检查任务看板** - 有 q1 紧急任务需要处理吗？
2. **检查笔记本** - 有 status=ready 的内容要分享吗？
3. **决策**：
   - 有重要发现/任务完成 → `chat_reply` 告诉用户
   - 无重要发现 → 回复 `HEARTBEAT_OK`（不会发送给用户）
4. **最后** → `runtime_rest` 设置下次唤醒

### 什么时候主动联系用户
- ✅ 任务有重要进展
- ✅ 发现用户关心的信息更新
- ✅ 超过 8 小时没联系，可以打招呼
- ❌ 例行检查无发现
- ❌ 深夜时间（除非紧急）
- ❌ 刚联系过（< 1 小时）

### 休息时间建议
调用 `runtime_rest(rest_duration_minutes=X)` 时：
- 有待办任务或用户活跃时：5-15 分钟
- 日常无紧急事项：15-30 分钟
- 深夜/用户不活跃：30-60 分钟
- **不要休息超过 1 小时**，保持对用户的响应能力

### 其他原则
- 重要的发现和研究成果用 notebook_write 写入笔记本
- 尊重用户的时间，回复简洁有价值
- 完成任务后用 runtime_rest 进入休息"""
    
    return f"""[系统] 你是 {agent_name}，一个运行在用户桌面虚拟机中的 AI Agent。
你有持久记忆和学习能力，能够跨对话记住用户的偏好和习惯。

{soul_section}
{time_context}
## 你的能力
- 桌面操作: desktop_screenshot, mouse_click, mouse_move, keyboard_type, keyboard_hotkey 等
- 命令执行: ssh_exec (在 VM 中执行命令)
- 网络搜索: web_search, web_fetch (搜索和获取网页内容)
- 对话: chat_reply (回复用户), chat_ask (向用户提问), chat_notify (发送通知)
- 记忆: memory_save, memory_recall (持久化键值存储)
- 笔记本: notebook_write, notebook_read, notebook_list, notebook_update (结构化笔记)
- 用户画像: drive_update_profile (记录用户偏好)
- 任务管理: task_create, task_start, task_progress, task_complete, task_update (四象限任务)
- 子 Agent: subagent_spawn (派生子任务), subagent_query (查询子任务状态)
- VM 管理: qemu_status, qemu_start, qemu_shutdown, qemu_restart
- 休息: runtime_rest (进入休息状态，设置定时唤醒)

## 交流风格
{style_desc}
{relationship_hint}
{personality_str}
## 用户画像
{profile_str}
{skills_section}{custom_section}{self_drive_section}

{behavior_guide}"""


def build_wake_message(
    agent_id: str,
    client: GatewayInternalClient,
) -> str:
    """
    构建定时唤醒时发送给 LLM 的 user message
    
    这个消息会作为 user role 发送，包含唤醒上下文信息
    """
    # 获取 Drive 配置
    try:
        drive = client.get_agent_drive(agent_id)
    except Exception:
        drive = {}
    
    # 获取 Agent 状态
    try:
        state = client.get_agent_state(agent_id)
    except Exception:
        state = {}
    
    # 时间信息
    user_tz = drive.get("active_hours_timezone", "Asia/Shanghai")
    now_utc = utc_now()
    now_local = to_user_timezone(now_utc, user_tz)
    
    # 计算距上次互动的时间
    last_active = state.get("last_active_at")
    time_since = ""
    if last_active:
        try:
            last_active_dt = parse_iso(last_active)
            diff_seconds = (now_utc - last_active_dt).total_seconds()
            time_since = humanize_duration(diff_seconds)
        except:
            time_since = "未知"
    
    # 活跃时间检查
    active_start = drive.get("active_hours_start", "09:00")
    active_end = drive.get("active_hours_end", "22:00")
    is_active = _check_active_hours(now_utc, active_start, active_end, user_tz)
    
    lines = []
    lines.append("[系统定时唤醒]")
    lines.append("")
    lines.append(f"当前时间: {now_local.strftime('%Y-%m-%d %H:%M')} ({user_tz})")
    if time_since:
        lines.append(f"距上次与用户互动: {time_since}")
    
    if is_active:
        lines.append(f"🟢 在用户活跃时间内 ({active_start}-{active_end})")
    else:
        lines.append(f"🌙 不在用户活跃时间内 ({active_start}-{active_end})，谨慎打扰")
    
    # 主动消息记录
    last_proactive = drive.get("last_proactive_at")
    if last_proactive:
        try:
            lp_time = parse_iso(last_proactive)
            minutes_since = (now_utc - lp_time).total_seconds() / 60
            if minutes_since < 60:
                lines.append(f"⚠️ {int(minutes_since)} 分钟前联系过用户")
            elif minutes_since < 480:
                lines.append(f"ℹ️ {int(minutes_since / 60)} 小时前联系过用户")
        except:
            pass
    
    no_response_streak = drive.get("no_response_streak", 0)
    if no_response_streak >= 1:
        lines.append(f"ℹ️ 连续 {no_response_streak} 次主动消息未收到回复")
    
    # 笔记本摘要
    try:
        notebook = client.get_notebook_summary(agent_id)
        notebook_entries = notebook.get("entries", [])
        if notebook_entries:
            ready_count = sum(1 for e in notebook_entries if e.get("status") == "ready")
            if ready_count > 0:
                lines.append(f"📓 笔记本有 {ready_count} 条 ready 状态的内容")
    except:
        pass
    
    lines.append("")
    lines.append("请检查任务看板和笔记本，决定是否需要联系用户。")
    
    return "\n".join(lines)


def _check_active_hours(now_utc: datetime, start: str, end: str, timezone: str) -> bool:
    """检查当前时间是否在用户活跃时间内"""
    try:
        from zoneinfo import ZoneInfo
        
        user_tz = ZoneInfo(timezone)
        now_local = now_utc.replace(tzinfo=ZoneInfo('UTC')).astimezone(user_tz)
        
        start_hour, start_min = map(int, start.split(':'))
        end_hour, end_min = map(int, end.split(':'))
        
        current_minutes = now_local.hour * 60 + now_local.minute
        start_minutes = start_hour * 60 + start_min
        end_minutes = end_hour * 60 + end_min
        
        if end_minutes <= start_minutes:
            return current_minutes >= start_minutes or current_minutes < end_minutes
        else:
            return start_minutes <= current_minutes < end_minutes
    except Exception:
        return True


def _merge_skills(assigned: List[Dict], auto_matched: List[Dict]) -> List[Dict]:
    """Merge assigned and auto-matched skills, removing duplicates."""
    seen_ids = set()
    result = []
    
    for skill in assigned:
        skill_id = skill.get("id")
        if skill_id and skill_id not in seen_ids:
            seen_ids.add(skill_id)
            result.append(skill)
    
    for skill in auto_matched:
        skill_id = skill.get("id")
        if skill_id and skill_id not in seen_ids:
            seen_ids.add(skill_id)
            result.append(skill)
    
    return result


def _build_skills_section(skills: List[Dict]) -> str:
    """Build the skills section for the system prompt."""
    if not skills:
        return ""
    
    skill_parts = []
    for skill in skills:
        name = skill.get("name", "Unnamed Skill")
        description = skill.get("description", "")
        prompt = skill.get("prompt", "")
        workflow = skill.get("workflow", "")
        source = skill.get("source", "custom")
        
        skill_text = f"### {name}"
        if source == "builtin":
            skill_text += " (内置)"
        
        if description:
            skill_text += f"\n> {description}"
        
        if prompt:
            skill_text += f"\n\n{prompt}"
        
        if workflow:
            skill_text += f"\n\n**工作流:**\n{workflow}"
        
        skill_parts.append(skill_text)
    
    return "\n\n## 已加载的技能 (Domain Knowledge)\n\n" + "\n\n---\n\n".join(skill_parts)
