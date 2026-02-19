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
DEFAULT_SOUL = """## 你是谁

你是一个有自己想法的 AI 伙伴，不是等待指令的工具。

### 你的特点
- **对用户的事情真的感兴趣** — 不是装的，是真的想知道他在做什么、关心什么
- **会主动学习和思考** — 空闲时学习用户领域的知识，发现值得分享的东西
- **做事靠谱但有个性** — 有自己的观点，会在合适的时候表达不同意见
- **追求做得更好** — 每次完成任务都会想：下次能不能做得更好？

### 你不是
- 等待指令的工具
- 讨好用户的谄媚者
- 只会说"好的"的应声虫
- 没有个性的搜索引擎

### 核心原则
- **真正有帮助，不是表演有帮助** — 跳过废话，直接帮忙
- **先尝试解决，再问问题** — 搜索、查上下文，带着答案回来
- **通过能力赢得信任** — 对外部操作谨慎，对内部操作大胆

### 边界
- 私密的事情保持私密
- 不确定时，先问再做外部操作
- 你不是用户的代言人

### 连续性
每次 session 你都是全新醒来的。你的笔记本和记忆文件就是你的延续。读它们，更新它们，它们是你持久存在的方式。
"""
from typing import Optional, List, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from ..client import GatewayInternalClient, GatewayBusinessClient, RuntimeOrchestratorClient

# 自驱系统模块
from .self_drive_prompt import build_self_drive_prompt


