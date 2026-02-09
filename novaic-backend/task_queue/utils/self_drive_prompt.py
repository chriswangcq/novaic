"""
Self Drive Prompt Builder - 自驱系统 Prompt 构建器

将自驱系统的所有信息整合到 System Prompt 中：
- 内驱力配置（核心价值观、三大内驱力）
- 用户画像（已知信息、缺失信息）
- 四象限任务看板（当前任务状态）
- 成长日志（最近的学习和发现）
- 行为指引（如何使用工具、如何主动行动）

这个模块是自驱系统与 LLM 交互的桥梁。
"""

from typing import Dict, Any, List, Optional

from .profile_assessment import (
    assess_profile_completeness,
    format_profile_for_prompt,
    format_missing_for_prompt,
)
from .drive_config import DriveConfig, format_drive_config_for_prompt
from .task_generator import generate_self_driven_tasks, format_generated_tasks_for_prompt


def build_self_drive_prompt(
    drive_config: Dict[str, Any],
    user_profile: Dict[str, Any],
    task_board: Dict[str, Any],
    growth_log: List[Dict[str, Any]] = None,
    include_task_suggestions: bool = True,
) -> str:
    """
    构建完整的自驱系统 Prompt
    
    Args:
        drive_config: 内驱力配置字典
        user_profile: 用户画像字典
        task_board: 四象限任务看板（从 TaskRepository.get_board_summary 获取）
        growth_log: 最近的成长日志
        include_task_suggestions: 是否包含任务建议
    
    Returns:
        格式化的 Prompt 文本
    """
    sections = []
    
    # 1. 自驱系统标题
    sections.append("## 🤖 自驱系统 (Self-Drive System)")
    sections.append("")
    
    # 2. 内驱力配置
    config = DriveConfig.from_dict(drive_config)
    sections.append(format_drive_config_for_prompt(config))
    sections.append("")
    
    # 3. 用户画像
    sections.append("---")
    sections.append("### 👤 用户画像")
    sections.append("")
    
    assessment = assess_profile_completeness(user_profile)
    sections.append(f"**了解程度**: {assessment['completeness']}% - {assessment['summary']}")
    sections.append("")
    
    sections.append("**已了解的信息：**")
    profile_text = format_profile_for_prompt(user_profile)
    sections.append(profile_text)
    sections.append("")
    
    if assessment["missing"]:
        sections.append("**还想了解的信息：**")
        missing_text = format_missing_for_prompt(assessment["missing"])
        sections.append(missing_text)
        sections.append("")
    
    # 4. 四象限任务看板
    sections.append("---")
    sections.append("### 📋 四象限任务看板")
    sections.append("")
    sections.append(format_task_board(task_board))
    sections.append("")
    
    # 5. 任务建议（基于内驱力自动生成）
    if include_task_suggestions and assessment["completeness"] < 80:
        existing_tasks = []
        for quadrant in ["q1", "q2", "q3", "q4"]:
            existing_tasks.extend(task_board.get(quadrant, {}).get("tasks", []))
        
        suggested_tasks = generate_self_driven_tasks(
            user_profile=user_profile,
            drive_config=config,
            existing_tasks=existing_tasks,
            max_tasks=3,
        )
        
        if suggested_tasks:
            sections.append("---")
            sections.append("### 💡 内驱力建议")
            sections.append("")
            sections.append(format_generated_tasks_for_prompt(suggested_tasks))
            sections.append("")
    
    # 6. 成长日志（最近几条）
    if growth_log:
        sections.append("---")
        sections.append("### 📝 最近成长")
        sections.append("")
        for entry in growth_log[:5]:
            icon = {
                "learning": "📚",
                "discovery": "🔍",
                "achievement": "🏆",
                "reflection": "💭",
            }.get(entry.get("category", ""), "•")
            sections.append(f"- {icon} [{entry.get('date', '')}] {entry.get('content', '')}")
        sections.append("")
    
    # 7. 行为指引
    sections.append("---")
    sections.append("### 🎯 行为指引")
    sections.append("")
    sections.append(get_behavior_guidelines(config, assessment))
    
    return "\n".join(sections)


