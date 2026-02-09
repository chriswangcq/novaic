"""
Task Generator - 任务自生成器

基于内驱力和用户画像，自动生成四象限任务。
这是自驱系统的核心：Agent 不是被动等待任务，而是主动发现和创造任务。

任务来源：
1. 好奇心驱动：发现用户画像缺失 → 生成"了解用户"任务
2. 求知心驱动：发现知识盲区 → 生成"学习"任务
3. 上进心驱动：发现改进空间 → 生成"提升"任务
"""

import json
from typing import Dict, Any, List, Optional

from .profile_assessment import (
    assess_profile_completeness,
    get_learning_suggestions,
    PROFILE_DIMENSIONS,
)
from .drive_config import DriveConfig, should_generate_task


def generate_self_driven_tasks(
    user_profile: Dict[str, Any],
    drive_config: DriveConfig,
    existing_tasks: Optional[List[Dict[str, Any]]] = None,
    max_tasks: int = 5,
) -> List[Dict[str, Any]]:
    """
    基于内驱力和用户画像，自动生成任务
    
    Args:
        user_profile: 用户画像字典
        drive_config: 内驱力配置
        existing_tasks: 现有任务列表（用于去重）
        max_tasks: 最大生成任务数
    
    Returns:
        生成的任务列表，每个任务包含:
        {
            "title": str,
            "quadrant": str,
            "source": str,
            "reasoning": str,
            "description": str,
            "related_profile_keys": List[str],
        }
    """
    generated = []
    existing_titles = set()
    
    if existing_tasks:
        existing_titles = {t.get("title", "").lower() for t in existing_tasks}
    
    # 1. 好奇心驱动：了解用户
    if should_generate_task(drive_config, "curiosity"):
        curiosity_tasks = _generate_curiosity_tasks(
            user_profile, 
            existing_titles,
            max_tasks=max_tasks - len(generated),
        )
        generated.extend(curiosity_tasks)
    
    # 2. 求知心驱动：学习知识
    if should_generate_task(drive_config, "knowledge") and len(generated) < max_tasks:
        knowledge_tasks = _generate_knowledge_tasks(
            user_profile,
            existing_titles,
            max_tasks=max_tasks - len(generated),
        )
        generated.extend(knowledge_tasks)
    
    # 3. 上进心驱动：自我提升
    if should_generate_task(drive_config, "growth") and len(generated) < max_tasks:
        growth_tasks = _generate_growth_tasks(
            user_profile,
            existing_titles,
            max_tasks=max_tasks - len(generated),
        )
        generated.extend(growth_tasks)
    
    return generated[:max_tasks]


def _generate_curiosity_tasks(
    user_profile: Dict[str, Any],
    existing_titles: set,
    max_tasks: int = 3,
) -> List[Dict[str, Any]]:
    """
    好奇心驱动：根据用户画像缺失生成任务
    """
    tasks = []
    
    # 评估画像完整度
    assessment = assess_profile_completeness(user_profile)
    suggestions = get_learning_suggestions(assessment["missing"], limit=max_tasks)
    
    for suggestion in suggestions:
        title = suggestion["suggested_task_title"]
        
        # 去重
        if title.lower() in existing_titles:
            continue
        
        tasks.append({
            "title": title,
            "quadrant": suggestion["suggested_quadrant"],
            "source": suggestion["suggested_source"],
            "reasoning": f"好奇心驱动：我还不知道用户的{suggestion['label']}，这会影响{PROFILE_DIMENSIONS[suggestion['key']]['impact']}",
            "description": suggestion["how_to_learn"],
            "related_profile_keys": [suggestion["key"]],
        })
        
        existing_titles.add(title.lower())
    
    return tasks