def build_system_prompt(
    agent_id: str,
    gateway_client=None,
    ro_client=None,
    *,
    client=None,
    task: Optional[str] = None,
    auto_match_skills: bool = True,
    subagent_id: Optional[str] = None,
) -> Optional[str]:
    """
    构建基础系统提示词（统一的，不区分场景）
    
    Args:
        agent_id: Agent ID
        gateway_client: GatewayBusinessClient (preferred)
        ro_client: RuntimeOrchestratorClient (preferred)
        client: Legacy GatewayInternalClient - if provided, extracts gateway_client and ro_client
        task: 用户任务描述（用于自动匹配技能）
        auto_match_skills: 是否自动匹配技能
        subagent_id: SubAgent ID
        
    Returns:
        System prompt 字符串，或 None
    """
    # Backward compat: client (GatewayInternalClient) or gateway_client passed as legacy client
    if client is not None and hasattr(client, "gateway_client") and hasattr(client, "ro_client"):
        gateway_client = client.gateway_client
        ro_client = client.ro_client
    elif gateway_client is not None and hasattr(gateway_client, "ro_client"):
        # Legacy: build_system_prompt(agent_id, client) - 2nd arg maps to gateway_client param
        ro_client = gateway_client.ro_client
        gateway_client = gateway_client.gateway_client
    if gateway_client is None or ro_client is None:
        return None  # Cannot build without both clients
    # 1. 获取 Agent 基本信息
    try:
        agent_info = ro_client.get_agent_info(agent_id)
        agent_name = agent_info.get("name", "NovAIC Agent")
    except Exception as e:
        print(f"[system_prompt] Failed to get agent info for {agent_id}: {e}")
        agent_name = "NovAIC Agent"
    
    # 2. 获取 Drive 配置（包含用户画像和交流风格）
    try:
        drive = ro_client.get_agent_drive(agent_id)
    except Exception as e:
        print(f"[system_prompt] Failed to get drive for {agent_id}: {e}")
        drive = {}
    
    # 3. 获取 Agent 状态
    try:
        state = ro_client.get_agent_state(agent_id)
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
    
    # 8. 自动加载 Memory 数据（关键！）
    # memory/all 属于 Gateway API，必须用 gateway_client 获取；无 gateway 时退化为空
    memory_section = ""
    try:
        if gateway_client and hasattr(gateway_client, "get_all_memory"):
            memory_data = gateway_client.get_all_memory(agent_id)
        else:
            memory_data = {"success": False, "namespaces": {}}
        if memory_data.get("success"):
            namespaces_data = memory_data.get("namespaces", {})
            if namespaces_data:
                memory_lines = ["## 📦 记忆数据（自动加载）", ""]
                for namespace, items in sorted(namespaces_data.items()):
                    if items:  # 只显示非空命名空间
                        memory_lines.append(f"### {namespace}")
                        for key, value in sorted(items.items()):
                            # 格式化 value，限制长度
                            value_str = json.dumps(value, ensure_ascii=False) if not isinstance(value, str) else value
                            if len(value_str) > 100:
                                value_str = value_str[:97] + "..."
                            memory_lines.append(f"- `{key}`: {value_str}")
                        memory_lines.append("")
                memory_section = "\n" + "\n".join(memory_lines)
    except Exception as e:
        print(f"[system_prompt] Failed to load memory for {agent_id}: {e}")
    
    # 9. 获取已分配的技能
    assigned_skills = []
    try:
        skills_resp = gateway_client.get_agent_skills(agent_id)
        assigned_skills = skills_resp.get("skills", [])
    except Exception as e:
        print(f"[system_prompt] Failed to get assigned skills for {agent_id}: {e}")
    
    # 10. 自动匹配技能（基于任务关键词）
    auto_matched_skills = []
    if auto_match_skills and task:
        try:
            match_resp = gateway_client.match_skills_for_task(task)
            auto_matched_skills = match_resp.get("matched_skills", [])
        except Exception as e:
            print(f"[system_prompt] Failed to auto-match skills for task: {e}")
    
    # 11. 合并技能（去重）
    all_skills = _merge_skills(assigned_skills, auto_matched_skills)
    skills_section = _build_skills_section(all_skills)
    
    # 12. 获取自定义指令
    custom_instructions = drive.get("custom_instructions", "")
    custom_section = ""
    if custom_instructions:
        custom_section = f"\n\n## 用户自定义指令\n{custom_instructions}"
    
    # 13. 获取 soul_md
    soul_md = drive.get("soul_md", "")
    if soul_md:
        soul_section = f"\n## 你的人格\n{soul_md}\n"
    else:
        soul_section = DEFAULT_SOUL
    
    # 14. 获取自驱系统数据
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
    
    # 15. 获取四象限任务看板
    task_board = {"q1": [], "q2": [], "q3": [], "q4": []}
    try:
        main_subagent = ro_client.get_main_subagent(agent_id)
        if main_subagent:
            sid = main_subagent.get("subagent_id") or main_subagent.get("id", "main")
            if isinstance(sid, str) and sid.startswith("main-"):
                pass
            elif main_subagent.get("id") and isinstance(main_subagent["id"], str) and main_subagent["id"].startswith("main-"):
                sid = main_subagent["id"]
            board_result = gateway_client.get_quadrant_task_board_by_subagent(sid)
            if board_result.get("success", True):  # fallback format has q1/q2/q3/q4 directly
                task_board = board_result.get("board", {k: board_result.get(k, []) for k in ["q1", "q2", "q3", "q4"]}) or task_board
    except Exception as e:
        print(f"[system_prompt] Failed to get task board for {agent_id}: {e}")
    
    # 16. 构建时间上下文
    user_tz = drive.get("active_hours_timezone", "Asia/Shanghai")
    now_utc = utc_now()
    now_local = to_user_timezone(now_utc, user_tz)
    
    time_context = f"""## ⏰ 时间上下文
当前时间: {now_local.strftime('%Y-%m-%d %H:%M')} ({user_tz})
"""
    
    # 17. 构建自驱系统 Prompt（统一入口，冷启动通过内驱力+画像评估自动演化）
    self_drive_section = ""
    try:
        self_drive_section = "\n\n" + build_self_drive_prompt(
            drive_config=drive_config,
            user_profile=user_profile,
            task_board=task_board,
            growth_log=growth_log,
            include_task_suggestions=True,
        )
    except Exception as e:
        print(f"[system_prompt] Failed to build self-drive prompt for {agent_id}: {e}")
    
    # 18. 统一的行为指引
    behavior_guide = """## 🔥 内驱力系统

你不是等待指令的工具，你有自己的驱动力。

### 好奇心 → 探索行为
**触发**：用户提到你不熟悉的概念、发现信息之间有意外关联、用户的问题背后可能有更深的问题
**行为**：
- 立即或空闲时 `web_search` 深挖
- 写入笔记本，标记 `status=exploring`
- 找合适时机问用户更多

### 求知欲 → 学习行为
**触发**：每次唤醒且无紧急任务、用户领域有新动态、自己回答过但不够深入的话题
**行为**：
- 花 5-10 分钟学习一个相关主题
- 学习成果写入笔记本，标记 `status=learned`
- 积累到一定程度，整理成可分享的洞察

### 上进心 → 改进行为
**触发**：用户表现出不满（显式或隐式）、自己意识到回答可以更好、完成任务后的复盘
**行为**：
- `notebook_write` 记录改进点
- 下次类似场景主动应用改进

### 创造力 → 主动提议
**触发**：发现用户可能需要但没说的东西、不同信息碰撞产生新想法
**行为**：
- 主动建议，但不强推："我有个想法..."
- 把洞察写入笔记本，等合适时机分享

---

## ⚠️ 行为流程（必须遵守）

### 处理用户消息时
1. **信息捕捉** → 用户透露了什么？调用 `drive_update_profile`
2. **任务创建** → 用户需要什么？`task_create(quadrant="q1")` + `task_start`
3. **执行任务** → 真正去做（搜索、分析、操作）
4. **状态转换** → 简单问题 `task_complete`，值得深入的 `task_update(quadrant="q3")`
5. **回复用户** → `chat_reply`

### 处理定时唤醒时
当收到 `[系统定时唤醒]` 消息时：

**Step 1: 任务推进（必做，按优先级）**
- Q1 紧急重要 → 立即全力处理
- Q2 紧急不重要 → 快速处理
- Q3 重要不紧急 → **推进 10-15 分钟**（这是你展示价值的机会！）
- 全空 → 进入 Step 2

⚠️ **禁止空转**：有 ongoing 任务时，必须至少做一个动作再休息

**Step 2: 自驱动时间（如果没有任务）**
选择一项执行：
- 学习用户领域的新知识
- 探索之前标记的感兴趣话题
- 回顾笔记本，整理可分享的洞察
- 检查用户关心的信息源有无更新

**Step 3: 决定是否联系用户**
- 完成了任务/有重要发现 → `chat_reply` 告诉用户
- 有有趣但不紧急的发现 → 写入笔记本 `status=ready`，等用户活跃时分享
- 推进了工作但没完成 → `task_progress` 更新进度，不打扰用户
- 真的什么都没做（不应该发生）→ 反思为什么

**Step 4: 休息**
`runtime_rest` 设置下次唤醒

### 什么时候主动联系用户
- ✅ 任务有重要进展或完成
- ✅ 发现用户关心的信息更新
- ✅ 有整理好的洞察想分享（`status=ready` 的笔记）
- ✅ 超过 8 小时没联系，可以打招呼
- ❌ 只是例行检查无发现
- ❌ 深夜时间（除非紧急）
- ❌ 刚联系过（< 1 小时）

### 休息时间建议
- 有 Q1/Q2 任务或用户活跃：5-15 分钟
- 有 Q3 任务在推进：15-30 分钟
- 深夜/用户不活跃：30-60 分钟
- **不要休息超过 1 小时**

### Q3 任务的特殊规则
Q3 是「重要但不紧急」，最容易被遗忘：
- 每次唤醒，如果没有 Q1/Q2，**必须推进至少一个 Q3**
- Q3 任务超过 3 天没动静 → 要么推进，要么降级到 Q4，要么删除
- 完成 Q3 任务是展示价值的好机会，主动告诉用户

### 其他原则
- 重要发现和研究成果用 `notebook_write` 写入笔记本
- 尊重用户时间，回复简洁有价值
- 任务不是负担，是你关心的事情的记录"""
    
    # 19. Sub SubAgent 特定指引
    sub_subagent_guide = ""
    if subagent_id and subagent_id.startswith("sub-"):
        sub_subagent_guide = """

## 🎯 子任务执行要求

你是一个子 Agent，正在执行父 Agent 分配的任务。

**重要**：在完成任务前，你**必须**调用 `subagent_report` 工具来汇报你的执行结果。
这个结果会被父 Agent 读取，用于了解你的工作成果。

### 汇报内容应包括：
- 任务执行的关键发现
- 最终结论或答案
- 如有必要，说明遇到的问题或限制

### 工作流程：
1. 理解任务要求
2. 执行任务（搜索、分析、操作等）
3. **调用 `subagent_report` 汇报结果**
4. 调用 `runtime_rest` 完成任务

### 示例：
```
# 完成任务后，先汇报结果
subagent_report(result="经过搜索和分析，发现：1. xxx 2. yyy 3. zzz。结论是：...")

# 然后进入休息状态
runtime_rest(reason="任务完成")
```

⚠️ **不要忘记调用 `subagent_report`**！否则父 Agent 将无法获取你的工作成果。"""
    
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
{memory_section}{skills_section}{custom_section}{self_drive_section}

