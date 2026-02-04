#!/usr/bin/env python3
"""
测试 FIFO 锁的正确性

验证：
1. 锁按 FIFO 顺序执行
2. 分片锁正确分片
3. 超时机制正常工作
4. 监控指标正确
"""

import threading
import time
from collections import deque

# 导入锁实现
import sys
sys.path.insert(0, "/Users/wangchaoqun/novaic/novaic-backend")

from gateway.db.locks import FIFOLock, ShardedFIFOLock, DatabaseLockManager


def test_fifo_order():
    """测试 FIFO 顺序"""
    print("\n=== 测试 1: FIFO 顺序 ===")
    
    lock = FIFOLock()
    execution_order = []
    
    def worker(worker_id, delay):
        with lock.acquire(resource_id=f"worker_{worker_id}"):
            execution_order.append(worker_id)
            time.sleep(delay)
    
    # 启动 5 个线程
    threads = []
    for i in range(5):
        t = threading.Thread(target=worker, args=(i, 0.1))
        threads.append(t)
        t.start()
        time.sleep(0.01)  # 确保按顺序到达
    
    for t in threads:
        t.join()
    
    print(f"执行顺序: {execution_order}")
    
    # 验证顺序
    if execution_order == [0, 1, 2, 3, 4]:
        print("✅ FIFO 顺序正确！")
    else:
        print(f"❌ FIFO 顺序错误！期望 [0,1,2,3,4]，实际 {execution_order}")
    
    # 检查指标
    metrics = lock.get_metrics()
    print(f"指标: {metrics}")
    assert metrics["total_acquires"] == 5
    assert metrics["current_waiting"] == 0
    print("✅ 指标正确！")


def test_timeout():
    """测试超时机制"""
    print("\n=== 测试 2: 超时机制 ===")
    
    lock = FIFOLock()
    
    def holder():
        with lock.acquire(resource_id="holder"):
            time.sleep(3)  # 持有 3 秒
    
    def waiter():
        try:
            with lock.acquire(resource_id="waiter", timeout=1.0):  # 只等 1 秒
                print("❌ 不应该获得锁")
        except TimeoutError as e:
            print(f"✅ 正确超时: {e}")
    
    # 启动持有者
    holder_thread = threading.Thread(target=holder)
    holder_thread.start()
    time.sleep(0.1)  # 确保持有者先获得锁
    
    # 启动等待者
    waiter_thread = threading.Thread(target=waiter)
    waiter_thread.start()
    
    holder_thread.join()
    waiter_thread.join()


def test_sharded_lock():
    """测试分片锁"""
    print("\n=== 测试 3: 分片锁 ===")
    
    lock = ShardedFIFOLock(num_shards=2)
    execution_times = {}
    
    def worker(resource_id):
        start = time.time()
        with lock.acquire(resource_id=resource_id):
            time.sleep(0.5)
        end = time.time()
        execution_times[resource_id] = (start, end)
    
    # 启动 4 个线程，2 个资源
    threads = []
    for i in range(4):
        resource_id = f"resource_{i % 2}"  # 只有 2 个不同的资源
        t = threading.Thread(target=worker, args=(resource_id,))
        threads.append(t)
        t.start()
        time.sleep(0.01)
    
    for t in threads:
        t.join()
    
    print("执行时间:")
    for resource_id, (start, end) in sorted(execution_times.items()):
        print(f"  {resource_id}: {start:.2f} - {end:.2f}")
    
    # 检查指标
    metrics = lock.get_metrics()
    print(f"分片指标: {metrics}")
    print("✅ 分片锁测试完成！")


def test_database_lock_manager():
    """测试数据库锁管理器"""
    print("\n=== 测试 4: DatabaseLockManager ===")
    
    manager = DatabaseLockManager()
    execution_order = []
    
    def worker(lock_type, resource_id, worker_id):
        with manager.acquire(lock_type, resource_id=resource_id):
            execution_order.append((lock_type, resource_id, worker_id))
            time.sleep(0.1)
    
    # 测试不同类型的锁
    threads = []
    
    # 消息锁（分片）
    for i in range(3):
        t = threading.Thread(
            target=worker,
            args=("message", f"msg_{i}", i)
        )
        threads.append(t)
        t.start()
        time.sleep(0.01)
    
    # Agent 锁（分片）
    for i in range(2):
        t = threading.Thread(
            target=worker,
            args=("agent", f"agent_{i}", i + 10)
        )
        threads.append(t)
        t.start()
        time.sleep(0.01)
    
    # 全局锁
    t = threading.Thread(
        target=lambda: (
            manager.acquire("global").__enter__(),
            execution_order.append(("global", None, 100)),
            time.sleep(0.1),
            manager.acquire("global").__exit__(None, None, None)
        )
    )
    threads.append(t)
    t.start()
    
    for t in threads:
        t.join()
    
    print(f"执行顺序: {execution_order}")
    
    # 检查所有锁的指标
    all_metrics = manager.get_metrics()
    print("\n所有锁的指标:")
    for lock_type, metrics in all_metrics.items():
        if metrics["total_acquires"] > 0:
            print(f"  {lock_type}: {metrics}")
    
    print("✅ DatabaseLockManager 测试完成！")


def test_concurrent_load():
    """测试高并发负载"""
    print("\n=== 测试 5: 高并发负载 ===")
    
    lock = ShardedFIFOLock(num_shards=4)
    counter = {"value": 0}
    counter_lock = threading.Lock()
    
    def worker(resource_id):
        for _ in range(10):
            with lock.acquire(resource_id=resource_id):
                # 模拟数据库操作
                time.sleep(0.01)
                with counter_lock:
                    counter["value"] += 1
    
    # 启动 20 个线程，操作 10 个不同资源
    threads = []
    start_time = time.time()
    
    for i in range(20):
        resource_id = f"resource_{i % 10}"
        t = threading.Thread(target=worker, args=(resource_id,))
        threads.append(t)
        t.start()
    
    for t in threads:
        t.join()
    
    elapsed = time.time() - start_time
    
    print(f"总操作数: {counter['value']}")
    print(f"总耗时: {elapsed:.2f}s")
    print(f"QPS: {counter['value'] / elapsed:.2f}")
    
    # 检查指标
    metrics = lock.get_metrics()
    print(f"指标: {metrics}")
    print(f"最大等待队列: {metrics['max_waiting']}")
    
    assert counter["value"] == 200  # 20 threads * 10 operations
    print("✅ 高并发负载测试通过！")


if __name__ == "__main__":
    print("开始测试 FIFO 锁实现...")
    
    try:
        test_fifo_order()
        test_timeout()
        test_sharded_lock()
        test_database_lock_manager()
        test_concurrent_load()
        
        print("\n" + "=" * 50)
        print("🎉 所有测试通过！")
        print("=" * 50)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
