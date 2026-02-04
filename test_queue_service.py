#!/usr/bin/env python3
"""
Queue Service 测试脚本

验证 Queue Service 的基本功能。
"""

import httpx
import time
import sys

QUEUE_SERVICE_URL = "http://127.0.0.1:19997"


def test_health():
    """测试健康检查"""
    print("🔍 Testing health check...")
    
    try:
        resp = httpx.get(f"{QUEUE_SERVICE_URL}/health", timeout=5.0)
        if resp.status_code == 200:
            data = resp.json()
            print(f"✅ Health check passed: {data}")
            return True
        else:
            print(f"❌ Health check failed: {resp.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False


def test_root():
    """测试根路径"""
    print("\n🔍 Testing root endpoint...")
    
    try:
        resp = httpx.get(f"{QUEUE_SERVICE_URL}/", timeout=5.0)
        if resp.status_code == 200:
            data = resp.json()
            print(f"✅ Root endpoint passed: {data.get('service')}")
            return True
        else:
            print(f"❌ Root endpoint failed: {resp.status_code}")
            return False
    except Exception as e:
        print(f"❌ Root endpoint error: {e}")
        return False


def test_task_publish():
    """测试发布任务"""
    print("\n🔍 Testing task publish...")
    
    try:
        resp = httpx.post(
            f"{QUEUE_SERVICE_URL}/api/queue/tasks/publish",
            json={
                "topic": "test.task",
                "payload": {"message": "Hello Queue Service!"},
                "max_retries": 3,
            },
            timeout=5.0
        )
        
        if resp.status_code == 200:
            data = resp.json()
            task_id = data.get("task_id")
            print(f"✅ Task published: {task_id}")
            return task_id
        else:
            print(f"❌ Task publish failed: {resp.status_code} - {resp.text}")
            return None
    except Exception as e:
        print(f"❌ Task publish error: {e}")
        return None


def test_task_claim(topics):
    """测试认领任务"""
    print("\n🔍 Testing task claim...")
    
    try:
        resp = httpx.post(
            f"{QUEUE_SERVICE_URL}/api/queue/tasks/claim",
            json={
                "topics": topics,
                "worker_id": "test-worker",
            },
            timeout=5.0
        )
        
        if resp.status_code == 200:
            data = resp.json()
            task = data.get("task")
            if task:
                print(f"✅ Task claimed: {task['id']}")
                return task
            else:
                print("ℹ️  No task available to claim")
                return None
        else:
            print(f"❌ Task claim failed: {resp.status_code} - {resp.text}")
            return None
    except Exception as e:
        print(f"❌ Task claim error: {e}")
        return None


def test_task_complete(task_id):
    """测试完成任务"""
    print("\n🔍 Testing task complete...")
    
    try:
        resp = httpx.post(
            f"{QUEUE_SERVICE_URL}/api/queue/tasks/{task_id}/complete",
            json={
                "result": {"status": "success", "data": "Task completed!"},
            },
            timeout=5.0
        )
        
        if resp.status_code == 200:
            data = resp.json()
            print(f"✅ Task completed: {data}")
            return True
        else:
            print(f"❌ Task complete failed: {resp.status_code} - {resp.text}")
            return False
    except Exception as e:
        print(f"❌ Task complete error: {e}")
        return False


def test_saga_start():
    """测试启动 Saga"""
    print("\n🔍 Testing saga start...")
    
    try:
        resp = httpx.post(
            f"{QUEUE_SERVICE_URL}/api/queue/sagas/start",
            json={
                "saga_type": "test.saga",
                "context": {"user_id": "test-user", "action": "test"},
            },
            timeout=5.0
        )
        
        if resp.status_code == 200:
            data = resp.json()
            saga_id = data.get("saga_id")
            print(f"✅ Saga started: {saga_id}")
            return saga_id
        else:
            print(f"❌ Saga start failed: {resp.status_code} - {resp.text}")
            return None
    except Exception as e:
        print(f"❌ Saga start error: {e}")
        return None


def test_saga_claim(saga_types):
    """测试认领 Saga"""
    print("\n🔍 Testing saga claim...")
    
    try:
        resp = httpx.post(
            f"{QUEUE_SERVICE_URL}/api/queue/sagas/claim",
            json={
                "saga_types": saga_types,
                "worker_id": "test-saga-worker",
            },
            timeout=5.0
        )
        
        if resp.status_code == 200:
            data = resp.json()
            saga = data.get("saga")
            if saga:
                print(f"✅ Saga claimed: {saga['id']}")
                return saga
            else:
                print("ℹ️  No saga available to claim")
                return None
        else:
            print(f"❌ Saga claim failed: {resp.status_code} - {resp.text}")
            return None
    except Exception as e:
        print(f"❌ Saga claim error: {e}")
        return None


def test_saga_complete(saga_id):
    """测试完成 Saga"""
    print("\n🔍 Testing saga complete...")
    
    try:
        resp = httpx.post(
            f"{QUEUE_SERVICE_URL}/api/queue/sagas/{saga_id}/complete",
            json={
                "step_results": {"step1": "success", "step2": "success"},
            },
            timeout=5.0
        )
        
        if resp.status_code == 200:
            data = resp.json()
            print(f"✅ Saga completed: {data}")
            return True
        else:
            print(f"❌ Saga complete failed: {resp.status_code} - {resp.text}")
            return False
    except Exception as e:
        print(f"❌ Saga complete error: {e}")
        return False


def main():
    """运行所有测试"""
    print("=" * 60)
    print("Queue Service 测试")
    print("=" * 60)
    
    # 1. 健康检查
    if not test_health():
        print("\n❌ 健康检查失败，请确保 Queue Service 已启动")
        print("   启动命令：./start_queue_service.sh")
        sys.exit(1)
    
    # 2. 根路径
    if not test_root():
        print("\n⚠️  根路径测试失败")
    
    # 3. Task Queue 测试
    print("\n" + "=" * 60)
    print("Task Queue 功能测试")
    print("=" * 60)
    
    task_id = test_task_publish()
    if task_id:
        time.sleep(0.5)  # 等待任务写入
        
        task = test_task_claim(["test.task"])
        if task:
            test_task_complete(task["id"])
    
    # 4. Saga 测试
    print("\n" + "=" * 60)
    print("Saga 功能测试")
    print("=" * 60)
    
    saga_id = test_saga_start()
    if saga_id:
        time.sleep(0.5)  # 等待 Saga 写入
        
        saga = test_saga_claim(["test.saga"])
        if saga:
            test_saga_complete(saga["id"])
    
    # 5. 总结
    print("\n" + "=" * 60)
    print("✅ Queue Service 测试完成")
    print("=" * 60)
    print("\n提示：")
    print("  - 查看日志：tail -f $NOVAIC_DATA_DIR/logs/queue-service-*.log")
    print("  - 查看数据库：sqlite3 $NOVAIC_DATA_DIR/queue.db")
    print("  - API 文档：http://127.0.0.1:19997/docs")


if __name__ == "__main__":
    main()
