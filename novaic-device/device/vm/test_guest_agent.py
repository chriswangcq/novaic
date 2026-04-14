#!/usr/bin/env python3
"""
Test QEMU Guest Agent connectivity
测试 QEMU Guest Agent 连接
"""

import json
import socket
import sys
import time
from pathlib import Path
import tempfile


def send_qga_command(socket_path: str, command: dict, timeout: int = 5) -> dict:
    """
    Send a command to QEMU Guest Agent via socket.
    
    Args:
        socket_path: Path to the Guest Agent socket
        command: QGA command as dict
        timeout: Socket timeout in seconds
    
    Returns:
        Response from Guest Agent as dict
    """
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    
    try:
        sock.connect(socket_path)
        
        # Send command
        cmd_json = json.dumps(command) + "\n"
        sock.sendall(cmd_json.encode('utf-8'))
        
        # Receive response
        response = b""
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                break
            response += chunk
            # Check if we have a complete JSON response
            try:
                result = json.loads(response.decode('utf-8'))
                return result
            except json.JSONDecodeError:
                continue
        
        return json.loads(response.decode('utf-8'))
    
    finally:
        sock.close()


def test_guest_agent(agent_id: str):
    """
    Test Guest Agent connectivity for a specific agent.
    
    Args:
        agent_id: Agent ID (required)
    """
    # Build socket path
    socket_dir = Path(tempfile.gettempdir()) / "novaic"
    ga_socket_path = socket_dir / f"novaic-ga-{agent_id}.sock"
    
    print(f"Testing Guest Agent for agent {agent_id}")
    print(f"Socket path: {ga_socket_path}")
    print("-" * 60)
    
    # Check if socket exists
    if not ga_socket_path.exists():
        print(f"❌ ERROR: Socket file does not exist: {ga_socket_path}")
        print("\nPossible reasons:")
        print("  1. VM is not running")
        print("  2. QEMU was not started with Guest Agent configuration")
        print("  3. Wrong agent_id")
        print("\nTo fix:")
        print("  1. Start the VM first")
        print("  2. Check QEMU command includes Guest Agent parameters")
        return False
    
    print(f"✅ Socket file exists\n")
    
    # Test 1: guest-ping
    print("Test 1: guest-ping")
    try:
        response = send_qga_command(str(ga_socket_path), {"execute": "guest-ping"})
        if "return" in response:
            print(f"✅ guest-ping successful: {response}")
        else:
            print(f"❌ Unexpected response: {response}")
            return False
    except socket.timeout:
        print(f"❌ Timeout - Guest Agent not responding")
        print("\nPossible reasons:")
        print("  1. qemu-guest-agent not installed in VM")
        print("  2. qemu-guest-agent service not running in VM")
        print("\nTo fix (inside VM):")
        print("  Ubuntu/Debian:")
        print("    sudo apt-get update")
        print("    sudo apt-get install -y qemu-guest-agent")
        print("    sudo systemctl enable qemu-guest-agent")
        print("    sudo systemctl start qemu-guest-agent")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    print()
    
    # Test 2: guest-info
    print("Test 2: guest-info")
    try:
        response = send_qga_command(str(ga_socket_path), {"execute": "guest-info"})
        if "return" in response:
            info = response["return"]
            print(f"✅ guest-info successful")
            print(f"   Version: {info.get('version', 'N/A')}")
            print(f"   Supported commands: {len(info.get('supported_commands', []))}")
            
            # Show some important commands
            important_cmds = [
                'guest-file-open', 'guest-file-read', 'guest-file-write', 'guest-file-close',
                'guest-exec', 'guest-exec-status',
                'guest-shutdown', 'guest-sync',
            ]
            supported = [cmd['name'] for cmd in info.get('supported_commands', [])]
            print(f"\n   Important commands available:")
            for cmd in important_cmds:
                status = "✅" if cmd in supported else "❌"
                print(f"     {status} {cmd}")
        else:
            print(f"❌ Unexpected response: {response}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    print()
    print("=" * 60)
    print("✅ Guest Agent is working correctly!")
    print("=" * 60)
    return True


def list_sockets():
    """List all available Guest Agent sockets."""
    socket_dir = Path(tempfile.gettempdir()) / "novaic"
    
    print("Available Guest Agent sockets:")
    print("-" * 60)
    
    if not socket_dir.exists():
        print(f"Socket directory does not exist: {socket_dir}")
        return
    
    ga_sockets = list(socket_dir.glob("novaic-ga-*.sock"))
    
    if not ga_sockets:
        print("No Guest Agent sockets found.")
        print(f"(checked in {socket_dir})")
    else:
        for sock in sorted(ga_sockets):
            agent_id = sock.stem.replace('novaic-ga-', '')
            print(f"  Agent {agent_id}: {sock}")


def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        if sys.argv[1] == "list":
            list_sockets()
            return
        else:
            agent_id = sys.argv[1]
    else:
        print(f"Error: agent_id is required")
        print(f"Usage: {sys.argv[0]} <agent_id|list>")
        print(f"Example: {sys.argv[0]} 550e8400-e29b-41d4-a716-446655440000")
        print(f"         {sys.argv[0]} list")
        sys.exit(1)
    
    success = test_guest_agent(agent_id)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