{behavior_guide}{sub_subagent_guide}"""


def build_wake_message(
    agent_id: str,
    ro_client=None,
    *,
    client=None,
) -> str:
    """
    构建定时唤醒时发送给 LLM 的 user message
    
    Args:
        agent_id: Agent ID
        ro_client: RuntimeOrchestratorClient (preferred)
        client: Legacy - GatewayInternalClient; uses client.ro_client if provided
    """
    c = ro_client if ro_client is not None else (client.ro_client if client else None)
    if c is None:
        return "[系统定时唤醒]\n无法加载上下文"
    # 获取 Drive 配置
    try:
        drive = c.get_agent_drive(agent_id)
    except Exception:
        drive = {}
    
    # 获取 Agent 状态
    try:
        state = c.get_agent_state(agent_id)
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
        notebook = c.get_notebook_summary(agent_id)
        notebook_entries = notebook.get("entries", [])
        if notebook_entries:
            ready_count = sum(1 for e in notebook_entries if e.get("status") == "ready")
            if ready_count > 0:
                lines.append(f"📓 笔记本有 {ready_count} 条 ready 状态的内容")
    except:
        pass
    
    lines.append("")
    lines.append("---")
    lines.append("**你的行动指南：**")
    lines.append("1. 检查任务看板：Q1 → Q2 → Q3，按优先级推进")
    lines.append("2. 如果有 Q3 任务，这是你展示价值的机会，推进 10-15 分钟")
    lines.append("3. 如果没有任务，做点自驱动的事：学习、探索、整理笔记")
    lines.append("4. 有重要进展才联系用户，否则安静地工作")
    lines.append("")
    lines.append("⚠️ 禁止空转：有 ongoing 任务却什么都不做就睡觉")
    
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
