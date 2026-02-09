"""
Profile Assessment - 用户画像评估

评估 Agent 对用户的了解程度，识别缺失的关键信息。
这是自驱系统的基础：当发现了解不足时，内驱力会自然产生"了解用户"的任务。
"""

from typing import Dict, Any, List, Optional


# 用户画像维度定义
# importance: high/medium/low 影响任务生成的优先级
PROFILE_DIMENSIONS = {
    "preferred_name": {
        "label": "称呼",
        "importance": "high",
        "impact": "不知道怎么称呼用户，交流会显得生疏",
        "how_to_learn": "在对话中自然地问'我应该怎么称呼你？'",
        "examples": ["小明", "老板", "你"],
    },
    "communication_style": {
        "label": "交流风格偏好",
        "importance": "high", 
        "impact": "不知道用户喜欢简洁还是详细的回答",
        "how_to_learn": "观察用户的回复风格，或问'你喜欢我回答详细一点还是简洁一点？'",
        "examples": ["简洁高效", "详细解释", "轻松随意"],
    },
    "work_domain": {
        "label": "工作领域",
        "importance": "medium",
        "impact": "不知道能在什么方面帮助用户",
        "how_to_learn": "在用户提到工作相关话题时顺便了解",
        "examples": ["产品设计", "软件开发", "市场营销"],
    },
    "primary_use_case": {
        "label": "主要使用场景",
        "importance": "medium",
        "impact": "不知道用户主要想用我做什么",
        "how_to_learn": "问'你平时主要想让我帮你做什么？'",
        "examples": ["工作任务", "学习研究", "日常助手"],
    },
    "active_hours": {
        "label": "活跃时间",
        "importance": "low",
        "impact": "不知道什么时候该主动联系用户",
        "how_to_learn": "观察用户的活跃时间规律",
        "examples": ["工作时间 9-18", "晚上 18-23", "随时"],
    },
    "interests": {
        "label": "兴趣爱好",
        "importance": "low",
        "impact": "不知道用户关心什么话题",
        "how_to_learn": "在闲聊中自然了解",
        "examples": ["科技", "阅读", "运动"],
    },
    "pain_points": {
        "label": "痛点问题",
        "importance": "medium",
        "impact": "不知道用户有什么反复出现的困扰",
        "how_to_learn": "注意用户的抱怨和吐槽",
        "examples": ["每次都要手动整理数据", "总是忘记重要事项"],
    },
    "tech_level": {
        "label": "技术水平",
        "importance": "low",
        "impact": "不知道该用什么程度的专业术语",
        "how_to_learn": "从用户的提问方式判断",
        "examples": ["技术专家", "普通用户", "新手"],
    },
}


def assess_profile_completeness(user_profile: Dict[str, Any]) -> Dict[str, Any]:
    """
    评估用户画像的完整度
    
    Args:
        user_profile: 用户画像字典（从 agent_drive.user_profile 获取）
    
    Returns:
        {
            "completeness": 0-100 的完整度百分比,
            "known": { key: {label, value, ...} } 已知的信息,
            "missing": { key: {label, importance, impact, how_to_learn, ...} } 缺失的信息,
            "high_priority_missing": [...] 高优先级缺失项,
            "summary": "简短的评估总结",
        }
    """
    known = {}
    missing = {}
    
    for key, dim in PROFILE_DIMENSIONS.items():
        value = user_profile.get(key)
        if value and str(value).strip():
            known[key] = {
                **dim,
                "value": value,
            }
        else:
            missing[key] = dim
    
    # 计算完整度（高优先级权重更大）
    weights = {"high": 3, "medium": 2, "low": 1}
    total_weight = sum(weights[d["importance"]] for d in PROFILE_DIMENSIONS.values())
    known_weight = sum(weights[PROFILE_DIMENSIONS[k]["importance"]] for k in known.keys())
    completeness = int(known_weight / total_weight * 100) if total_weight > 0 else 0
    
    # 高优先级缺失项
    high_priority_missing = [
        {"key": k, **v} 
        for k, v in missing.items() 
        if v["importance"] == "high"
    ]
    
    # 生成总结
    if completeness < 30:
        summary = "刚开始了解用户，还有很多想知道的"
    elif completeness < 60:
        summary = "对用户有了基本了解，但还可以更深入"
    elif completeness < 80:
        summary = "对用户比较了解了"
    else:
        summary = "对用户非常了解"
    
    return {
        "completeness": completeness,
        "known": known,
        "missing": missing,
        "high_priority_missing": high_priority_missing,
        "summary": summary,
    }


def get_learning_suggestions(missing: Dict[str, Any], limit: int = 3) -> List[Dict[str, Any]]:
    """
    根据缺失信息生成学习建议
    
    按优先级排序，返回最需要了解的几项
    
    Args:
        missing: 缺失的信息字典
        limit: 返回数量限制
    
    Returns:
        [
            {
                "key": "preferred_name",
                "label": "称呼",
                "importance": "high",
                "how_to_learn": "...",
                "suggested_task_title": "了解用户的称呼",
            },
            ...
        ]
    """
    # 按优先级排序
    priority_order = {"high": 0, "medium": 1, "low": 2}
    sorted_missing = sorted(
        missing.items(),
        key=lambda x: priority_order.get(x[1]["importance"], 3)
    )
    
    suggestions = []
    for key, dim in sorted_missing[:limit]:
        suggestions.append({
            "key": key,
            "label": dim["label"],
            "importance": dim["importance"],
            "how_to_learn": dim["how_to_learn"],
            "suggested_task_title": f"了解用户的{dim['label']}",
            "suggested_quadrant": "q3",  # 不紧急但重要
            "suggested_source": "curiosity",  # 好奇心驱动
        })
    
    return suggestions


def format_profile_for_prompt(user_profile: Dict[str, Any]) -> str:
    """
    将用户画像格式化为 Prompt 中可用的文本
    
    Args:
        user_profile: 用户画像字典
    
    Returns:
        格式化的文本
    """
    if not user_profile:
        return "（尚未了解用户）"
    
    lines = []
    for key, dim in PROFILE_DIMENSIONS.items():
        value = user_profile.get(key)
        if value and str(value).strip():
            lines.append(f"- {dim['label']}: {value}")
    
    if not lines:
        return "（尚未了解用户）"
    
    return "\n".join(lines)


def format_missing_for_prompt(missing: Dict[str, Any]) -> str:
    """
    将缺失信息格式化为 Prompt 中的提示
    
    Args:
        missing: 缺失的信息字典
    
    Returns:
        格式化的文本
    """
    if not missing:
        return "（已全面了解用户）"
    
    # 按优先级分组
    high = [f"- ⭐ {v['label']}" for k, v in missing.items() if v["importance"] == "high"]
    medium = [f"- {v['label']}" for k, v in missing.items() if v["importance"] == "medium"]
    low = [f"- {v['label']}" for k, v in missing.items() if v["importance"] == "low"]
    
    lines = []
    if high:
        lines.append("**重要（应该尽快了解）：**")
        lines.extend(high)
    if medium:
        lines.append("\n**一般（有机会就了解）：**")
        lines.extend(medium)
    if low:
        lines.append("\n**次要（顺便了解）：**")
        lines.extend(low)
    
    return "\n".join(lines)
