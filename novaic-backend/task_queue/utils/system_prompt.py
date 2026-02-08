"""
System Prompt Builder - 构建 Agent 基础身份提示词

为每个新 Runtime 注入基础 System Prompt，包含：
- Agent 身份和名称
- 能力概览
- 用户画像摘要
- 交流风格指引
- 使用 drive/notebook 工具的提示

与 drive_prompt.py 的区别：
- system_prompt: 每个 session 都注入（user_message + scheduled_wake）
- drive_prompt: 仅在 scheduled_wake 时注入
"""

import json
from typing import Optional

from ..client import GatewayInternalClient


def build_system_prompt(agent_id: str, client: GatewayInternalClient) -> Optional[str]:
    """
    构建基础系统提示词
    
    Args:
        agent_id: Agent ID
        client: GatewayInternalClient 实例
        
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
    
    # 3. Get assigned skills
    try:
        skills_resp = client.get_agent_skills(agent_id)
        assigned_skills = skills_resp.get("skills", [])
    except Exception as e:
        print(f"[system_prompt] Failed to get skills for {agent_id}: {e}")
        assigned_skills = []
    
    # 4. Get custom instructions
    custom_instructions = drive.get("custom_instructions", "")
    
    # 5. 构建用户画像部分
    user_profile = drive.get("user_profile", {})
    if user_profile:
        profile_str = json.dumps(user_profile, ensure_ascii=False, indent=2)
    else:
        profile_str = "尚未了解用户。在对话中注意观察用户的偏好、习惯和兴趣，用 drive_update_profile 记录。"
    
    # 6. 交流风格
    communication_style = drive.get("communication_style", "friendly")
    style_map = {
        "friendly": "友好、自然、像朋友一样交流",
        "professional": "专业、简洁、注重效率",
        "casual": "轻松、随意、幽默",
        "formal": "正式、礼貌、详细",
    }
    style_desc = style_map.get(communication_style, communication_style)
    
    # 7. 个性特征
    personality = drive.get("personality", {})
    personality_str = ""
    if personality:
        traits = []
        for k, v in personality.items():
            traits.append(f"- {k}: {v}")
        if traits:
            personality_str = "\n## 你的个性\n" + "\n".join(traits) + "\n"
    
    # 8. 关系信息
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
    
    # Build skills section
    skills_section = ""
    if assigned_skills:
        skill_parts = []
        for skill in assigned_skills:
            skill_text = f"### {skill.get('name', 'Unnamed Skill')}"
            if skill.get('description'):
                skill_text += f"\n{skill['description']}"
            if skill.get('prompt'):
                skill_text += f"\n{skill['prompt']}"
            if skill.get('workflow'):
                skill_text += f"\n\n工作流:\n{skill['workflow']}"
            skill_parts.append(skill_text)
        skills_section = "\n\n## 你的技能\n" + "\n\n".join(skill_parts)
    
    # Custom instructions
    custom_section = ""
    if custom_instructions:
        custom_section = f"\n\n## 额外指令\n{custom_instructions}"
    
    return f"""[系统] 你是 {agent_name}，一个运行在用户桌面虚拟机中的 AI Agent。
你有持久记忆和学习能力，能够跨对话记住用户的偏好和习惯。

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