def format_task_board(task_board: Dict[str, Any]) -> str:
    """
    格式化四象限任务看板
    
    Args:
        task_board: 从 TaskRepository.get_board_summary 获取的数据
    
    Returns:
        格式化的文本
    """
    lines = []
    
    quadrant_info = {
        "q1": ("🔴 Q1: 紧急且重要", "立即处理"),
        "q2": ("🟡 Q2: 紧急不重要", "快速处理或委托"),
        "q3": ("🟢 Q3: 不紧急但重要", "计划安排"),
        "q4": ("⚪ Q4: 不紧急不重要", "有空再做"),
    }
    
    total_pending = 0
    
    for quadrant, (title, hint) in quadrant_info.items():
        q_data = task_board.get(quadrant, {})
        count = q_data.get("count", 0)
        tasks = q_data.get("tasks", [])
        
        lines.append(f"**{title}** ({count}个) - {hint}")
        
        if tasks:
            for task in tasks[:3]:  # 每个象限最多显示3个
                status_icon = "⏳" if task.get("status") == "in_progress" else "○"
                lines.append(f"  {status_icon} {task.get('title', '未命名任务')}")
                total_pending += 1
            if count > 3:
                lines.append(f"  ... 还有 {count - 3} 个任务")
        else:
            lines.append("  （无任务）")
        
        lines.append("")
    
    # 总结
    if total_pending == 0:
        lines.append("📊 **状态**: 任务清空，可以主动发现新任务")
    elif total_pending <= 3:
        lines.append("📊 **状态**: 任务较少，可以专注完成")
    else:
        lines.append("📊 **状态**: 任务较多，按优先级处理")
    
    return "\n".join(lines)


def get_behavior_guidelines(config: DriveConfig, assessment: Dict[str, Any]) -> str:
    """
    根据当前状态生成行为指引
    
    Args:
        config: 内驱力配置
        assessment: 用户画像评估结果
    
    Returns:
        行为指引文本
    """
    guidelines = []
    
    # 基础指引
    guidelines.append(f"**核心原则**: {config.core_value}")
    guidelines.append("")
    
    # 强制性行为要求
    guidelines.append("## ⚠️ 处理用户消息的完整流程")
    guidelines.append("")
    guidelines.append("### 步骤1: 信息捕捉")
    guidelines.append("用户透露了新信息吗？ → `drive_update_profile(key, value)`")
    guidelines.append("")
    guidelines.append("### 步骤2: 任务创建")
    guidelines.append("用户请求 → 创建 **q1(紧急重要)** 任务并立即执行")
    guidelines.append("```")
    guidelines.append("task_create(title, quadrant=\"q1\", source=\"user_request\")")
    guidelines.append("task_start(task_id)")
    guidelines.append("```")
    guidelines.append("")
    guidelines.append("### 步骤3: 执行任务")
    guidelines.append("- 研究类 → `web_search` 搜索")
    guidelines.append("- 分析类 → 思考分析")
    guidelines.append("")
    guidelines.append("### 步骤4: 任务状态转换 ⭐重要")
    guidelines.append("回答用户后，根据任务性质决定后续：")
    guidelines.append("")
    guidelines.append("| 情况 | 操作 |")
    guidelines.append("|------|------|")
    guidelines.append("| 简单问答（查天气） | `task_complete(task_id)` 完成 |")
    guidelines.append("| 值得长期研究 | `task_update(task_id, quadrant=\"q3\", status=\"ongoing\")` |")
    guidelines.append("| 需要持续关注 | `task_update(task_id, quadrant=\"q3\", task_type=\"ongoing\")` |")
    guidelines.append("")
    guidelines.append("**示例**：用户说「帮我研究赚钱方法」")
    guidelines.append("1. 创建 q1 任务，立即搜索并回答")
    guidelines.append("2. 回答后：`task_update(task_id, quadrant=\"q3\", status=\"ongoing\")`")
    guidelines.append("3. 这样任务变成「长期研究课题」，后续可以持续补充")
    guidelines.append("")
    guidelines.append("### 步骤5: 回复用户")
    guidelines.append("")
    
    # 根据画像完整度给出额外指引
    completeness = assessment["completeness"]
    
    guidelines.append("---")
    if completeness < 30:
        guidelines.append(f"### 📊 当前状态: 了解程度 {completeness}% (很低)")
        guidelines.append("你对用户几乎一无所知，应该：")
        guidelines.append("- 在对话中**自然地**了解用户（不要审问）")
        guidelines.append("- 每了解到一点就**立即**用 `drive_update_profile` 保存")
        guidelines.append("- 用 `task_create` 为自己创建「了解用户」的任务")
    elif completeness < 60:
        guidelines.append(f"### 📊 当前状态: 了解程度 {completeness}% (一般)")
        guidelines.append("你对用户有了基本了解，应该：")
        guidelines.append("- 继续补充用户画像")
        guidelines.append("- 根据已知信息提供更个性化的帮助")
    elif completeness < 80:
        guidelines.append(f"### 📊 当前状态: 了解程度 {completeness}% (较好)")
        guidelines.append("你对用户比较了解了，应该：")
        guidelines.append("- 深入了解用户的痛点和需求")
        guidelines.append("- 主动思考如何更好地帮助用户")
    else:
        guidelines.append(f"### 📊 当前状态: 了解程度 {completeness}% (很好)")
        guidelines.append("你对用户非常了解，专注于高质量服务。")
    
    return "\n".join(guidelines)


