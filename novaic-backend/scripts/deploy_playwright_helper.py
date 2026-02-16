#!/usr/bin/env python3
"""
Deploy Playwright Helper Script to VM

This script deploys the playwright_helper.py to a running VM via vmcontrol Guest Agent API.
It should be called after VM setup is complete.

Usage:
    python3 deploy_playwright_helper.py <vm_id> [vmcontrol_url]
    
    vm_id: VM ID (e.g., "1")
    vmcontrol_url: Optional vmcontrol service URL (default: http://localhost:9527)

Example:
    python3 deploy_playwright_helper.py 1
    python3 deploy_playwright_helper.py 1 http://localhost:9527
"""

import sys
import os
import json
import asyncio
import base64
from pathlib import Path
import httpx

from common.http.clients import internal_async_client


async def deploy_playwright_helper(vm_id: str, vmcontrol_url: str = "http://localhost:9527") -> None:
    """
    Deploy Playwright helper script to VM via vmcontrol API.
    
    Args:
        vm_id: VM ID (e.g., "1")
        vmcontrol_url: vmcontrol service URL
    """
    print(f"🚀 Deploying Playwright helper to VM {vm_id}...")
    print(f"   vmcontrol URL: {vmcontrol_url}")
    
    # Read the playwright helper script
    script_path = Path(__file__).parent / "playwright_helper.py"
    if not script_path.exists():
        print(f"❌ Error: Playwright helper script not found at {script_path}")
        sys.exit(1)
    
    with open(script_path, "rb") as f:
        script_content = f.read()
    
    print(f"✅ Read script ({len(script_content)} bytes)")
    
    # Create HTTP client (internal vmcontrol service)
    async with internal_async_client(base_url=vmcontrol_url, timeout=30.0) as client:
        try:
            # Test vmcontrol connection
            print(f"📡 Connecting to vmcontrol service...")
            response = await client.get("/health")
            response.raise_for_status()
            print("✅ vmcontrol service is healthy")
            
            # Create script directory
            print("📁 Creating /opt/novaic/scripts directory...")
            response = await client.post(
                f"/api/vms/{vm_id}/guest/exec",
                json={
                    "path": "/bin/mkdir",
                    "args": ["-p", "/opt/novaic/scripts"],
                    "wait": True
                }
            )
            response.raise_for_status()
            result = response.json()
            
            if result.get("exit_code", 0) != 0:
                print(f"⚠️  Warning: mkdir may have failed (probably already exists)")
            else:
                print("✅ Directory created")
            
            # Write script file
            print("📝 Writing playwright_helper.py...")
            script_b64 = base64.b64encode(script_content).decode('utf-8')
            
            response = await client.post(
                f"/api/vms/{vm_id}/guest/file",
                json={
                    "path": "/opt/novaic/scripts/playwright_helper.py",
                    "content": script_b64
                }
            )
            response.raise_for_status()
            write_result = response.json()
            
            if not write_result.get("success"):
                print("❌ Error: Failed to write script file")
                sys.exit(1)
            
            print(f"✅ Script written ({write_result.get('bytes_written', 0)} bytes)")
            
            # Make script executable
            print("🔧 Making script executable...")
            response = await client.post(
                f"/api/vms/{vm_id}/guest/exec",
                json={
                    "path": "/bin/chmod",
                    "args": ["+x", "/opt/novaic/scripts/playwright_helper.py"],
                    "wait": True
                }
            )
            response.raise_for_status()
            result = response.json()
            
            if result.get("exit_code", 0) != 0:
                print("❌ Error: Failed to chmod script")
                sys.exit(1)
            
            print("✅ Script is now executable")
            
            # Verify Playwright is installed
            print("🔍 Checking Playwright installation...")
            response = await client.post(
                f"/api/vms/{vm_id}/guest/exec",
                json={
                    "path": "/opt/novaic-venv/bin/python3",
                    "args": ["-c", "import playwright; print(playwright.__version__)"],
                    "wait": True
                }
            )
            response.raise_for_status()
            result = response.json()
            
            if result.get("exit_code") == 0:
                stdout = result.get("stdout", "")
                if stdout:
                    # stdout is already decoded by vmcontrol
                    version = stdout.strip()
                    print(f"✅ Playwright is installed (version: {version})")
                else:
                    print("✅ Playwright is installed")
            else:
                print("⚠️  Warning: Playwright may not be installed")
                print("   You may need to run: /opt/novaic-venv/bin/pip install playwright")
                print("   and: /opt/novaic-venv/bin/playwright install chromium")
            
            print("\n🎉 Deployment complete!")
            print("\nYou can now use browser control APIs:")
            print(f"  POST {vmcontrol_url}/api/vms/{vm_id}/browser/navigate")
            print(f"  POST {vmcontrol_url}/api/vms/{vm_id}/browser/click")
            print(f"  POST {vmcontrol_url}/api/vms/{vm_id}/browser/type")
            print(f"  GET  {vmcontrol_url}/api/vms/{vm_id}/browser/content")
            print(f"  POST {vmcontrol_url}/api/vms/{vm_id}/browser/screenshot")
            
        except httpx.HTTPStatusError as e:
            print(f"❌ HTTP Error: {e.response.status_code}")
            print(f"   Response: {e.response.text}")
            sys.exit(1)
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


async def main():
    if len(sys.argv) < 2:
        print("Usage: python3 deploy_playwright_helper.py <vm_id> [vmcontrol_url]")
        print("\nExample:")
        print("  python3 deploy_playwright_helper.py 1")
        print("  python3 deploy_playwright_helper.py 1 http://localhost:9527")
        sys.exit(1)
    
    vm_id = sys.argv[1]
    vmcontrol_url = sys.argv[2] if len(sys.argv) > 2 else "http://localhost:9527"
    
    await deploy_playwright_helper(vm_id, vmcontrol_url)


if __name__ == "__main__":
    asyncio.run(main())
