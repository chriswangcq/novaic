"""
MicroAgentEngine - Executes micro agent evaluations

Manages micro agent execution, including rule evaluation and LLM calls.
"""

import asyncio
import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

from .agent import MicroAgent, EvalMode, EvalResult

logger = logging.getLogger(__name__)


class MicroAgentEngine:
    """
    Engine for executing micro agent evaluations.
    
    Responsibilities:
    - Manage registered micro agents
    - Execute evaluations (rules and/or LLM)
    - Cache and optimize LLM calls
    - Track evaluation statistics
    """
    
    def __init__(
        self,
        llm_client=None,
        llm_model: str = "gpt-4o-mini",
        storage_dir: str = "storage/micro_agents",
    ):
        """
        Initialize the engine.
        
        Args:
            llm_client: LLM client for LLM-based evaluations
            llm_model: Model to use for LLM evaluations
            storage_dir: Directory for micro agent persistence
        """
        self.llm_client = llm_client
        self.llm_model = llm_model
        self.storage_dir = storage_dir
        
        # Registered micro agents
        self._agents: Dict[str, MicroAgent] = {}
        
        # Statistics
        self._stats = {
            "evaluations": 0,
            "rule_evaluations": 0,
            "llm_evaluations": 0,
            "wakes_triggered": 0,
        }
    
    def register_agent(self, agent: MicroAgent) -> str:
        """
        Register a micro agent.
        
        Args:
            agent: MicroAgent to register
        
        Returns:
            Agent ID
        """
        self._agents[agent.id] = agent
        logger.info(f"[MicroEngine] Registered agent: {agent.name} ({agent.id})")
        return agent.id
    
    def unregister_agent(self, agent_id: str) -> bool:
        """Unregister a micro agent."""
        if agent_id in self._agents:
            del self._agents[agent_id]
            return True
        return False
    
    def get_agent(self, agent_id: str) -> Optional[MicroAgent]:
        """Get a micro agent by ID."""
        return self._agents.get(agent_id)
    
    def list_agents(self) -> List[Dict[str, Any]]:
        """List all registered micro agents."""
        return [agent.to_dict() for agent in self._agents.values()]
    
    async def evaluate(
        self,
        agent_id: str,
        event_text: str,
        event_data: Optional[Dict[str, Any]] = None,
    ) -> EvalResult:
        """
        Evaluate an event using a specific micro agent.
        
        Args:
            agent_id: ID of the micro agent to use
            event_text: Text content to evaluate
            event_data: Additional event data
        
        Returns:
            EvalResult with the decision
        """
        agent = self._agents.get(agent_id)
        if not agent:
            return EvalResult(
                should_wake=False,
                confidence=0.0,
                reason=f"Agent not found: {agent_id}",
            )
        
        if not agent.enabled:
            return EvalResult(
                should_wake=False,
                confidence=0.0,
                reason="Agent is disabled",
            )
        
        return await self._evaluate_with_agent(agent, event_text, event_data)
    
    async def evaluate_all(
        self,
        event_text: str,
        event_data: Optional[Dict[str, Any]] = None,
    ) -> EvalResult:
        """
        Evaluate an event using all enabled micro agents.
        
        The first agent to return should_wake=True wins.
        
        Args:
            event_text: Text content to evaluate
            event_data: Additional event data
        
        Returns:
            EvalResult with the aggregated decision
        """
        self._stats["evaluations"] += 1
        start_time = datetime.now()
        
        for agent in self._agents.values():
            if not agent.enabled:
                continue
            
            result = await self._evaluate_with_agent(agent, event_text, event_data)
            
            if result.should_wake and result.confidence >= agent.confidence_threshold:
                result.duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
                self._stats["wakes_triggered"] += 1
                return result
        
        # No agent triggered wake
        return EvalResult(
            should_wake=False,
            confidence=1.0,
            reason="No micro agent triggered wake",
            duration_ms=int((datetime.now() - start_time).total_seconds() * 1000),
        )
    
    async def _evaluate_with_agent(
        self,
        agent: MicroAgent,
        event_text: str,
        event_data: Optional[Dict[str, Any]] = None,
    ) -> EvalResult:
        """
        Evaluate using a specific agent.
        
        Args:
            agent: The micro agent to use
            event_text: Text content
            event_data: Additional data
        
        Returns:
            EvalResult
        """
        start_time = datetime.now()
        
        if agent.mode == EvalMode.RULES:
            self._stats["rule_evaluations"] += 1
            result = agent.evaluate_rules(event_text)
            
        elif agent.mode == EvalMode.LLM:
            self._stats["llm_evaluations"] += 1
            result = await self._evaluate_with_llm(agent, event_text, event_data)
            
        else:  # HYBRID
            # First try rules
            self._stats["rule_evaluations"] += 1
            result = agent.evaluate_rules(event_text)
            
            # If no rules matched with high confidence, use LLM
            if not result.matched_rules or result.confidence < agent.confidence_threshold:
                self._stats["llm_evaluations"] += 1
                llm_result = await self._evaluate_with_llm(agent, event_text, event_data)
                
                # Merge results
                if llm_result.confidence > result.confidence:
                    result = llm_result
                    result.matched_rules = []  # Clear since we're using LLM result
        
        result.duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
        return result
    
    async def _evaluate_with_llm(
        self,
        agent: MicroAgent,
        event_text: str,
        event_data: Optional[Dict[str, Any]] = None,
    ) -> EvalResult:
        """
        Evaluate using LLM.
        
        Args:
            agent: The micro agent (for prompt)
            event_text: Text content
            event_data: Additional data
        
        Returns:
            EvalResult from LLM evaluation
        """
        if not self.llm_client:
            return EvalResult(
                should_wake=False,
                confidence=0.0,
                reason="No LLM client configured",
            )
        
        # Build prompt
        event_info = event_text
        if event_data:
            event_info += f"\n\nAdditional data: {json.dumps(event_data, ensure_ascii=False)}"
        
        prompt = agent.llm_prompt.format(event=event_info)
        
        try:
            response = await self.llm_client.chat(
                messages=[
                    {"role": "system", "content": "You are a micro agent that filters events."},
                    {"role": "user", "content": prompt}
                ],
                model=self.llm_model,
                max_tokens=200,
            )
            
            content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
            
            # Parse response
            should_wake, confidence, reason = self._parse_llm_response(content)
            
            return EvalResult(
                should_wake=should_wake,
                confidence=confidence,
                reason=reason,
                llm_response=content,
            )
            
        except Exception as e:
            logger.error(f"[MicroEngine] LLM evaluation failed: {e}")
            return EvalResult(
                should_wake=False,
                confidence=0.0,
                reason=f"LLM evaluation error: {e}",
            )
    
    def _parse_llm_response(self, response: str) -> tuple:
        """
        Parse LLM response to extract decision.
        
        Returns:
            Tuple of (should_wake, confidence, reason)
        """
        response_upper = response.upper()
        
        if "WAKE" in response_upper and "IGNORE" not in response_upper[:20]:
            return True, 0.9, response
        elif "IGNORE" in response_upper:
            return False, 0.9, response
        elif "QUEUE" in response_upper:
            return False, 0.7, response
        else:
            # Uncertain
            return False, 0.5, response
    
    def get_stats(self) -> Dict[str, Any]:
        """Get engine statistics."""
        return {
            **self._stats,
            "registered_agents": len(self._agents),
            "enabled_agents": sum(1 for a in self._agents.values() if a.enabled),
        }
