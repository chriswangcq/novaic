#!/usr/bin/env python3
"""5-Agent High-Intensity Stress Test"""
import asyncio, time, json, os
import httpx

# 禁用代理
os.environ['NO_PROXY'] = '*'
os.environ['no_proxy'] = '*'
os.environ['HTTP_PROXY'] = ''
os.environ['HTTPS_PROXY'] = ''
os.environ['http_proxy'] = ''
os.environ['https_proxy'] = ''

GATEWAY = "http://127.0.0.1:19999"

async def create_agents(n=5):
    """创建n个测试agent"""
    agents = []
    async with httpx.AsyncClient(trust_env=False) as client:
        for i in range(n):
            resp = await client.post(f"{GATEWAY}/api/agents", json={
                "name": f"StressTest-{i+1}",
                "description": "High-intensity stress test agent",
                "model": "kimi-k2.5"
            })
            agent = resp.json()
            agent_id = agent["id"]
            agents.append(agent_id)
            print(f"✓ Created agent {i+1}: {agent_id}")
    return agents

async def spawn_subagents(agent_ids):
    """每个agent spawn 3个subagent任务"""
    results = {"success": 0, "fail": 0}
    async with httpx.AsyncClient(timeout=30.0, trust_env=False) as client:
        for agent_id in agent_ids:
            await client.post(f"{GATEWAY}/api/agents/{agent_id}/select")
            
            for task_num in range(3):
                try:
                    resp = await client.post(f"{GATEWAY}/api/chat/send", json={
                        "content": f"Please spawn a subagent to help analyze task {task_num+1}. The subagent should summarize what it found."
                    }, timeout=30.0)
                    if resp.status_code == 200:
                        results["success"] += 1
                        print(f"✓ Agent {agent_id[:8]} spawn task {task_num+1}")
                    else:
                        results["fail"] += 1
                        print(f"✗ Agent {agent_id[:8]} spawn failed: {resp.status_code}")
                except Exception as e:
                    results["fail"] += 1
                    print(f"✗ Agent {agent_id[:8]} spawn error: {e}")
    return results

async def continuous_messages(agent_ids, duration_sec=300, interval=0.2):
    """连续发送消息"""
    results = {"success": 0, "fail": 0}
    start_time = time.time()
    msg_count = 0
    
    async with httpx.AsyncClient(timeout=10.0, trust_env=False) as client:
        while time.time() - start_time < duration_sec:
            agent_id = agent_ids[msg_count % len(agent_ids)]
            msg_count += 1
            
            try:
                await client.post(f"{GATEWAY}/api/agents/{agent_id}/select")
                resp = await client.post(f"{GATEWAY}/api/chat/send", json={
                    "content": f"Quick ping #{msg_count}, please respond briefly."
                }, timeout=10.0)
                
                if resp.status_code == 200:
                    results["success"] += 1
                    if msg_count % 50 == 0:
                        print(f"  [{int(time.time()-start_time)}s] Sent {msg_count} messages ({results['success']}/{msg_count})")
                else:
                    results["fail"] += 1
                    print(f"✗ Message {msg_count} failed: {resp.status_code}")
            except Exception as e:
                results["fail"] += 1
                print(f"✗ Message {msg_count} error: {e}")
            
            await asyncio.sleep(interval)
    
    return results, msg_count

async def check_status():
    """检查系统状态"""
    async with httpx.AsyncClient(trust_env=False) as client:
        tasks_resp = await client.get(f"{GATEWAY}/api/internal/tasks")
        tasks = tasks_resp.json()
        task_stats = {}
        for t in tasks:
            status = t.get("status", "unknown")
            task_stats[status] = task_stats.get(status, 0) + 1
        
        sagas_resp = await client.get(f"{GATEWAY}/api/internal/sagas")
        sagas = sagas_resp.json()
        saga_stats = {}
        for s in sagas:
            status = s.get("status", "unknown")
            saga_stats[status] = saga_stats.get(status, 0) + 1
        
        runtimes_resp = await client.get(f"{GATEWAY}/api/internal/runtimes")
        runtimes = runtimes_resp.json()
        runtime_stats = {}
        for r in runtimes:
            status = r.get("status", "unknown")
            runtime_stats[status] = runtime_stats.get(status, 0) + 1
        
        return {
            "tasks": task_stats,
            "sagas": saga_stats,
            "runtimes": runtime_stats
        }

async def main():
    print("=" * 80)
    print("🚀 Starting 5-Agent High-Intensity Stress Test")
    print("=" * 80)
    
    print("\n[1/4] Creating 5 agents...")
    agents = await create_agents(5)
    print(f"✓ Created {len(agents)} agents")
    
    print("\n[2/4] Spawning subagents (3 per agent)...")
    spawn_results = await spawn_subagents(agents)
    print(f"✓ Spawn results: {spawn_results['success']} success, {spawn_results['fail']} fail")
    
    print("\n[3/4] Waiting 30s for spawn tasks to process...")
    await asyncio.sleep(30)
    
    print("\n[4/4] Sending continuous messages (300s @ 0.2s interval)...")
    msg_results, total_msgs = await continuous_messages(agents, duration_sec=300, interval=0.2)
    
    print("\n" + "=" * 80)
    print("📊 FINAL RESULTS")
    print("=" * 80)
    print(f"Agents created: {len(agents)}")
    print(f"Subagent spawns: {spawn_results['success']}/{spawn_results['success']+spawn_results['fail']} success")
    print(f"Continuous messages: {msg_results['success']}/{total_msgs} success ({msg_results['fail']} failed)")
    
    print("\n📈 System Status:")
    status = await check_status()
    print(f"  Tasks: {status['tasks']}")
    print(f"  Sagas: {status['sagas']}")
    print(f"  Runtimes: {status['runtimes']}")
    
    print("\n✅ Stress test completed")

if __name__ == "__main__":
    asyncio.run(main())
