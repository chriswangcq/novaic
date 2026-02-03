"""
RuntimeCollector

Processes runtime creation result and triggers think.

Post-logic:
- Verify runtime was created successfully
- Trigger think_launcher with new runtime
"""

from typing import Dict, Any, List, TYPE_CHECKING

from ..collector_worker import BaseCollector, CollectorWorker

if TYPE_CHECKING:
    from ..gateway_client import GatewayClient


@CollectorWorker.register("runtime_collector")
class RuntimeCollector(BaseCollector):
    """
    Collector that verifies runtime creation and triggers think.
    """
    
    async def collect_and_trigger(
        self,
        task: dict,
        runtime_id: str,
        stage_id: str,
        agent_id: str,
        args: dict,
        async_results: List[dict],
    ) -> dict:
        """
        Verify runtime and trigger think.
        """
        # Get REQUIRED fields from args
        actual_agent_id = args.get("agent_id")
        new_runtime_id = args.get("new_runtime_id")
        mcp_url = args.get("mcp_url")
        subagent_id = args.get("subagent_id")
        
        # Strict validation
        if not actual_agent_id or actual_agent_id == "system":
            raise ValueError(f"runtime_collector requires real agent_id in args, got: {actual_agent_id}")
        
        if not new_runtime_id:
            print(f"[RuntimeCollector] No runtime created, ending")
            return {
                "should_continue": False,
                "next_stage_type": None,
                "next_args": {},
            }
        
        if not mcp_url:
            print(f"[RuntimeCollector] Runtime {new_runtime_id} has no MCP, failing")
            # Mark runtime as failed via Gateway API
            await self.client.update_runtime(
                new_runtime_id,
                status="failed",
                error="MCP creation failed",
            )
            
            # Failed: awaking → sleeping
            if subagent_id:
                await self.client.set_subagent_sleeping(actual_agent_id, subagent_id)
                print(f"[RuntimeCollector] SubAgent {subagent_id}: awaking → sleeping (failed)")
            
            # Trigger summarize to record failure context
            return {
                "should_continue": True,
                "next_stage_type": "summarize_launcher",
                "next_args": {
                    "agent_id": actual_agent_id,
                    "runtime_id": new_runtime_id,
                    "subagent_id": subagent_id,
                    "simple_summary": "Runtime failed: MCP creation failed",
                    "is_failure": True,
                },
            }
        
        # Runtime ready: awaking → awake
        if subagent_id:
            await self.client.set_subagent_awake(actual_agent_id, subagent_id)
            print(f"[RuntimeCollector] SubAgent {subagent_id}: awaking → awake")
        
        print(f"[RuntimeCollector] Runtime {new_runtime_id} ready, triggering think")
        
        return {
            "should_continue": True,
            "next_stage_type": "think_launcher",
            "next_args": {
                "agent_id": actual_agent_id,  # REQUIRED for next tasks
                "runtime_id": new_runtime_id,
            },
        }
