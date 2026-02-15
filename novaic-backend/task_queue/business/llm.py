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


@dataclass
class HotColdSummaryResult:
    """Hot/Cold Summary 生成结果"""
    success: bool
    hot_summary: str = ""
    cold_summary: str = ""
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
        from ..utils.trs_client import expand_messages_for_summary
        context = expand_messages_for_summary(context)

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
    
    def generate_hot_cold_summary(
        self,
        runtime_id: str,
        *,
        model: str = "kimi-k2.5",
    ) -> HotColdSummaryResult:
        """
        生成 Hot Summary 和 Cold Summary
        
        Hot Summary:
        - 除最后3轮外：LLM 总结成一段话
        - 最后3轮：保留 think + tools + full_result
        
        Cold Summary:
        - 所有轮次：LLM 总结成一段话
        
        Args:
            runtime_id: Runtime ID
            model: 模型名称
            
        Returns:
            HotColdSummaryResult
        """
        from ..utils import (
            prepare_hot_summary_parts,
            prepare_cold_summary_text,
            HOT_SUMMARY_PROMPT,
            COLD_SUMMARY_PROMPT,
        )
        
        # 1. 获取 runtime 信息
        runtime = self.client.get_runtime(runtime_id)
        if not runtime:
            return HotColdSummaryResult(success=False, error="Runtime not found")

        context = runtime.get("context") or []
        from ..utils.trs_client import expand_messages_for_summary
        context = expand_messages_for_summary(context)

        if not context:
            return HotColdSummaryResult(
                success=True, 
                hot_summary="[No context]", 
                cold_summary="[No context]"
            )
        
        if not self.llm_client:
            return HotColdSummaryResult(success=False, error="LLM client not configured")
        
        # 2. 准备 Hot Summary 部分
        earlier_text, recent_text = prepare_hot_summary_parts(context, recent_rounds=3)
        
        hot_summary = ""
        cold_summary = ""
        
        # 3. 生成 Hot Summary
        try:
            if earlier_text:
                # 需要 LLM 总结前面轮次
                hot_prompt = HOT_SUMMARY_PROMPT.format(content=earlier_text)
                hot_messages = [
                    {"role": "user", "content": hot_prompt},
                ]
                
                hot_response = self.llm_client.chat(
                    messages=hot_messages,
                    model=model,
                )
                
                earlier_summary = hot_response.get("choices", [{}])[0].get("message", {}).get("content", "")
                
                # 组合 hot_summary: 前面总结 + 最近完整内容
                hot_summary = f"【历史摘要】\n{earlier_summary}\n\n【最近对话】\n{recent_text}"
            else:
                # 轮次不超过3轮，直接用完整内容
                hot_summary = recent_text
        except Exception as e:
            return HotColdSummaryResult(success=False, error=f"Failed to generate hot summary: {str(e)}")
        
        # 4. 生成 Cold Summary
        try:
            cold_text = prepare_cold_summary_text(context)
            cold_prompt = COLD_SUMMARY_PROMPT.format(content=cold_text)
            cold_messages = [
                {"role": "user", "content": cold_prompt},
            ]
            
            cold_response = self.llm_client.chat(
                messages=cold_messages,
                model=model,
            )
            
            cold_summary = cold_response.get("choices", [{}])[0].get("message", {}).get("content", "")
        except Exception as e:
            return HotColdSummaryResult(success=False, error=f"Failed to generate cold summary: {str(e)}")
        
        # 5. 保存到数据库
        try:
            self.client.set_runtime_hot_cold_summary(runtime_id, hot_summary, cold_summary)
        except Exception as e:
            return HotColdSummaryResult(
                success=False, 
                error=f"Failed to save summaries: {str(e)}",
                hot_summary=hot_summary,
                cold_summary=cold_summary,
            )
        
        return HotColdSummaryResult(
            success=True,
            hot_summary=hot_summary,
            cold_summary=cold_summary,
        )
