"""
Self-Drive System Tests - 自驱系统单元测试

测试内容：
1. 用户画像评估模块
2. 内驱力配置模块
3. 任务自生成器
4. Prompt 构建器
"""

import pytest
from typing import Dict, Any


# ========================================
# Profile Assessment Tests
# ========================================

class TestProfileAssessment:
    """测试用户画像评估模块"""
    
    def test_empty_profile_completeness(self):
        """空画像应该返回 0% 完整度"""
        from task_queue.utils.profile_assessment import assess_profile_completeness
        
        result = assess_profile_completeness({})
        
        assert result["completeness"] == 0
        assert len(result["missing"]) == 8  # 8 个维度
        assert len(result["known"]) == 0
        assert "刚开始了解用户" in result["summary"]
    
    def test_partial_profile_completeness(self):
        """部分画像应该返回正确的完整度"""
        from task_queue.utils.profile_assessment import assess_profile_completeness
        
        profile = {
            "preferred_name": "小明",
            "communication_style": "简洁高效",
            "work_domain": "软件开发",
        }
        
        result = assess_profile_completeness(profile)
        
        assert result["completeness"] > 0
        assert result["completeness"] < 100
        assert len(result["known"]) == 3
        assert "preferred_name" in result["known"]
    
    def test_full_profile_completeness(self):
        """完整画像应该返回高完整度"""
        from task_queue.utils.profile_assessment import assess_profile_completeness
        
        profile = {
            "preferred_name": "小明",
            "communication_style": "简洁高效",
            "work_domain": "软件开发",
            "primary_use_case": "工作任务",
            "active_hours": "9-18",
            "interests": "科技",
            "pain_points": "数据整理",
            "tech_level": "专家",
        }
        
        result = assess_profile_completeness(profile)
        
        assert result["completeness"] == 100
        assert len(result["missing"]) == 0
        assert "非常了解" in result["summary"]
    
    def test_learning_suggestions(self):
        """应该按优先级返回学习建议"""
        from task_queue.utils.profile_assessment import (
            assess_profile_completeness,
            get_learning_suggestions,
        )
        
        result = assess_profile_completeness({})
        suggestions = get_learning_suggestions(result["missing"], limit=3)
        
        assert len(suggestions) <= 3
        # 高优先级应该排在前面
        assert suggestions[0]["importance"] == "high"
    
    def test_format_profile_for_prompt(self):
        """格式化画像应该返回可读文本"""
        from task_queue.utils.profile_assessment import format_profile_for_prompt
        
        profile = {"preferred_name": "小明", "work_domain": "软件开发"}
        result = format_profile_for_prompt(profile)
        
        assert "小明" in result
        assert "软件开发" in result
    
    def test_format_empty_profile(self):
        """空画像格式化应该返回提示文本"""
        from task_queue.utils.profile_assessment import format_profile_for_prompt
        
        result = format_profile_for_prompt({})
        
        assert "尚未了解用户" in result


# ========================================
# Drive Config Tests
# ========================================

