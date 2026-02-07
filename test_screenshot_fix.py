#!/usr/bin/env python3
"""
测试 VM 截图 API 修复
验证三层 API 的返回格式
"""
import sys
import asyncio
import httpx
sys.path.insert(0, "/Users/wangchaoqun/novaic/novaic-backend")

from gateway.clients.vmcontrol import VmControlClient
from gateway.clients.vmuse_adapter import VmuseAdapter


async def test_vmcontrol_direct():
    """测试 1: vmcontrol 直接 API"""
    print("=" * 60)
    print("测试 1: vmcontrol 直接 API (http://localhost:8080)")
    print("=" * 60)
    
    try:
        client = VmControlClient()
        vms = await client.list_vms()
        if not vms:
            print("❌ 没有运行中的 VM")
            return None
        
        vm_id = vms[0]["id"]
        print(f"✓ 找到 VM: {vm_id}")
        
        result = await client.screenshot(vm_id)
        print(f"✓ 返回类型: {type(result)}")
        
        if isinstance(result, dict):
            print(f"✓ 返回 JSON 格式")
            print(f"  - Has 'data': {'data' in result}")
            print(f"  - Has 'format': {'format' in result}")
            print(f"  - Format: {result.get('format')}")
            if 'data' in result:
                print(f"  - Data length: {len(result.get('data', ''))}")
        else:
            print(f"❌ 返回类型错误: {type(result)}")
        
        await client.close()
        return vm_id
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_gateway_proxy(vm_id: str):
    """测试 2: Gateway 代理 API"""
    print("\n" + "=" * 60)
    print("测试 2: Gateway 代理 API (http://localhost:19999/api/vmcontrol)")
    print("=" * 60)
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(f"http://localhost:19999/api/vmcontrol/vms/{vm_id}/screenshot")
            response.raise_for_status()
            result = response.json()
            
            print(f"✓ 返回 JSON 格式")
            print(f"  - Has 'content': {'content' in result}")
            
            if 'content' in result and result['content']:
                content = result['content'][0]
                print(f"  - Content type: {content.get('type')}")
                print(f"  - Has 'data': {'data' in content}")
                print(f"  - MimeType: {content.get('mimeType')}")
                if 'data' in content:
                    print(f"  - Data length: {len(content.get('data', ''))}")
            else:
                print(f"❌ 缺少 'content' 字段或为空")
                print(f"  - 实际返回: {list(result.keys())}")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


async def test_vmuse_adapter(vm_id: str):
    """测试 3: vmuse_adapter 适配层"""
    print("\n" + "=" * 60)
    print("测试 3: vmuse_adapter 适配层")
    print("=" * 60)
    
    try:
        adapter = VmuseAdapter()
        result = await adapter.call_tool("screenshot", {}, vm_id=vm_id)
        
        print(f"✓ 调用成功")
        print(f"  - Success: {result.get('success')}")
        
        if result.get('success'):
            result_data = result.get('result', {})
            print(f"  - Has 'image_data': {'image_data' in result_data}")
            print(f"  - Format: {result_data.get('format')}")
            print(f"  - Width: {result_data.get('width')}")
            print(f"  - Height: {result_data.get('height')}")
            if 'image_data' in result_data:
                print(f"  - Data length: {len(result_data.get('image_data', ''))}")
        else:
            print(f"❌ 返回 success=False")
            print(f"  - Error: {result.get('error')}")
        
        await adapter.close()
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


async def main():
    print("VM 截图 API 修复验证")
    print("=" * 60)
    print()
    
    # 测试 1: vmcontrol 直接 API
    vm_id = await test_vmcontrol_direct()
    
    if vm_id:
        # 测试 2: Gateway 代理 API
        await test_gateway_proxy(vm_id)
        
        # 测试 3: vmuse_adapter
        await test_vmuse_adapter(vm_id)
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
