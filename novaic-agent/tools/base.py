"""
Base Tool Executor
"""

from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseTool(ABC):
    """Base class for all tool executors"""
    
    def __init__(self):
        self._interrupted = False
    
    @abstractmethod
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute the tool with given parameters.
        
        Returns:
            Result dictionary with success status and output
        """
        pass
    
    def interrupt(self) -> None:
        """Interrupt ongoing execution"""
        self._interrupted = True
    
    def reset(self) -> None:
        """Reset interrupt flag"""
        self._interrupted = False
    
    def _format_result(
        self,
        success: bool,
        output: Any = None,
        error: str = None
    ) -> Dict[str, Any]:
        """Format execution result"""
        result = {"success": success}
        
        if output is not None:
            result["output"] = output
        
        if error is not None:
            result["error"] = error
        
        return result

