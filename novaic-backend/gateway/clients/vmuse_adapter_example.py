"""
VMUSE 适配器使用示例

演示如何使用 VmuseAdapter 与 vmcontrol 服务交互
"""

import asyncio
import logging
from typing import Dict, Any

from gateway.clients.vmuse_adapter import get_vmuse_adapter

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def example_browser_operations(vm_id: str = "1"):
    """浏览器操作示例"""
    logger.info("=== Browser Operations Example ===")
    
    adapter = get_vmuse_adapter()
    
    # 1. 导航到网页
    logger.info("1. Navigating to example.com...")
    result = await adapter.call_tool("browser_navigate", {
        "url": "https://example.com"
    }, vm_id=vm_id)
    
    if result["success"]:
        logger.info("✓ Navigation successful")
    else:
        logger.error(f"✗ Navigation failed: {result.get('error')}")
        return
    
    # 2. 点击按钮
    logger.info("2. Clicking button...")
    result = await adapter.call_tool("browser_click", {
        "selector": "#submit-button"
    }, vm_id=vm_id)
    
    if result["success"]:
        logger.info("✓ Click successful")
    else:
        logger.error(f"✗ Click failed: {result.get('error')}")
    
    # 3. 输入文本
    logger.info("3. Typing text...")
    result = await adapter.call_tool("browser_type", {
        "selector": "#username",
        "text": "testuser"
    }, vm_id=vm_id)
    
    if result["success"]:
        logger.info("✓ Type successful")
    else:
        logger.error(f"✗ Type failed: {result.get('error')}")


async def example_file_operations(vm_id: str = "1"):
    """文件操作示例"""
    logger.info("\n=== File Operations Example ===")
    
    adapter = get_vmuse_adapter()
    
    # 1. 写入文件
    logger.info("1. Writing file...")
    test_content = "Hello from VMUSE Adapter!\nLine 2\nLine 3"
    result = await adapter.call_tool("file_write", {
        "path": "/tmp/adapter_test.txt",
        "content": test_content
    }, vm_id=vm_id)
    
    if result["success"]:
        logger.info(f"✓ File written: {result['result']['bytes_written']} bytes")
    else:
        logger.error(f"✗ Write failed: {result.get('error')}")
        return
    
    # 2. 读取文件
    logger.info("2. Reading file...")
    result = await adapter.call_tool("file_read", {
        "path": "/tmp/adapter_test.txt"
    }, vm_id=vm_id)
    
    if result["success"]:
        content = result["result"]["content"]
        size = result["result"]["size"]
        logger.info(f"✓ File read: {size} bytes")
        logger.info(f"Content preview: {content[:50]}...")
    else:
        logger.error(f"✗ Read failed: {result.get('error')}")


async def example_shell_operations(vm_id: str = "1"):
    """Shell 操作示例"""
    logger.info("\n=== Shell Operations Example ===")
    
    adapter = get_vmuse_adapter()
    
    # 1. 执行简单命令
    logger.info("1. Running 'uname -a'...")
    result = await adapter.call_tool("shell_exec", {
        "command": "uname -a"
    }, vm_id=vm_id)
    
    if result["success"]:
        logger.info(f"✓ Command successful")
        logger.info(f"Output: {result['result']['stdout']}")
    else:
        logger.error(f"✗ Command failed: {result.get('error')}")
    
    # 2. 执行带管道的命令
    logger.info("2. Running 'ls -la | head -5'...")
    result = await adapter.call_tool("shell_exec", {
        "command": "ls -la /tmp | head -5"
    }, vm_id=vm_id)
    
    if result["success"]:
        logger.info(f"✓ Command successful")
        logger.info(f"Output:\n{result['result']['stdout']}")
    else:
        logger.error(f"✗ Command failed: {result.get('error')}")
    
    # 3. 执行失败的命令（测试错误处理）
    logger.info("3. Running invalid command (testing error handling)...")
    result = await adapter.call_tool("shell_exec", {
        "command": "invalid_command_xyz"
    }, vm_id=vm_id)
    
    if not result["success"]:
        logger.info(f"✓ Error handled correctly")
        logger.info(f"Exit code: {result['result']['exit_code']}")
        logger.info(f"Stderr: {result['result']['stderr']}")
    else:
        logger.warning("Command should have failed but succeeded")


async def example_screenshot(vm_id: str = "1"):
    """截图示例"""
    logger.info("\n=== Screenshot Example ===")
    
    adapter = get_vmuse_adapter()
    
    logger.info("Taking screenshot...")
    result = await adapter.call_tool("screenshot", {}, vm_id=vm_id)
    
    if result["success"]:
        width = result["result"]["width"]
        height = result["result"]["height"]
        format_type = result["result"]["format"]
        logger.info(f"✓ Screenshot captured: {width}x{height} ({format_type})")
        
        # 可选：保存到文件
        # import base64
        # image_data = result["result"]["image_data"]
        # with open("/tmp/screenshot.png", "wb") as f:
        #     f.write(base64.b64decode(image_data))
        # logger.info("Screenshot saved to /tmp/screenshot.png")
    else:
        logger.error(f"✗ Screenshot failed: {result.get('error')}")


