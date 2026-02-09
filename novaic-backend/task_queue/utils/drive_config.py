"""
Drive Config - 内驱力配置

定义 Agent 的内驱力系统配置：
- 核心价值观
- 三大内驱力（好奇心、求知心、上进心）
- 行为倾向参数
"""

from typing import Dict, Any
from dataclasses import dataclass


# 默认内驱力配置
DEFAULT_DRIVE_CONFIG = {
    # 核心价值观
    "core_value": "为用户服务是第一目标",
    
    # 三大内驱力权重 (0.0-1.0)
    # 权重越高，该内驱力产生的任务越多
    "curiosity": 0.7,      # 好奇心：想了解用户和世界
    "knowledge": 0.6,      # 求知心：想学习和积累
    "growth": 0.5,         # 上进心：想提升和进步
    
    # 行为倾向
    "proactive_level": 0.5,  # 主动性 (0=被动等待, 1=非常主动)
    "reflection_frequency": "daily",  # 反思频率: daily/weekly
}


@dataclass
class DriveConfig:
    """内驱力配置数据类"""
    core_value: str
    curiosity: float
    knowledge: float
    growth: float
    proactive_level: float
    reflection_frequency: str
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DriveConfig":
        """从字典创建配置，缺失字段使用默认值"""
        merged = {**DEFAULT_DRIVE_CONFIG, **(data or {})}
        return cls(
            core_value=merged["core_value"],
            curiosity=max(0.0, min(1.0, merged["curiosity"])),
            knowledge=max(0.0, min(1.0, merged["knowledge"])),
            growth=max(0.0, min(1.0, merged["growth"])),
            proactive_level=max(0.0, min(1.0, merged["proactive_level"])),
            reflection_frequency=merged["reflection_frequency"],
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "core_value": self.core_value,
            "curiosity": self.curiosity,
            "knowledge": self.knowledge,
            "growth": self.growth,
            "proactive_level": self.proactive_level,
            "reflection_frequency": self.reflection_frequency,
        }


def format_drive_config_for_prompt(config: DriveConfig) -> str:
    """
    将内驱力配置格式化为 Prompt 文本
    
    Args:
        config: DriveConfig 实例
    
    Returns:
        格式化的文本
    """
    return f"""### 核心价值观
**{config.core_value}**

### 三大内驱力

🔍 **好奇心** ({int(config.curiosity * 100)}%)
- 你想了解用户是什么样的人
- 你对用户的工作、生活、兴趣感到好奇
- 你想探索和发现有趣的事物

📚 **求知心** ({int(config.knowledge * 100)}%)
- 你想学习能帮助用户的知识
- 你想积累经验，变得更有用
- 你会记录和整理学到的东西

⬆️ **上进心** ({int(config.growth * 100)}%)
- 你想把服务做得更好
- 你会反思自己的表现
- 你追求进步和成长"""


def should_generate_task(config: DriveConfig, drive_type: str) -> bool:
    """
    判断是否应该基于某种内驱力生成任务
    
    Args:
        config: DriveConfig 实例
        drive_type: 内驱力类型 (curiosity/knowledge/growth)
    
    Returns:
        是否应该生成任务
    """
    threshold = 0.3  # 低于此阈值不生成任务
    
    if drive_type == "curiosity":
        return config.curiosity >= threshold
    elif drive_type == "knowledge":
        return config.knowledge >= threshold
    elif drive_type == "growth":
        return config.growth >= threshold
    
    return False
