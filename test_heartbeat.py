#!/usr/bin/env python3
"""
测试心跳器功能
"""

import asyncio
import time
import sys
sys.path.insert(0, '/Users/wangchaoqun/novaic/novaic-backend')

from task_queue.heartbeat import Heartbeat, heartbeat, HeartbeatGroup


# ==================== 测试 1: 基本功能 ====================

async def test_basic():
    """测试基本功能"""
    print("\n=== 测试 1: 基本功能 ===")
    
    heartbeat_count = 0
    
    async def send_heartbeat():
        nonlocal heartbeat_count
        heartbeat_count += 1
        print(f"  ❤️  发送心跳 #{heartbeat_count}")
        return True
    
    print("开始任务...")
    start = time.time()
    
    async with Heartbeat("test-1", send_heartbeat, interval=2.0):
        print("  心跳已启动（后台运行）")
        await asyncio.sleep(7)  # 运行 7 秒
        print("  任务完成")
    
    elapsed = time.time() - start
    print(f"✅ 完成！耗时 {elapsed:.1f}s，共发送 {heartbeat_count} 次心跳")
    print(f"   预期：3 次（2s, 4s, 6s）")


# ==================== 测试 2: 统计信息 ====================

async def test_stats():
    """测试统计信息"""
    print("\n=== 测试 2: 统计信息 ===")
    
    call_count = 0
    
    async def send_heartbeat():
        nonlocal call_count
        call_count += 1
        # 模拟：前 2 次成功，第 3 次失败
        if call_count <= 2:
            print(f"  ✅ 心跳成功 #{call_count}")
            return True
        else:
            print(f"  ❌ 心跳失败 #{call_count}")
            return False
    
    async with Heartbeat("test-2", send_heartbeat, interval=1.0) as hb:
        await asyncio.sleep(5)
        
        stats = hb.get_stats()
        print(f"\n统计信息:")
        print(f"  成功: {stats['success_count']}")
        print(f"  失败: {stats['failure_count']}")
        print(f"  连续失败: {stats['consecutive_failures']}")
        print(f"  是否有失败: {hb.failed}")


# ==================== 测试 3: 失败回调 ====================

async def test_failure_callback():
    """测试失败回调"""
    print("\n=== 测试 3: 失败回调 ===")
    
    failure_notifications = []
    
    def on_failure(count: int):
        msg = f"⚠️  连续失败 {count} 次"
        failure_notifications.append(msg)
        print(f"  {msg}")
    
    async def send_heartbeat():
        print("  ❌ 心跳失败")
        return False  # 总是失败
    
    async with Heartbeat(
        "test-3",
        send_heartbeat,
        interval=1.0,
        fail_threshold=3,  # 连续失败 3 次后停止
        on_failure=on_failure
    ):
        await asyncio.sleep(5)
    
    print(f"✅ 共收到 {len(failure_notifications)} 次失败通知")


# ==================== 测试 4: 简化版 ====================

async def test_simplified():
    """测试简化版 heartbeat() 函数"""
    print("\n=== 测试 4: 简化版 API ===")
    
    count = 0
    
    async def send_hb():
        nonlocal count
        count += 1
        print(f"  ❤️  心跳 #{count}")
        return True
    
    async with heartbeat("test-4", send_hb, interval=2.0):
        await asyncio.sleep(5)
    
    print(f"✅ 发送了 {count} 次心跳")


# ==================== 测试 5: 心跳组 ====================

async def test_group():
    """测试心跳组"""
    print("\n=== 测试 5: 心跳组 ===")
    
    counts = {"task": 0, "saga": 0}
    
    async def send_task_hb():
        counts["task"] += 1
        print(f"  🔵 Task 心跳 #{counts['task']}")
        return True
    
    async def send_saga_hb():
        counts["saga"] += 1
        print(f"  🟢 Saga 心跳 #{counts['saga']}")
        return True
    
    group = HeartbeatGroup()
    
    async with group.add("task-1", send_task_hb, interval=2.0):
        async with group.add("saga-1", send_saga_hb, interval=3.0):
            print("  两个心跳同时运行")
            await asyncio.sleep(7)
            
            # 查看所有统计
            stats = group.get_all_stats()
            print(f"\n统计:")
            for name, stat in stats.items():
                print(f"  {name}: 成功 {stat['success_count']} 次")
    
    print(f"✅ Task: {counts['task']} 次, Saga: {counts['saga']} 次")


# ==================== 测试 6: 异常处理 ====================

async def test_exception_handling():
    """测试异常处理"""
    print("\n=== 测试 6: 异常处理 ===")
    
    call_count = 0
    
    async def send_heartbeat():
        nonlocal call_count
        call_count += 1
        if call_count == 2:
            print(f"  💥 抛出异常")
            raise Exception("网络错误")
        print(f"  ✅ 心跳成功 #{call_count}")
        return True
    
    async with Heartbeat("test-6", send_heartbeat, interval=1.0) as hb:
        await asyncio.sleep(4)
        
        print(f"\n结果:")
        print(f"  成功: {hb.success_count}")
        print(f"  失败: {hb.failure_count}")


# ==================== 测试 7: 性能测试 ====================

async def test_performance():
    """测试性能"""
    print("\n=== 测试 7: 性能测试（100个心跳器）===")
    
    total_heartbeats = 0
    
    async def send_hb():
        nonlocal total_heartbeats
        total_heartbeats += 1
        return True
    
    start = time.time()
    
    # 创建 100 个并发心跳
    tasks = []
    for i in range(100):
        async def run_heartbeat(id):
            async with Heartbeat(f"test-{id}", send_hb, interval=0.5):
                await asyncio.sleep(2)
        
        tasks.append(run_heartbeat(i))
    
    await asyncio.gather(*tasks)
    
    elapsed = time.time() - start
    print(f"✅ 100个心跳器运行 2 秒")
    print(f"   耗时: {elapsed:.2f}s")
    print(f"   总心跳: {total_heartbeats}")
    print(f"   预期: ~400 次（100个 × 4次）")


# ==================== 测试 8: 提前停止 ====================

async def test_early_stop():
    """测试提前停止"""
    print("\n=== 测试 8: 提前停止 ===")
    
    count = 0
    
    async def send_hb():
        nonlocal count
        count += 1
        print(f"  ❤️  心跳 #{count}")
        return True
    
    async with Heartbeat("test-8", send_hb, interval=1.0):
        print("  运行 2 秒后提前退出...")
        await asyncio.sleep(2)
        print("  退出")
    
    print(f"✅ 心跳自动停止，共发送 {count} 次")


# ==================== 运行所有测试 ====================

async def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("心跳器功能测试")
    print("=" * 60)
    
    tests = [
        test_basic,
        test_stats,
        test_failure_callback,
        test_simplified,
        test_group,
        test_exception_handling,
        test_performance,
        test_early_stop,
    ]
    
    for test in tests:
        try:
            await test()
        except Exception as e:
            print(f"❌ 测试失败: {e}")
            import traceback
            traceback.print_exc()
        
        await asyncio.sleep(0.5)  # 测试间隔
    
    print("\n" + "=" * 60)
    print("所有测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(run_all_tests())
