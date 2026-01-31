# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for novaic-worker

Worker is a lightweight process that:
- Connects to Gateway via SSE
- Claims and executes tasks (think, tool_call, reply)
- Reports results back to Gateway
"""

from PyInstaller.utils.hooks import collect_all, collect_submodules

# Collect all aiohttp files (required for SSE connection)
aiohttp_datas, aiohttp_binaries, aiohttp_hiddenimports = collect_all('aiohttp')

a = Analysis(
    ['worker_main.py'],
    pathex=[],
    binaries=aiohttp_binaries,
    datas=aiohttp_datas + [
        ('worker', 'worker'),
        ('executor', 'executor'),  # v2.9: MCPClient for session management
    ],
    hiddenimports=aiohttp_hiddenimports + [
        # http clients
        'aiohttp',
        'aiohttp.client',
        'aiohttp.connector',
        'aiohttp.http_parser',
        # httpx (for MCPClient)
        'httpx',
        'httpx._client',
        'httpx._transports',
        'httpx._transports.default',
        'httpx_sse',
        # multidict (aiohttp dependency)
        'multidict',
        'multidict._multidict',
        # yarl (aiohttp dependency)
        'yarl',
        'yarl._url',
        # async io
        'asyncio',
        'aiofiles',
        # anyio for async
        'anyio',
        'anyio._backends',
        'anyio._backends._asyncio',
        # ssl/tls
        'ssl',
        'certifi',
        # h11 (httpx dependency)
        'h11',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='novaic-worker',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