class TestDriveConfig:
    """测试内驱力配置模块"""
    
    def test_default_config(self):
        """默认配置应该有合理的值"""
        from task_queue.utils.drive_config import DriveConfig, DEFAULT_DRIVE_CONFIG
        
        config = DriveConfig.from_dict({})
        
        assert config.curiosity == DEFAULT_DRIVE_CONFIG["curiosity"]
        assert config.knowledge == DEFAULT_DRIVE_CONFIG["knowledge"]
        assert config.growth == DEFAULT_DRIVE_CONFIG["growth"]
        assert config.core_value == DEFAULT_DRIVE_CONFIG["core_value"]
    
    def test_custom_config(self):
        """自定义配置应该覆盖默认值"""
        from task_queue.utils.drive_config import DriveConfig
        
        config = DriveConfig.from_dict({
            "curiosity": 0.9,
            "knowledge": 0.3,
        })
        
        assert config.curiosity == 0.9
        assert config.knowledge == 0.3
    
    def test_config_bounds(self):
        """配置值应该被限制在 0-1 范围内"""
        from task_queue.utils.drive_config import DriveConfig
        
        config = DriveConfig.from_dict({
            "curiosity": 1.5,  # 超出上限
            "knowledge": -0.5,  # 超出下限
        })
        
        assert config.curiosity == 1.0
        assert config.knowledge == 0.0
    
    def test_should_generate_task(self):
        """应该根据阈值判断是否生成任务"""
        from task_queue.utils.drive_config import DriveConfig, should_generate_task
        
        high_config = DriveConfig.from_dict({"curiosity": 0.8})
        low_config = DriveConfig.from_dict({"curiosity": 0.1})
        
        assert should_generate_task(high_config, "curiosity") == True
        assert should_generate_task(low_config, "curiosity") == False
    
    def test_format_drive_config_for_prompt(self):
        """格式化配置应该返回可读文本"""
        from task_queue.utils.drive_config import DriveConfig, format_drive_config_for_prompt
        
        config = DriveConfig.from_dict({})
        result = format_drive_config_for_prompt(config)
        
        assert "好奇心" in result
        assert "求知心" in result
        assert "上进心" in result


# ========================================
# Task Generator Tests
# ========================================

class TestTaskGenerator:
    """测试任务自生成器"""
    
    def test_generate_tasks_for_empty_profile(self):
        """空画像应该生成了解用户的任务"""
        from task_queue.utils.drive_config import DriveConfig
        from task_queue.utils.task_generator import generate_self_driven_tasks
        
        config = DriveConfig.from_dict({})
        tasks = generate_self_driven_tasks(
            user_profile={},
            drive_config=config,
            max_tasks=5,
        )
        
        assert len(tasks) > 0
        # 应该有好奇心驱动的任务
        assert any(t["source"] == "curiosity" for t in tasks)
    
    def test_generate_tasks_with_work_domain(self):
        """知道工作领域应该生成学习任务"""
        from task_queue.utils.drive_config import DriveConfig
        from task_queue.utils.task_generator import generate_self_driven_tasks
        
        config = DriveConfig.from_dict({"knowledge": 0.8})
        tasks = generate_self_driven_tasks(
            user_profile={"work_domain": "机器学习"},
            drive_config=config,
            max_tasks=5,
        )
        
        # 应该有学习相关的任务
        learning_tasks = [t for t in tasks if t["source"] == "learning"]
        assert len(learning_tasks) > 0
        assert any("机器学习" in t["title"] for t in learning_tasks)
    
    def test_task_deduplication(self):
        """应该去重已存在的任务"""
        from task_queue.utils.drive_config import DriveConfig
        from task_queue.utils.task_generator import generate_self_driven_tasks
        
        config = DriveConfig.from_dict({})
        
        # 第一次生成
        tasks1 = generate_self_driven_tasks(
            user_profile={},
            drive_config=config,
            max_tasks=5,
        )
        
        # 第二次生成，传入已存在的任务
        tasks2 = generate_self_driven_tasks(
            user_profile={},
            drive_config=config,
            existing_tasks=tasks1,
            max_tasks=5,
        )
        
        # 不应该有重复的标题
        titles1 = {t["title"].lower() for t in tasks1}
        titles2 = {t["title"].lower() for t in tasks2}
        assert len(titles1 & titles2) == 0
    
    def test_task_quadrant_assignment(self):
        """任务应该被分配到正确的象限"""
        from task_queue.utils.drive_config import DriveConfig
        from task_queue.utils.task_generator import generate_self_driven_tasks
        
        config = DriveConfig.from_dict({})
        tasks = generate_self_driven_tasks(
            user_profile={},
            drive_config=config,
            max_tasks=5,
        )
        
        for task in tasks:
            assert task["quadrant"] in ["q1", "q2", "q3", "q4"]


# ========================================
# Prompt Builder Tests
# ========================================

