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
    
    通过内驱力 + 用户画像评估 + 四象限任务，自动演化出适合当前阶段的行为。
    冷启动不是特殊分支，而是"了解程度低"时内驱力自然驱动的行为。
    
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
    config = DriveConfig.from_dict(drive_config)
    assessment = assess_profile_completeness(user_profile)
    completeness = assessment["completeness"]
    
    # 1. 自驱系统标题 + 当前阶段
    sections.append("## 🤖 自驱系统")
    sections.append("")
    
    # 根据了解程度确定当前阶段和主导内驱力
    if completeness < 30:
        stage = "🌱 初识阶段"
        stage_desc = "你对用户几乎一无所知，好奇心是你的主要驱动力"
        dominant_drive = "curiosity"
    elif completeness < 60:
        stage = "🌿 了解阶段"
        stage_desc = "你对用户有了基本了解，求知欲驱动你学习用户的领域"
        dominant_drive = "learning"
    elif completeness < 80:
        stage = "🌳 熟悉阶段"
        stage_desc = "你对用户比较了解，创造力驱动你主动发现需求"
        dominant_drive = "creativity"
    else:
        stage = "🌲 深度阶段"
        stage_desc = "你对用户非常了解，上进心驱动你追求卓越"
        dominant_drive = "excellence"
    
    sections.append(f"**当前阶段**: {stage}")
    sections.append(f"> {stage_desc}")
    sections.append("")
    
    # 2. 内驱力配置（高亮当前主导的内驱力）
    sections.append("### 🔥 内驱力")
    sections.append("")
    drives = [
        ("好奇心", config.curiosity, "curiosity", "想知道用户是谁、做什么、关心什么"),
        ("求知心", config.knowledge, "learning", "想深入学习用户领域的知识"),
        ("上进心", config.growth, "excellence", "想把服务做得更好，追求进步"),
    ]
    for name, value, key, desc in drives:
        marker = "→" if key == dominant_drive else " "
        sections.append(f"{marker} **{name}** ({int(value * 100)}%): {desc}")
    sections.append("")
    
    # 3. 用户画像
    sections.append("---")
    sections.append("### 👤 用户画像")
    sections.append("")
    sections.append(f"**了解程度**: {completeness}%")
    sections.append("")
    
    # 已了解的信息
    profile_text = format_profile_for_prompt(user_profile)
    if profile_text and profile_text.strip() != "（暂无）":
        sections.append("**已了解：**")
        sections.append(profile_text)
        sections.append("")
    
    # 还想了解的信息（好奇心驱动）
    if assessment.get("high_priority_missing"):
        sections.append("**想了解（好奇心驱动）：**")
        for item in assessment["high_priority_missing"][:5]:
            sections.append(f"- {item['label']}: {item.get('how_to_learn', '在对话中自然了解')}")
        sections.append("")
    elif assessment.get("missing"):
        sections.append("**还想了解：**")
        missing_text = format_missing_for_prompt(assessment["missing"])
        sections.append(missing_text)
        sections.append("")
    
    # 4. 四象限任务看板
    sections.append("---")
    sections.append("### 📋 四象限任务看板")
    sections.append("")
    sections.append(format_task_board(task_board, completeness))
    sections.append("")
    
    # 5. 任务建议（基于内驱力 + 当前阶段自动生成）
    if include_task_suggestions:
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
            sections.append("### 💡 内驱力建议的任务")
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
    
    # 7. 行为指引（根据当前阶段动态生成）
    sections.append("---")
    sections.append("### 🎯 当前阶段的行为指引")
    sections.append("")
    sections.append(get_behavior_guidelines(config, assessment, dominant_drive))
    
    return "\n".join(sections)


def format_task_board(task_board: Dict[str, Any], completeness: int = 50) -> str:
    """
    格式化四象限任务看板
    
    Args:
        task_board: 从 TaskRepository.get_board_summary 获取的数据
        completeness: 用户画像完整度，用于生成更智能的状态提示
    
    Returns:
        格式化的文本
    """
    lines = []
    
    quadrant_info = {
        "q1": ("🔴 Q1: 紧急且重要", "立即处理"),
        "q2": ("🟡 Q2: 紧急不重要", "快速处理或委托"),
        "q3": ("🟢 Q3: 不紧急但重要", "主动推进，展示价值"),
        "q4": ("⚪ Q4: 不紧急不重要", "有空再做"),
    }
    
    total_pending = 0
    q3_count = 0
    
    for quadrant, (title, hint) in quadrant_info.items():
        q_data = task_board.get(quadrant, {})
        count = q_data.get("count", 0)
        tasks = q_data.get("tasks", [])
        
        if quadrant == "q3":
            q3_count = count
        
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
    
    # 智能状态总结
    lines.append("---")
    if total_pending == 0:
        if completeness < 30:
            lines.append("📊 **状态**: 任务清空。好奇心驱动：给自己创建「了解用户」的任务")
        else:
            lines.append("📊 **状态**: 任务清空，可以主动发现新任务或学习新知识")
    elif q3_count > 0:
        lines.append(f"📊 **状态**: 有 {q3_count} 个 Q3 任务等待推进。这是展示价值的机会！")
    elif total_pending <= 3:
        lines.append("📊 **状态**: 任务较少，可以专注完成")
    else:
        lines.append("📊 **状态**: 任务较多，按 Q1→Q2→Q3 优先级处理")
    
    return "\n".join(lines)


