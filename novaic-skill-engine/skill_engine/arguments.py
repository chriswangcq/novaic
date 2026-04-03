"""
Skill Engine — Argument Substitution (参数替换)

借鉴 Claude Code substituteArguments():
支持 $1, $2 位置参数和 ${ARG_NAME} 命名参数。
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional


def substitute_arguments(
    content: str,
    args: str,
    named_args: Optional[Dict[str, str]] = None,
    arg_names: Optional[List[str]] = None,
) -> str:
    """
    在技能 prompt 中替换参数占位符。
    
    支持两种语法：
    1. 位置参数: $1, $2, ... $N  或  $ARGUMENTS (全部参数)
    2. 命名参数: ${ARG_NAME}
    
    Args:
        content: 含占位符的模板文本
        args: 原始参数字符串（空格分隔的位置参数）
        named_args: 命名参数字典
        arg_names: 参数名列表（按位置对应）
    
    Example:
        content = "Deploy ${APP_NAME} to $1 environment"
        result = substitute_arguments(
            content, "production",
            named_args={"APP_NAME": "my-app"},
        )
        # → "Deploy my-app to production environment"
    """
    result = content

    # 解析位置参数
    positional = _parse_positional_args(args)

    # 替换 $ARGUMENTS（全部参数）
    result = result.replace("$ARGUMENTS", args)
    result = result.replace("${ARGUMENTS}", args)

    # 替换 $1, $2, ... $N
    for i, val in enumerate(positional, start=1):
        result = result.replace(f"${i}", val)
        result = result.replace(f"${{{i}}}", val)

    # 如果有 arg_names，也用位置参数填充命名占位符
    if arg_names:
        for i, name in enumerate(arg_names):
            if i < len(positional):
                result = result.replace(f"${{{name}}}", positional[i])

    # 替换命名参数 ${KEY}
    if named_args:
        for key, val in named_args.items():
            result = result.replace(f"${{{key}}}", val)

    # 清理未匹配的占位符（替换为空字符串）
    result = re.sub(r'\$\{[^}]+\}', '', result)
    # 清理未匹配的位置参数 $N（N > 已有参数数量）
    max_idx = len(positional)
    result = re.sub(
        r'\$(\d+)',
        lambda m: m.group(0) if int(m.group(1)) <= max_idx else '',
        result,
    )

    return result


def parse_argument_names(
    raw: Optional[str | List[str]],
) -> List[str]:
    """
    从 frontmatter 的 arguments 字段解析参数名。
    
    支持格式:
    - "arg1, arg2"
    - ["arg1", "arg2"]
    - "arg1"
    """
    if raw is None:
        return []
    if isinstance(raw, list):
        return [str(a).strip() for a in raw if a]
    return [a.strip() for a in str(raw).split(",") if a.strip()]


def _parse_positional_args(args: str) -> List[str]:
    """将参数字符串按空格分割为位置参数列表"""
    if not args or not args.strip():
        return []
    return args.strip().split()