async def example_error_handling():
    """错误处理示例"""
    logger.info("\n=== Error Handling Example ===")
    
    adapter = get_vmuse_adapter()
    
    # 1. 不支持的工具
    logger.info("1. Testing unsupported tool...")
    result = await adapter.call_tool("unsupported_tool", {})
    assert not result["success"]
    logger.info(f"✓ Unsupported tool error: {result['error']}")
    
    # 2. 缺少必需参数
    logger.info("2. Testing missing required parameter...")
    result = await adapter.call_tool("browser_navigate", {})
    assert not result["success"]
    logger.info(f"✓ Missing parameter error: {result['error']}")
    
    # 3. 无效的 VM ID（假设）
    logger.info("3. Testing invalid VM ID...")
    result = await adapter.call_tool("screenshot", {}, vm_id="invalid-vm-id")
    # 这个测试取决于 vmcontrol 如何处理无效 VM ID
    if not result["success"]:
        logger.info(f"✓ Invalid VM ID error: {result['error']}")
    else:
        logger.warning("Invalid VM ID did not produce an error")


async def example_tool_list():
    """工具列表示例"""
    logger.info("\n=== Tool List Example ===")
    
    adapter = get_vmuse_adapter()
    tools = adapter.list_tools()
    
    logger.info(f"Available tools: {len(tools)}")
    for tool_name, tool_def in tools.items():
        logger.info(f"\n  {tool_name}:")
        logger.info(f"    Description: {tool_def['description']}")
        logger.info(f"    Parameters: {list(tool_def['parameters'].keys())}")


async def example_concurrent_operations(vm_id: str = "1"):
    """并发操作示例"""
    logger.info("\n=== Concurrent Operations Example ===")
    
    adapter = get_vmuse_adapter()
    
    # 同时执行多个操作
    logger.info("Running multiple operations concurrently...")
    
    tasks = [
        adapter.call_tool("shell_exec", {"command": "echo 'Task 1'"}, vm_id=vm_id),
        adapter.call_tool("shell_exec", {"command": "echo 'Task 2'"}, vm_id=vm_id),
        adapter.call_tool("shell_exec", {"command": "echo 'Task 3'"}, vm_id=vm_id),
    ]
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    for i, result in enumerate(results, 1):
        if isinstance(result, Exception):
            logger.error(f"✗ Task {i} failed with exception: {result}")
        elif result["success"]:
            logger.info(f"✓ Task {i} completed: {result['result']['stdout'].strip()}")
        else:
            logger.error(f"✗ Task {i} failed: {result.get('error')}")


async def run_all_examples(vm_id: str = "1"):
    """运行所有示例"""
    logger.info("=" * 60)
    logger.info("VMUSE Adapter Examples")
    logger.info(f"VM ID: {vm_id}")
    logger.info("=" * 60)
    
    try:
        # 工具列表
        await example_tool_list()
        
        # 文件操作（较安全，先测试）
        await example_file_operations(vm_id)
        
        # Shell 操作
        await example_shell_operations(vm_id)
        
        # 截图
        await example_screenshot(vm_id)
        
        # 浏览器操作（需要浏览器环境）
        # await example_browser_operations(vm_id)
        
        # 错误处理
        await example_error_handling()
        
        # 并发操作
        await example_concurrent_operations(vm_id)
        
    except Exception as e:
        logger.error(f"Example failed with exception: {e}", exc_info=True)
    
    logger.info("\n" + "=" * 60)
    logger.info("All examples completed!")
    logger.info("=" * 60)


async def example_compatibility_check():
    """兼容性检查示例"""
    logger.info("\n=== Compatibility Check ===")
    
    from common.config import ServiceConfig
    
    logger.info(f"USE_LEGACY_VMUSE: {ServiceConfig.USE_LEGACY_VMUSE}")
    logger.info(f"VMCONTROL_URL: {ServiceConfig.VMCONTROL_URL}")
    
    if ServiceConfig.USE_LEGACY_VMUSE:
        logger.warning("⚠ Running in legacy VMUSE mode")
    else:
        logger.info("✓ Running with new vmcontrol adapter")
    
    # 测试健康检查
    from gateway.clients.vmcontrol import get_vmcontrol_client
    
    try:
        client = get_vmcontrol_client()
        healthy = await client.health_check()
        if healthy:
            logger.info("✓ vmcontrol service is healthy")
        else:
            logger.warning("⚠ vmcontrol service health check failed")
    except Exception as e:
        logger.error(f"✗ vmcontrol service connection failed: {e}")


# ==================== Main ====================

async def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="VMUSE Adapter Examples")
    parser.add_argument("--vm-id", default="1", help="VM ID to use (default: 1)")
    parser.add_argument("--example", choices=[
        "all", "browser", "file", "shell", "screenshot",
        "error", "tools", "concurrent", "compat"
    ], default="all", help="Which example to run")
    
    args = parser.parse_args()
    
    try:
        # 兼容性检查
        await example_compatibility_check()
        
        # 运行指定示例
        if args.example == "all":
            await run_all_examples(args.vm_id)
        elif args.example == "browser":
            await example_browser_operations(args.vm_id)
        elif args.example == "file":
            await example_file_operations(args.vm_id)
        elif args.example == "shell":
            await example_shell_operations(args.vm_id)
        elif args.example == "screenshot":
            await example_screenshot(args.vm_id)
        elif args.example == "error":
            await example_error_handling()
        elif args.example == "tools":
            await example_tool_list()
        elif args.example == "concurrent":
            await example_concurrent_operations(args.vm_id)
        elif args.example == "compat":
            pass  # Already ran compatibility check above
    
    finally:
        # 清理
        from gateway.clients.vmuse_adapter import close_vmuse_adapter
        await close_vmuse_adapter()
        logger.info("\nAdapter closed")


if __name__ == "__main__":
    asyncio.run(main())
