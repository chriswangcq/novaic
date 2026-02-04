#!/usr/bin/env python3
"""
测试 HTTP 超时问题

模拟 message.route handler 的执行，看看哪个环节会卡住
"""

import httpx
import time
from datetime import datetime


GATEWAY_URL = "http://127.0.0.1:19999"


def test_basic_requests():
    """测试基本的 HTTP 请求"""
    print("="*80)
    print("测试基本 HTTP 请求")
    print("="*80)
    
    # 测试不同的超时设置
    timeouts = [
        ("无超时", None),
        ("5秒超时", 5.0),
        ("10秒超时", 10.0),
        ("30秒超时", 30.0),
    ]
    
    for name, timeout in timeouts:
        print(f"\n{name}:")
        try:
            start = time.time()
            
            if timeout:
                client = httpx.Client(base_url=GATEWAY_URL, timeout=timeout)
            else:
                client = httpx.Client(base_url=GATEWAY_URL)
            
            # 测试一个简单的请求
            resp = client.get("/health")
            
            elapsed = time.time() - start
            print(f"  ✅ 成功: {resp.status_code}, 耗时 {elapsed:.3f}s")
            client.close()
            
        except httpx.TimeoutException as e:
            elapsed = time.time() - start
            print(f"  ❌ 超时: {e}, 耗时 {elapsed:.3f}s")
        except Exception as e:
            elapsed = time.time() - start
            print(f"  ❌ 错误: {e}, 耗时 {elapsed:.3f}s")


def test_message_route_calls():
    """测试 message.route handler 中的 HTTP 调用"""
    print("\n\n" + "="*80)
    print("测试 message.route 中的 HTTP 调用")
    print("="*80)
    
    # 模拟创建一个测试 agent
    print("\n1. 创建测试 Agent...")
    try:
        client = httpx.Client(base_url=GATEWAY_URL, timeout=10.0, trust_env=False)
        resp = client.get("/api/agents")
        agents = resp.json().get("agents", [])
        
        if agents:
            agent_id = agents[0]["id"]
            subagent_id = f"main-{agent_id[:12]}"
            print(f"  ✅ 使用 Agent: {agent_id[:12]}")
        else:
            print("  ❌ 没有找到 Agent")
            return
        
        # 测试 SubAgent 状态查询
        print("\n2. 测试 SubAgent 状态查询...")
        start = time.time()
        resp = client.get(f"/internal/subagents/{agent_id}/{subagent_id}")
        elapsed = time.time() - start
        print(f"  ✅ 成功: {resp.status_code}, 耗时 {elapsed:.3f}s")
        
        # 测试 Runtime 查询
        print("\n3. 测试 Runtime 查询...")
        start = time.time()
        resp = client.get(f"/internal/subagents/{agent_id}/{subagent_id}/runtime")
        elapsed = time.time() - start
        print(f"  ✅ 成功: {resp.status_code}, 耗时 {elapsed:.3f}s")
        
        client.close()
        
    except httpx.TimeoutException as e:
        elapsed = time.time() - start
        print(f"  ❌ 超时: {e}, 耗时 {elapsed:.3f}s")
    except Exception as e:
        elapsed = time.time() - start
        print(f"  ❌ 错误: {type(e).__name__}: {e}, 耗时 {elapsed:.3f}s")


def test_concurrent_requests():
    """测试并发请求"""
    print("\n\n" + "="*80)
    print("测试并发请求（模拟高负载）")
    print("="*80)
    
    import threading
    
    results = []
    
    def make_request(n):
        try:
            start = time.time()
            client = httpx.Client(base_url=GATEWAY_URL, timeout=10.0, trust_env=False)
            resp = client.get("/health")
            elapsed = time.time() - start
            results.append(("success", elapsed, resp.status_code))
            client.close()
        except httpx.TimeoutException:
            elapsed = time.time() - start
            results.append(("timeout", elapsed, None))
        except Exception as e:
            elapsed = time.time() - start
            results.append(("error", elapsed, str(e)))
    
    print("\n发送 20 个并发请求...")
    threads = []
    start_all = time.time()
    
    for i in range(20):
        t = threading.Thread(target=make_request, args=(i,))
        t.start()
        threads.append(t)
    
    for t in threads:
        t.join()
    
    total_time = time.time() - start_all
    
    # 统计结果
    success_count = sum(1 for r in results if r[0] == "success")
    timeout_count = sum(1 for r in results if r[0] == "timeout")
    error_count = sum(1 for r in results if r[0] == "error")
    
    avg_time = sum(r[1] for r in results if r[0] == "success") / success_count if success_count > 0 else 0
    max_time = max((r[1] for r in results if r[0] == "success"), default=0)
    
    print(f"\n结果:")
    print(f"  成功: {success_count}/20")
    print(f"  超时: {timeout_count}/20")
    print(f"  错误: {error_count}/20")
    print(f"  总耗时: {total_time:.3f}s")
    print(f"  平均耗时: {avg_time:.3f}s")
    print(f"  最大耗时: {max_time:.3f}s")


if __name__ == "__main__":
    print(f"开始时间: {datetime.now().isoformat()}\n")
    
    try:
        test_basic_requests()
        test_message_route_calls()
        test_concurrent_requests()
        
        print("\n\n" + "="*80)
        print("✅ 测试完成")
        print("="*80)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  测试被中断")
    except Exception as e:
        print(f"\n\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
