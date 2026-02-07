#!/usr/bin/env python3
"""
测试 VM 工具发现集成

验证以下流程：
1. vmuse_adapter.list_tools_mcp_format() 返回正确格式
2. Gateway API /internal/runtimes/{runtime_id}/vm-tools 正常工作
3. Tools Server 能够从 Gateway 获取 VM 工具
"""

import asyncio
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "novaic-backend"))


async def test_vmuse_adapter():
    """测试 1: vmuse_adapter 返回 MCP 格式工具列表"""
    print("\n" + "="*60)
    print("测试 1: vmuse_adapter.list_tools_mcp_format()")
    print("="*60)
    
    from gateway.clients.vmuse_adapter import VmuseAdapter
    
    adapter = VmuseAdapter()
    tools = adapter.list_tools_mcp_format()
    
    print(f"✓ 返回 {len(tools)} 个工具")
    
    # 验证格式
    for tool in tools:
        assert "name" in tool, f"工具缺少 name 字段: {tool}"
        assert "description" in tool, f"工具缺少 description 字段: {tool}"
        assert "inputSchema" in tool, f"工具缺少 inputSchema 字段: {tool}"
        print(f"  - {tool['name']}: {tool['description']}")
    
    print("\n✅ vmuse_adapter 测试通过")
    return True


async def test_gateway_api():
    """测试 2: Gateway API 端点"""
    print("\n" + "="*60)
    print("测试 2: Gateway API /internal/runtimes/{runtime_id}/vm-tools")
    print("="*60)
    
    import httpx
    from common.config import ServiceConfig
    
    gateway_url = ServiceConfig.GATEWAY_URL
    
    # 这里需要一个真实的 runtime_id 进行测试
    # 如果没有，我们只验证 API 端点是否定义
    print(f"Gateway URL: {gateway_url}")
    print("注意: 需要真实的 runtime_id 才能完整测试")
    
    # 尝试调用 API（可能会失败，因为没有真实 runtime）
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{gateway_url}/internal/runtimes/test-runtime-id/vm-tools",
                timeout=5.0
            )
            print(f"状态码: {response.status_code}")
            
            if response.status_code == 404:
                print("✓ API 端点存在（返回 404 是因为 runtime 不存在）")
                return True
            elif response.status_code == 200:
                data = response.json()
                print(f"✓ API 返回数据: {data}")
                return True
            else:
                print(f"⚠ 未预期的状态码: {response.status_code}")
                return False
    except Exception as e:
        print(f"⚠ API 调用失败: {e}")
        print("这可能是因为 Gateway 服务未运行")
        return False


def test_code_structure():
    """测试 3: 验证代码结构和 import"""
    print("\n" + "="*60)
    print("测试 3: 验证代码结构")
    print("="*60)
    
    # 验证 internal.py 中的新端点
    print("\n检查 gateway/api/internal.py...")
    with open("novaic-backend/gateway/api/internal.py", "r") as f:
        content = f.read()
        assert "get_runtime_vm_tools" in content, "缺少 get_runtime_vm_tools 函数"
        assert "/runtimes/{runtime_id}/vm-tools" in content, "缺少 VM 工具 API 路由"
        assert "list_tools_mcp_format" in content, "缺少对 list_tools_mcp_format 的调用"
        print("✓ internal.py 包含所需的 API 端点")
    
    # 验证 vmuse_adapter.py 中的新方法
    print("\n检查 gateway/clients/vmuse_adapter.py...")
    with open("novaic-backend/gateway/clients/vmuse_adapter.py", "r") as f:
        content = f.read()
        assert "list_tools_mcp_format" in content, "缺少 list_tools_mcp_format 方法"
        assert "inputSchema" in content, "缺少 MCP 格式的 inputSchema"
        print("✓ vmuse_adapter.py 包含 list_tools_mcp_format 方法")
    
    # 验证 runtime_manager.py 中的集成
    print("\n检查 tools_server/runtime_manager.py...")
    with open("novaic-backend/tools_server/runtime_manager.py", "r") as f:
        content = f.read()
        assert "/internal/runtimes/{runtime_id}/vm-tools" in content, "缺少 Gateway VM 工具 API 调用"
        assert "_source" in content and "vm" in content, "缺少 VM 工具来源标记"
        assert "VM tools" in content, "缺少 VM 工具发现日志"
        print("✓ runtime_manager.py 集成了 VM 工具发现逻辑")
    
    print("\n✅ 代码结构验证通过")
    return True


async def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("VM 工具发现集成测试")
    print("="*60)
    
    results = []
    
    # 测试 1: vmuse_adapter
    try:
        result = await test_vmuse_adapter()
        results.append(("vmuse_adapter", result))
    except Exception as e:
        print(f"\n❌ vmuse_adapter 测试失败: {e}")
        results.append(("vmuse_adapter", False))
    
    # 测试 2: Gateway API
    try:
        result = await test_gateway_api()
        results.append(("Gateway API", result))
    except Exception as e:
        print(f"\n❌ Gateway API 测试失败: {e}")
        results.append(("Gateway API", False))
    
    # 测试 3: 代码结构
    try:
        result = test_code_structure()
        results.append(("代码结构", result))
    except Exception as e:
        print(f"\n❌ 代码结构测试失败: {e}")
        results.append(("代码结构", False))
    
    # 总结
    print("\n" + "="*60)
    print("测试总结")
    print("="*60)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{name}: {status}")
    
    all_passed = all(result for _, result in results)
    
    if all_passed:
        print("\n🎉 所有测试通过！")
        return 0
    else:
        print("\n⚠️  部分测试失败，请检查上述输出")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