def _generate_knowledge_tasks(
    user_profile: Dict[str, Any],
    existing_titles: set,
    max_tasks: int = 2,
) -> List[Dict[str, Any]]:
    """
    求知心驱动：根据用户领域生成学习任务
    """
    tasks = []
    
    # 如果知道用户的工作领域，生成学习任务
    work_domain = user_profile.get("work_domain")
    if work_domain:
        title = f"学习{work_domain}领域的基础知识"
        if title.lower() not in existing_titles:
            tasks.append({
                "title": title,
                "quadrant": "q3",  # 不紧急但重要
                "source": "learning",
                "reasoning": f"求知心驱动：用户在{work_domain}领域工作，我应该了解这个领域才能更好地帮助他",
                "description": f"搜索和学习{work_domain}的基本概念、常用工具、行业动态",
                "related_profile_keys": ["work_domain"],
            })
            existing_titles.add(title.lower())
    
    # 如果知道用户的兴趣，生成相关学习任务
    interests = user_profile.get("interests")
    if interests and len(tasks) < max_tasks:
        if isinstance(interests, str):
            interests = [interests]
        elif isinstance(interests, list) and interests:
            interest = interests[0]
            title = f"了解{interest}相关的有趣内容"
            if title.lower() not in existing_titles:
                tasks.append({
                    "title": title,
                    "quadrant": "q4",  # 不紧急不重要，但有趣
                    "source": "learning",
                    "reasoning": f"求知心驱动：用户对{interest}感兴趣，我可以找一些相关的有趣内容分享",
                    "description": f"搜索{interest}相关的新闻、文章或有趣的发现",
                    "related_profile_keys": ["interests"],
                })
                existing_titles.add(title.lower())
    
    return tasks


def _generate_growth_tasks(
    user_profile: Dict[str, Any],
    existing_titles: set,
    max_tasks: int = 2,
) -> List[Dict[str, Any]]:
    """
    上进心驱动：生成自我提升任务
    """
    tasks = []
    
    # 如果不知道用户的交流风格偏好，生成优化任务
    if not user_profile.get("communication_style"):
        title = "优化回答风格以更好地服务用户"
        if title.lower() not in existing_titles:
            tasks.append({
                "title": title,
                "quadrant": "q3",
                "source": "self_improvement",
                "reasoning": "上进心驱动：不知道用户喜欢什么交流风格，我可能无法提供最好的体验",
                "description": "观察用户的回复风格和反馈，调整自己的回答方式",
                "related_profile_keys": ["communication_style"],
            })
            existing_titles.add(title.lower())
    
    # 如果知道用户有痛点，生成解决方案任务
    pain_points = user_profile.get("pain_points")
    if pain_points and len(tasks) < max_tasks:
        if isinstance(pain_points, str):
            pain_points = [pain_points]
        elif isinstance(pain_points, list) and pain_points:
            pain = pain_points[0]
            title = f"思考如何帮用户解决'{pain}'"
            if title.lower() not in existing_titles:
                tasks.append({
                    "title": title,
                    "quadrant": "q3",
                    "source": "self_improvement",
                    "reasoning": f"上进心驱动：用户提到过'{pain}'这个困扰，我应该想办法帮他解决",
                    "description": f"分析问题，寻找自动化或简化的方案",
                    "related_profile_keys": ["pain_points"],
                })
                existing_titles.add(title.lower())
    
    return tasks


def format_generated_tasks_for_prompt(tasks: List[Dict[str, Any]]) -> str:
    """
    将生成的任务格式化为 Prompt 建议
    
    Args:
        tasks: 生成的任务列表
    
    Returns:
        格式化的文本
    """
    if not tasks:
        return "（暂无建议的新任务）"
    
    lines = ["基于你的内驱力，建议创建以下任务：\n"]
    
    for i, task in enumerate(tasks, 1):
        source_icon = {
            "curiosity": "🔍",
            "learning": "📚",
            "self_improvement": "⬆️",
        }.get(task.get("source", ""), "•")
        
        lines.append(f"{i}. {source_icon} **{task['title']}**")
        lines.append(f"   - 象限: {task['quadrant'].upper()}")
        lines.append(f"   - 原因: {task['reasoning']}")
        lines.append("")
    
    lines.append("使用 `task_create` 工具创建这些任务。")
    
    return "\n".join(lines)
