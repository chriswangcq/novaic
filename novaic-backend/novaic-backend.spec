# -*- mode: python ; coding: utf-8 -*-
"""
NovAIC Backend - Unified PyInstaller Spec

v4.0: Single binary for gateway and workers (Saga/Task Architecture).
Uses onedir mode for faster startup and shared libraries.

Build:
    pyinstaller --clean --noconfirm novaic-backend.spec

Output:
    dist/novaic-backend/
    ├── novaic-backend          # Main executable
    └── _internal/              # Shared runtime and libraries

Entry points (via main_novaic.py unified CLI):
    - main_novaic.py    Unified entry point with subcommands:
        gateway         Gateway (API + SSE + DB)
        mcp-gateway     MCP Gateway (MCP aggregation)
        watchdog        Watchdog (message monitor, triggers Saga)
        task-worker     Task Worker (executes tasks)
        saga-worker     Saga Worker (orchestrates workflows)
        health          Health Worker (timeout recovery)
"""

from PyInstaller.utils.hooks import copy_metadata, collect_all, collect_submodules

# ==================== Metadata Collection ====================
# Required for packages that use importlib.metadata
datas = []
for pkg in [
    'fastmcp', 'mcp', 'aiohttp', 'aiofiles', 'httpx',
    'uvicorn', 'fastapi', 'starlette', 'pydantic', 'anyio', 'websockets',
]:
    try:
        datas += copy_metadata(pkg)
    except Exception:
        pass  # Package may not be installed

# ==================== Package Collection ====================
binaries = []
hiddenimports = []

# Collect all files from critical packages
critical_packages = [
    'fakeredis',  # FastMCP session management (includes commands.json)
    'lupa',       # Lua bindings for fakeredis
    'docket',     # FastMCP dependency
    'aiohttp',    # SSE and HTTP client
]

for pkg in critical_packages:
    try:
        d, b, h = collect_all(pkg)
        datas += d
        binaries += b
        hiddenimports += h
    except Exception:
        pass

# ==================== Analysis ====================
a = Analysis(
    ['main_novaic.py'],  # Unified entry point (v4)
    pathex=[],
    binaries=binaries,
    datas=datas + [
        # ===== Gateway package (all modules under gateway/) =====
        ('gateway', 'gateway'),
        # ===== MCP Gateway package =====
        ('mcp_gateway', 'mcp_gateway'),
        # ===== Task Queue (Saga/Task Architecture) =====
        ('task_queue', 'task_queue'),
        # ===== Entry points (for imports by main_novaic.py) =====
        ('main_gateway.py', '.'),
        ('main_mcp.py', '.'),
        ('main_watchdog.py', '.'),
        ('main_task.py', '.'),
        ('main_saga.py', '.'),
        ('main_health.py', '.'),
    ],
    hiddenimports=hiddenimports + [
        # ----- uvicorn -----
        'uvicorn.logging',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.lifespan.on',
        'uvicorn.lifespan.off',
        # ----- http clients -----
        'httpx',
        'httpx._client',
        'httpx._transports',
        'httpx._transports.default',
        'httpx_sse',
        'aiohttp',
        'aiohttp.client',
        'aiohttp.connector',
        'aiohttp.http_parser',
        # ----- async io -----
        'aiosqlite',
        'aiofiles',
        'asyncio',
        # ----- fastapi & pydantic -----
        'fastapi',
        'fastapi.middleware',
        'fastapi.middleware.cors',
        'fastapi.responses',
        'fastapi.staticfiles',
        'pydantic',
        'starlette',
        'starlette.routing',
        'starlette.responses',
        'starlette.middleware',
        # ----- fastmcp & mcp -----
        'fastmcp',
        'fastmcp.server',
        'fastmcp.server.server',
        'fastmcp.server.http',
        'mcp',
        'mcp.server',
        'mcp.server.streamable_http',
        'mcp.server.streamable_http_manager',
        # ----- anyio -----
        'anyio',
        'anyio._backends',
        'anyio._backends._asyncio',
        # ----- websockets -----
        'websockets',
        'websockets.legacy',
        'websockets.server',
        # ----- lupa (lua bindings) -----
        'lupa',
        'lupa.lua54',  # Primary lua version
        # ----- fakeredis -----
        'fakeredis',
        'fakeredis.aioredis',
        # ----- aiohttp dependencies -----
        'multidict',
        'multidict._multidict',
        'yarl',
        'yarl._url',
        # ----- httpx dependencies -----
        'h11',
        'httpcore',
        'httpcore._async',
        'httpcore._sync',
        'sniffio',
        # ----- ssl -----
        'ssl',
        'certifi',
        # ----- other -----
        'asyncssh',
        'PIL',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude unnecessary packages to reduce size
        'tkinter',
        'unittest',
        'test',
        'tests',
        'pip',
        'setuptools',
        'wheel',
        'distutils',
        'pkg_resources',
        # Exclude unused lupa versions (keep only lua54)
        'lupa.lua51',
        'lupa.lua52',
        'lupa.lua53',
        'lupa.luajit20',
        'lupa.luajit21',
    ],
    noarchive=False,
    optimize=0,
)

# ==================== PYZ Archive ====================
pyz = PYZ(a.pure)

# ==================== Executable ====================
# onedir mode: executable + _internal folder
exe = EXE(
    pyz,
    a.scripts,
    [],                      # Empty - binaries go to COLLECT
    exclude_binaries=True,   # Key: separate binaries to _internal
    name='novaic-backend',
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

# ==================== Collect (onedir output) ====================
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='novaic-backend',  # Output directory name
)
