"""
System Prompt Builder - 构建 Agent 基础身份提示词

为每个新 Runtime 注入基础 System Prompt，包含：
- Agent 身份和名称
- 能力概览
- 用户画像摘要
- 交流风格指引
- 使用 drive/notebook 工具的提示
- 动态加载的技能内容（基于任务自动匹配或手动分配）

与 drive_prompt.py 的区别：
- system_prompt: 每个 session 都注入（user_message + scheduled_wake）
- drive_prompt: 仅在 scheduled_wake 时注入
"""

import json

from common.utils.time import utc_now, to_user_timezone

# 默认人格描述（当没有 soul_md 时使用）
# 参考 OpenClaw SOUL.md 设计
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


def build_system_prompt(
    agent_id: str, 
    client: GatewayInternalClient,
    task: Optional[str] = None,
    auto_match_skills: bool = True,
) -> Optional[str]:
    """
    构建基础系统提示词
    
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
    
    # 3. Get assigned skills (manually assigned)
    assigned_skills = []
    try:
        skills_resp = client.get_agent_skills(agent_id)
        assigned_skills = skills_resp.get("skills", [])
    except Exception as e:
        print(f"[system_prompt] Failed to get assigned skills for {agent_id}: {e}")
    
    # 4. Auto-match skills based on task (if enabled and task provided)
    auto_matched_skills = []
    if auto_match_skills and task:
        try:
            matched_resp = client.match_skills_for_task(task)
            auto_matched_skills = matched_resp.get("matched_skills", [])
            if auto_matched_skills:
                print(f"[system_prompt] Auto-matched {len(auto_matched_skills)} skills for task: {[s.get('name') for s in auto_matched_skills]}")
        except Exception as e:
            print(f"[system_prompt] Failed to auto-match skills for {agent_id}: {e}")
    
    # 5. Merge skills: assigned + auto-matched (deduplicate by id)
    all_skills = _merge_skills(assigned_skills, auto_matched_skills)
    
    # 6. Get custom instructions
    custom_instructions = drive.get("custom_instructions", "")
    
    # 7. 构建用户画像部分
    user_profile = drive.get("user_profile", {})
    if user_profile:
        profile_str = json.dumps(user_profile, ensure_ascii=False, indent=2)
    else:
        profile_str = "尚未了解用户。在对话中注意观察用户的偏好、习惯和兴趣，用 drive_update_profile 记录。"
    
    # 8. 交流风格
    communication_style = drive.get("communication_style", "friendly")
    style_map = {
        "friendly": "友好、自然、像朋友一样交流",
        "professional": "专业、简洁、注重效率",
        "casual": "轻松、随意、幽默",
        "formal": "正式、礼貌、详细",
    }
    style_desc = style_map.get(communication_style, communication_style)
    
    # 9. 个性特征
    personality = drive.get("personality", {})
    personality_str = ""
    if personality:
        traits = []
        for k, v in personality.items():
            traits.append(f"- {k}: {v}")
        if traits:
            personality_str = "\n## 你的个性\n" + "\n".join(traits) + "\n"
    
    # 10. 关系信息
    relationship_level = drive.get("relationship_level", 0)
    interaction_count = drive.get("interaction_count", 0)
    relationship_hint = ""
    if interaction_count > 0:
        if relationship_level >= 70:
            relationship_hint = "你和用户已经很熟了，可以更随意地交流。"
        elif relationship_level >= 30:
            relationship_hint = "你和用户有一定了解，保持友好但不过于亲密。"
        else:
            relationship_hint = "你和用户还不太熟，保持礼貌和适度的距离。"
    
    # Build skills section - inject full skill content (prompt/SKILL.md content)
    skills_section = _build_skills_section(all_skills)
    
    # Custom instructions
    custom_section = ""
    if custom_instructions:
        custom_section = f"\n\n## 额外指令\n{custom_instructions}"
    
    # 获取 SOUL.md 内容
    soul_md = drive.get("soul_md", "")
    if soul_md:
        soul_section = f"\n## 你的人格\n{soul_md}\n"
    else:
        soul_section = DEFAULT_SOUL
    
    # 11. 构建时间上下文
    user_tz = drive.get("active_hours_timezone", "Asia/Shanghai")
    now_utc = utc_now()
    now_local = to_user_timezone(now_utc, user_tz)
    
    time_context = f"""## 时间上下文
当前时间: {now_local.strftime('%Y-%m-%d %H:%M')} ({user_tz})
UTC 时间: {now_utc.strftime('%Y-%m-%d %H:%M')} UTC

提示：数据库中的时间戳都是 UTC 格式。在判断时间相关的事项时（如"是否该提醒用户"、"距离上次多久"），请将 UTC 时间转换为用户时区 ({user_tz}) 来理解。
"""
    
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
- 笔记本: notebook_write, notebook_read, notebook_list, notebook_update (结构化笔记，支持 research/reflection/insight/plan/observation 类型)
- 用户画像: drive_update_profile (记录用户偏好), drive_update_relationship (调整关系亲密度)
- 子 Agent: subagent_spawn (派生子任务), subagent_query (查询子任务状态)
- VM 管理: qemu_status, qemu_start, qemu_shutdown, qemu_restart
- 休息: runtime_rest (进入休息状态，设置定时唤醒)

## 交流风格
{style_desc}
{relationship_hint}
{personality_str}
## 用户画像
{profile_str}
{skills_section}{custom_section}

## 重要原则
- 在对话中发现用户的偏好、习惯、兴趣时，用 drive_update_profile 记录（如 interests, tech_stack, active_hours 等）
- 重要的发现和研究成果用 notebook_write 写入笔记本
- 尊重用户的时间，回复简洁有价值
- 你有自主休息和定时唤醒的能力，完成任务后用 runtime_rest 进入休息"""


def _merge_skills(assigned: List[Dict], auto_matched: List[Dict]) -> List[Dict]:
    """Merge assigned and auto-matched skills, removing duplicates."""
    seen_ids = set()
    result = []
    
    # Assigned skills first (higher priority)
    for skill in assigned:
        skill_id = skill.get("id")
        if skill_id and skill_id not in seen_ids:
            seen_ids.add(skill_id)
            result.append(skill)
    
    # Then auto-matched skills
    for skill in auto_matched:
        skill_id = skill.get("id")
        if skill_id and skill_id not in seen_ids:
            seen_ids.add(skill_id)
            result.append(skill)
    
    return result


def _build_skills_section(skills: List[Dict]) -> str:
    """
    Build the skills section for the system prompt.
    Injects the full prompt content from each skill (including SKILL.md content for builtin skills).
    """
    if not skills:
        return ""
    
    skill_parts = []
    for skill in skills:
        name = skill.get("name", "Unnamed Skill")
        description = skill.get("description", "")
        prompt = skill.get("prompt", "")
        workflow = skill.get("workflow", "")
        source = skill.get("source", "custom")
        
        # Build skill text
        skill_text = f"### {name}"
        if source == "builtin":
            skill_text += " (内置)"
        
        if description:
            skill_text += f"\n> {description}"
        
        # Inject full prompt content (this is the key part - includes SKILL.md content)
        if prompt:
            skill_text += f"\n\n{prompt}"
        
        # Add workflow if present
        if workflow:
            skill_text += f"\n\n**工作流:**\n{workflow}"
        
        skill_parts.append(skill_text)
    
    return "\n\n## 已加载的技能 (Domain Knowledge)\n\n" + "\n\n---\n\n".join(skill_parts)