class TestPromptBuilder:
    """测试 Prompt 构建器"""
    
    def test_build_cold_start_prompt(self):
        """冷启动 Prompt 应该包含必要元素"""
        from task_queue.utils.self_drive_prompt import build_cold_start_prompt
        
        prompt = build_cold_start_prompt(
            drive_config={},
            user_profile={},
        )
        
        assert "初次见面" in prompt
        assert "好奇心" in prompt
        assert "行为建议" in prompt
    
    def test_build_self_drive_prompt(self):
        """完整 Prompt 应该包含所有部分"""
        from task_queue.utils.self_drive_prompt import build_self_drive_prompt
        
        prompt = build_self_drive_prompt(
            drive_config={"curiosity": 0.7},
            user_profile={"preferred_name": "小明"},
            task_board={
                "q1": {"count": 1, "tasks": [{"title": "测试任务", "status": "pending"}]},
                "q2": {"count": 0, "tasks": []},
                "q3": {"count": 0, "tasks": []},
                "q4": {"count": 0, "tasks": []},
            },
            growth_log=[{"date": "2024-01-01", "content": "学习了新知识", "category": "learning"}],
        )
        
        assert "自驱系统" in prompt
        assert "用户画像" in prompt
        assert "任务看板" in prompt
        assert "成长" in prompt
    
    def test_format_task_board(self):
        """任务看板格式化应该正确显示"""
        from task_queue.utils.self_drive_prompt import format_task_board
        
        task_board = {
            "q1": {"count": 2, "tasks": [
                {"title": "紧急任务1", "status": "in_progress"},
                {"title": "紧急任务2", "status": "pending"},
            ]},
            "q2": {"count": 0, "tasks": []},
            "q3": {"count": 1, "tasks": [{"title": "重要任务", "status": "pending"}]},
            "q4": {"count": 0, "tasks": []},
        }
        
        result = format_task_board(task_board)
        
        assert "Q1" in result
        assert "紧急任务1" in result
        assert "重要任务" in result
        assert "⏳" in result  # in_progress 图标


# ========================================
# Integration Tests
# ========================================

class TestIntegration:
    """集成测试"""
    
    def test_full_flow_cold_start(self):
        """测试完整的冷启动流程"""
        from task_queue.utils.profile_assessment import assess_profile_completeness
        from task_queue.utils.drive_config import DriveConfig
        from task_queue.utils.task_generator import generate_self_driven_tasks
        from task_queue.utils.self_drive_prompt import build_cold_start_prompt
        
        # 1. 评估空画像
        assessment = assess_profile_completeness({})
        assert assessment["completeness"] < 30
        
        # 2. 生成任务
        config = DriveConfig.from_dict({})
        tasks = generate_self_driven_tasks({}, config)
        assert len(tasks) > 0
        
        # 3. 构建 Prompt
        prompt = build_cold_start_prompt({}, {})
        assert len(prompt) > 100
    
    def test_full_flow_normal(self):
        """测试完整的正常流程"""
        from task_queue.utils.profile_assessment import assess_profile_completeness
        from task_queue.utils.drive_config import DriveConfig
        from task_queue.utils.task_generator import generate_self_driven_tasks
        from task_queue.utils.self_drive_prompt import build_self_drive_prompt
        
        profile = {
            "preferred_name": "小明",
            "communication_style": "简洁",
            "work_domain": "开发",
            "primary_use_case": "工作",
        }
        
        # 1. 评估画像
        assessment = assess_profile_completeness(profile)
        assert assessment["completeness"] > 30
        
        # 2. 生成任务
        config = DriveConfig.from_dict({})
        tasks = generate_self_driven_tasks(profile, config)
        
        # 3. 构建 Prompt
        prompt = build_self_drive_prompt(
            drive_config={},
            user_profile=profile,
            task_board={"q1": {"count": 0, "tasks": []}, "q2": {"count": 0, "tasks": []}, "q3": {"count": 0, "tasks": []}, "q4": {"count": 0, "tasks": []}},
            growth_log=[],
        )
        assert "小明" in prompt or "用户画像" in prompt


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
