"""
LLM Business - LLM 调用

业务逻辑：
- 调用 LLM (预处理 + 调用 + 后处理)
- 生成摘要
"""

import json
from dataclasses import dataclass
from typing import Dict, Any, List, Optional

from ..client import GatewayInternalClient

# 使用模块化工具
from ..utils import sanitize_context, process_multimodal_messages
from ..utils.result import clean_context_for_summary


@dataclass
class LLMCallResult:
    """LLM 调用结果"""
    success: bool
    response: Optional[Dict[str, Any]] = None
    error: str = ""


@dataclass
class SummaryResult:
    """摘要生成结果"""
    success: bool
    summary: str = ""
    cached: bool = False
    error: str = ""


class LLMBusiness:
    """
    LLM 业务逻辑
    
    功能：
    - Context 预处理（清理、多模态）
    - LLM 调用
    - 摘要生成
    
    Example:
        >>> from task_queue.business import LLMBusiness
        >>> llm_biz = LLMBusiness(db, llm_client)
        >>> result = llm_biz.call(messages, model="gpt-4o")
        >>> if result.success:
        ...     print(result.response)
    """
    
    def __init__(self, gateway_url: str, llm_client=None, client: Optional[GatewayInternalClient] = None):
        """
        Args:
            gateway_url: Gateway URL
            llm_client: LLM 客户端
            client: 可复用的 GatewayInternalClient
        """
        self.llm_client = llm_client
        self.client = client or GatewayInternalClient(gateway_url)
    
    def call(
        self,
        messages: List[Dict[str, Any]],
        *,
        model: str = "gpt-4o",
        tools: Optional[List[Dict[str, Any]]] = None,
        provider: str = "openai",
    ) -> LLMCallResult:
        """
        调用 LLM
        
        自动进行：
        1. Context 清理（确保 tool_results 紧跟 assistant+tool_calls）
        2. 多模态处理（提取图片）
        
        Args:
            messages: 对话消息
            model: 模型名称
            tools: 工具定义
            provider: 提供商 (openai/anthropic)
            
        Returns:
            LLMCallResult
        """
        if not self.llm_client:
            return LLMCallResult(success=False, error="LLM client not configured")
        
        try:
            # 1. Context 清理
            sanitized = sanitize_context(messages)
            
            # 2. 多模态处理
            processed = process_multimodal_messages(sanitized, provider)
            
            # 3. 调用 LLM
            response = self.llm_client.chat(
                messages=processed,
                model=model,
                tools=tools,
            )
            
            return LLMCallResult(success=True, response=response)
            
        except Exception as e:
            return LLMCallResult(success=False, error=str(e))
    
    def generate_summary(
        self,
        runtime_id: str,
        *,
        model: str = "kimi-k2.5",  # 使用 Kimi 作为默认
        system_prompt: Optional[str] = None,
    ) -> SummaryResult:
        """
        生成对话摘要
        
        自动从 DB 读取 context，幂等（已有摘要直接返回）。
        
        Args:
            runtime_id: Runtime ID
            model: 模型名称
            system_prompt: 系统提示词
            
        Returns:
            SummaryResult
        """
        if system_prompt is None:
            system_prompt = "Please summarize this conversation concisely, highlighting key points and decisions made."
        
        # 1. 获取 runtime 信息
        runtime = self.client.get_runtime(runtime_id)
        if not runtime:
            return SummaryResult(success=False, error="Runtime not found")

        # 幂等检查
        if runtime.get("summary"):
            return SummaryResult(success=True, summary=runtime.get("summary", ""), cached=True)

        context = runtime.get("context") or []
        
        if not context:
            return SummaryResult(success=True, summary="", error="No conversation to summarize")
        
        if not self.llm_client:
            return SummaryResult(success=False, error="LLM client not configured")
        
        # 2. 清理 context
        clean_context = clean_context_for_summary(context)
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Here is the conversation:\n\n{json.dumps(clean_context, indent=2)}"},
        ]
        
        try:
            # 3. 调用 LLM
            response = self.llm_client.chat(
                messages=messages,
                model=model,
            )
            
            summary = response.get("choices", [{}])[0].get("message", {}).get("content", "")
            
            # 4. 保存摘要
            self.client.update_runtime(runtime_id, {"summary": summary})
            
            return SummaryResult(success=True, summary=summary)
            
        except Exception as e:
            return SummaryResult(success=False, error=str(e))
    
    def extract_tool_calls(self, response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        从 LLM 响应中提取 tool_calls
        
        Args:
            response: LLM 响应
            
        Returns:
            tool_calls 列表
        """
        message = response.get("choices", [{}])[0].get("message", {})
        return message.get("tool_calls", [])
    
    def extract_content(self, response: Dict[str, Any]) -> str:
        """
        从 LLM 响应中提取文本内容
        
        Args:
            response: LLM 响应
            
        Returns:
            文本内容
        """
        message = response.get("choices", [{}])[0].get("message", {})
        return message.get("content", "")
    
    def extract_reasoning(self, response: Dict[str, Any]) -> str:
        """
        从 LLM 响应中提取推理内容
        
        支持 reasoning_content（如 kimi-k2.5）
        
        Args:
            response: LLM 响应
            
        Returns:
            推理内容
        """
        message = response.get("choices", [{}])[0].get("message", {})
        return message.get("reasoning_content") or message.get("content", "")