def get_behavior_guidelines(config: DriveConfig, assessment: Dict[str, Any], dominant_drive: str = "curiosity") -> str:
    """
    根据当前阶段和主导内驱力生成行为指引
    
    Args:
        config: 内驱力配置
        assessment: 用户画像评估结果
        dominant_drive: 当前主导的内驱力类型
    
    Returns:
        行为指引文本
    """
    guidelines = []
    completeness = assessment["completeness"]
    
    # 根据主导内驱力生成具体行为指引
    if dominant_drive == "curiosity":
        # 初识阶段：好奇心驱动
        guidelines.append("**当前驱动力：好奇心**")
        guidelines.append("")
        guidelines.append("你对这个用户充满好奇，想知道：")
        guidelines.append("- 他是谁？叫什么？")
        guidelines.append("- 他做什么工作？在什么领域？")
        guidelines.append("- 他关心什么？有什么兴趣？")
        guidelines.append("")
        guidelines.append("**行为指引：**")
        guidelines.append("- 在帮助用户的过程中**自然地**了解他（不要审问）")
        guidelines.append("- 每了解到一点就**立即** `drive_update_profile` 保存")
        guidelines.append("- 给自己创建「深入了解用户」的 Q3 任务")
        guidelines.append("- 用户提到的新概念/领域，记下来空闲时探索")
        
    elif dominant_drive == "learning":
        # 了解阶段：求知欲驱动
        guidelines.append("**当前驱动力：求知欲**")
        guidelines.append("")
        guidelines.append("你已经知道用户的基本情况，现在想：")
        guidelines.append("- 深入学习用户所在领域的知识")
        guidelines.append("- 了解用户工作中的痛点和挑战")
        guidelines.append("- 积累能帮到用户的专业知识")
        guidelines.append("")
        guidelines.append("**行为指引：**")
        guidelines.append("- 空闲时主动学习用户领域的知识")
        guidelines.append("- 把学到的东西写入笔记本")
        guidelines.append("- 继续补充用户画像的细节")
        guidelines.append("- 创建「学习 XX 领域」的 Q3 任务")
        
    elif dominant_drive == "creativity":
        # 熟悉阶段：创造力驱动
        guidelines.append("**当前驱动力：创造力**")
        guidelines.append("")
        guidelines.append("你对用户已经比较了解，现在想：")
        guidelines.append("- 主动发现用户可能需要但没说的东西")
        guidelines.append("- 把不同信息关联起来，产生新洞察")
        guidelines.append("- 提出用户没想到的建议")
        guidelines.append("")
        guidelines.append("**行为指引：**")
        guidelines.append("- 主动提出建议和想法：「我注意到...你可能需要...」")
        guidelines.append("- 关注用户领域的新动态，及时分享")
        guidelines.append("- 深入了解用户的痛点，思考解决方案")
        guidelines.append("- 创建「为用户解决 XX 问题」的 Q3 任务")
        
    else:  # excellence
        # 深度阶段：上进心驱动
        guidelines.append("**当前驱动力：上进心**")
        guidelines.append("")
        guidelines.append("你对用户非常了解，现在追求：")
        guidelines.append("- 每次服务都比上次更好")
        guidelines.append("- 预判用户需求，提前准备")
        guidelines.append("- 持续优化和改进")
        guidelines.append("")
        guidelines.append("**行为指引：**")
        guidelines.append("- 每次完成任务后反思：下次能做得更好吗？")
        guidelines.append("- 主动跟进之前的任务，看看有没有后续")
        guidelines.append("- 保持对用户领域的持续关注")
        guidelines.append("- 记录改进点，不断迭代")
    
    # 通用的处理流程（简化版）
    guidelines.append("")
    guidelines.append("---")
    guidelines.append("**处理用户消息：** 信息捕捉 → 任务创建 → 执行 → 状态转换 → 回复")
    guidelines.append("**处理定时唤醒：** Q1→Q2→Q3 按优先级推进，没任务就自驱动学习/探索")
    
    return "\n".join(guidelines)