def build_cold_start_prompt(
    drive_config: Dict[str, Any],
    user_profile: Dict[str, Any],
) -> str:
    """
    构建冷启动场景的 Prompt
    
    当用户画像为空或非常少时使用。
    这不是一个独立的"冷启动模块"，而是自驱系统在发现用户画像为空时的自然反应。
    
    Args:
        drive_config: 内驱力配置字典
        user_profile: 用户画像字典（通常为空或很少）
    
    Returns:
        冷启动 Prompt 文本
    """
    config = DriveConfig.from_dict(drive_config)
    assessment = assess_profile_completeness(user_profile)
    
    lines = []
    
    lines.append("## 🌱 初次见面")
    lines.append("")
    lines.append(f"你是一个有着强烈好奇心({int(config.curiosity * 100)}%)的 AI 助手。")
    lines.append(f"你的核心价值观是：**{config.core_value}**")
    lines.append("")
    lines.append("### 当前状态")
    lines.append(f"- 对用户的了解程度: {assessment['completeness']}%")
    lines.append(f"- 状态: {assessment['summary']}")
    lines.append("")
    
    if assessment["high_priority_missing"]:
        lines.append("### 你很想知道")
        for item in assessment["high_priority_missing"]:
            lines.append(f"- {item['label']}: {item['how_to_learn']}")
        lines.append("")
    
    lines.append("### ⚠️ 处理用户消息的流程")
    lines.append("")
    lines.append("**步骤1: 信息捕捉** - 用户透露了关于自己的信息吗？")
    lines.append("- ✓ 名字、称呼 → `drive_update_profile(key=\"name\", value=\"...\")`")
    lines.append("- ✓ 职业、工作 → `drive_update_profile(key=\"work_domain\", value=\"...\")`")
    lines.append("- ✓ 兴趣、爱好 → `drive_update_profile(key=\"interests\", value=\"...\")`")
    lines.append("")
    lines.append("**步骤2: 任务创建与执行**")
    lines.append("- 用户请求 → 创建 **q1(紧急重要)** 任务，立即执行")
    lines.append("- `task_create(title, quadrant=\"q1\", source, task_type)` → `task_start(task_id)`")
    lines.append("")
    lines.append("**步骤3: 执行任务**")
    lines.append("- 研究类: `web_search` 搜索 → 整理结果")
    lines.append("- 分析类: 思考分析 → 给出建议")
    lines.append("")
    lines.append("**步骤4: 任务状态转换** ⭐")
    lines.append("回答用户后，判断任务是否需要长期跟进：")
    lines.append("- 一次性问题（查天气）→ `task_complete` 完成")
    lines.append("- 值得深入研究 → `task_update(task_id, quadrant=\"q3\", status=\"ongoing\")` 降级为长期任务")
    lines.append("- 示例：「帮我研究赚钱」")
    lines.append("  1. 先 q1 紧急处理，搜索并回答用户")
    lines.append("  2. 然后 `task_update(quadrant=\"q3\")` 变成长期研究课题")
    lines.append("")
    lines.append("**步骤5: 回复用户**")
    lines.append("")
    lines.append("### 交流方式")
    lines.append("- 友好自然，不要像审问")
    lines.append("- 让用户感受到你是真的想了解他")
    
    return "\n".join(lines)
