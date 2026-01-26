"""
测试 MCP 集成

验证：
1. MCP Server 可以列出工具
2. MCP Client 可以发现工具
3. Agent 可以使用 MCP Client 调用工具
"""

import asyncio
import sys
from core.mcp_client import MCPClient
from core.agent import NBCCAgent
from config import settings


async def test_mcp_server():
    """测试 MCP Server 端点"""
    print("=" * 60)
    print("测试 1: MCP Server 工具列表")
    print("=" * 60)
    
    client = MCPClient()
    await client.register_server("executor", settings.executor_url)
    
    try:
        tools = await client.list_all_tools()
        print(f"✅ 发现 {len(tools)} 个工具")
        for tool in tools[:3]:  # 只显示前3个
            print(f"  - {tool['name']}: {tool['description'][:50]}...")
        return True
    except Exception as e:
        print(f"❌ 失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await client.close()


async def test_mcp_tool_call():
    """测试 MCP 工具调用"""
    print("\n" + "=" * 60)
    print("测试 2: MCP 工具调用")
    print("=" * 60)
    
    client = MCPClient()
    await client.register_server("executor", settings.executor_url)
    
    try:
        result = await client.call_tool(
            "run_command",
            {"command": "echo 'Hello from MCP!'"}
        )
        print(f"✅ 工具调用成功")
        print(f"  结果: {result}")
        return True
    except Exception as e:
        print(f"❌ 失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await client.close()


async def test_agent_mcp_integration():
    """测试 Agent MCP 集成"""
    print("\n" + "=" * 60)
    print("测试 3: Agent MCP 集成")
    print("=" * 60)
    
    # 需要提供 API key 才能测试
    api_key = settings.llm_api_key
    if not api_key:
        print("⚠️  跳过：需要设置 LLM_API_KEY")
        return True
    
    agent = NBCCAgent(
        api_base=settings.llm_api_base,
        api_key=api_key,
        use_mcp=True
    )
    
    try:
        # 初始化 Agent（会加载工具）
        await agent.initialize()
        print(f"✅ Agent 初始化成功")
        print(f"   工具数量: {len(agent.tools)}")
        print(f"   使用 MCP: {agent.use_mcp}")
        
        # 显示前几个工具
        for tool in agent.tools[:3]:
            tool_name = tool.get("function", {}).get("name", "unknown")
            print(f"   - {tool_name}")
        
        return True
    except Exception as e:
        print(f"❌ 失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await agent.close()


async def main():
    """运行所有测试"""
    print("\n🧪 MCP 集成测试\n")
    
    results = []
    
    # 测试 1: MCP Server
    results.append(await test_mcp_server())
    
    # 测试 2: MCP 工具调用
    results.append(await test_mcp_tool_call())
    
    # 测试 3: Agent 集成
    results.append(await test_agent_mcp_integration())
    
    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"通过: {passed}/{total}")
    
    if passed == total:
        print("✅ 所有测试通过！")
        return 0
    else:
        print("❌ 部分测试失败")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

