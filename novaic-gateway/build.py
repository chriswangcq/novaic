#!/usr/bin/env python3
"""
NovAIC Gateway Build Script

Packages the Gateway into a standalone executable using PyInstaller.
"""

import subprocess
import sys
import os
from pathlib import Path

def main():
    gateway_dir = Path(__file__).parent
    
    # Ensure we're in the gateway directory
    os.chdir(gateway_dir)
    
    # Install PyInstaller if not available
    try:
        import PyInstaller
    except ImportError:
        print("[Build] Installing PyInstaller...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
    
    # PyInstaller command
    # Use --onedir for faster startup (no extraction needed)
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onedir",
        "--name", "novaic-gateway",
        "--distpath", "dist",
        "--workpath", "build",
        "--specpath", "build",
        # Hidden imports that PyInstaller might miss
        "--hidden-import", "uvicorn.logging",
        "--hidden-import", "uvicorn.protocols.http",
        "--hidden-import", "uvicorn.protocols.http.auto",
        "--hidden-import", "uvicorn.protocols.http.h11_impl",
        "--hidden-import", "uvicorn.protocols.websockets",
        "--hidden-import", "uvicorn.protocols.websockets.auto",
        "--hidden-import", "uvicorn.protocols.websockets.wsproto_impl",
        "--hidden-import", "uvicorn.lifespan",
        "--hidden-import", "uvicorn.lifespan.on",
        "--hidden-import", "uvicorn.lifespan.off",
        "--hidden-import", "httpx",
        "--hidden-import", "httpx._transports",
        "--hidden-import", "httpx._transports.default",
        "--hidden-import", "anyio",
        "--hidden-import", "anyio._backends",
        "--hidden-import", "anyio._backends._asyncio",
        # Main entry point
        "main.py",
    ]
    
    print("[Build] Running PyInstaller...")
    print(f"[Build] Command: {' '.join(cmd)}")
    
    result = subprocess.run(cmd)
    
    if result.returncode == 0:
        print("\n[Build] Success!")
        print(f"[Build] Output: {gateway_dir / 'dist' / 'novaic-gateway'}")
    else:
        print("\n[Build] Failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
