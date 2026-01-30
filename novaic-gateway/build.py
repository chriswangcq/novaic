#!/usr/bin/env python3
"""
NovAIC Gateway Build Script

Packages the Gateway into a standalone executable using PyInstaller.
"""

import subprocess
import sys
import os
import shutil
from pathlib import Path

def main():
    gateway_dir = Path(__file__).parent
    os.chdir(gateway_dir)
    
    # Install PyInstaller if not available
    try:
        import PyInstaller
    except ImportError:
        print("[Build] Installing PyInstaller...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
    
    # Clean previous build
    print("[Build] Cleaning previous build...")
    for d in ["build", "dist", "__pycache__"]:
        if (gateway_dir / d).exists():
            shutil.rmtree(gateway_dir / d)
    
    # PyInstaller command - put --collect-all FIRST for reliable collection
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onedir",
        "--noconfirm",
        "--name", "novaic-gateway",
        "--distpath", "dist",
        "--workpath", "build",
        "--specpath", "build",
        # IMPORTANT: --collect-all must come first for reliable package collection
        "--collect-all", "fastmcp",
        "--collect-all", "mcp",
        "--collect-all", "starlette",
        "--collect-all", "aiosqlite",
        "--collect-all", "bs4",
        "--collect-all", "html2text",
        "--collect-all", "readability",
        # FastMCP internal dependencies (required for lifespan init)
        "--collect-all", "fakeredis",
        "--collect-all", "lupa",
        # Hidden imports for modules that might be missed
        "--hidden-import", "uvicorn.logging",
        "--hidden-import", "httpx",
        "--hidden-import", "anyio",
        "--hidden-import", "aiofiles",
        "--hidden-import", "mcp_servers",
        "--hidden-import", "mcp_servers.base",
        "--hidden-import", "mcp_servers.agent_context",
        "--hidden-import", "mcp_servers.local",
        "--hidden-import", "mcp_servers.memory",
        "--hidden-import", "mcp_servers.chat",
        "--hidden-import", "mcp_servers.manager",
        "--hidden-import", "lupa.lua51",
        "--hidden-import", "lupa.lua52",
        "--hidden-import", "lupa.lua53",
        "--hidden-import", "lupa.lua54",
        "--hidden-import", "lupa.luajit20",
        "--hidden-import", "lupa.luajit21",
        "--hidden-import", "fakeredis",
        "--hidden-import", "fakeredis.aioredis",
        # Main entry point
        "main.py",
    ]
    
    print("[Build] Running PyInstaller...")
    print(f"[Build] Command: {' '.join(cmd)}")
    
    result = subprocess.run(cmd)
    
    if result.returncode == 0:
        internal_dir = gateway_dir / "dist" / "novaic-gateway" / "_internal"
        
        # Copy skills directory to dist
        skills_src = gateway_dir / "skills"
        skills_dst = internal_dir / "skills"
        if skills_src.exists():
            if skills_dst.exists():
                shutil.rmtree(skills_dst)
            shutil.copytree(skills_src, skills_dst)
            print(f"[Build] Copied skills to: {skills_dst}")
        
        # Fix fakeredis data files (commands.json)
        # fakeredis looks for commands.json relative to its model directory
        try:
            import site
            for sp in site.getsitepackages() + [site.getusersitepackages()]:
                fakeredis_src = Path(sp) / "fakeredis" / "commands.json"
                if fakeredis_src.exists():
                    fakeredis_dst = internal_dir / "fakeredis" / "commands.json"
                    fakeredis_dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(fakeredis_src, fakeredis_dst)
                    print(f"[Build] Copied fakeredis/commands.json")
                    break
        except Exception as e:
            print(f"[Build] Warning: Could not copy fakeredis data: {e}")
        
        print("\n[Build] Success!")
        print(f"[Build] Output: {gateway_dir / 'dist' / 'novaic-gateway'}")
    else:
        print("\n[Build] Failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
