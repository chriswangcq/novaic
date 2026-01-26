"""
NovAIC - The AI Computer Engine

NovAIC = Nov(a) + AIC (AI Computer)
PC 是给人用的电脑，AIC 是给 AI 用的电脑。

提供 44+ MCP 工具，让 AI 能够：
- 控制桌面（截图、鼠标、键盘）
- 自动化浏览器
- 执行命令和代码
- 管理文件系统
- 操作窗口
- 持久化记忆
- 感知环境
"""

__version__ = "0.1.0"

from .main import app, MCP_TOOLS, execute_tool

__all__ = ["app", "MCP_TOOLS", "execute_tool", "__version__"]

