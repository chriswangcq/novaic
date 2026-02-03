# -*- mode: python ; coding: utf-8 -*-
"""
NovAIC Backend - Unified PyInstaller Spec

v3.0: Single binary for gateway and workers (Three-Task Architecture).
Uses onedir mode for faster startup and shared libraries.

Build:
    pyinstaller --clean --noconfirm novaic-backend.spec

Output:
    dist/novaic-backend/
    ├── novaic-backend          # Main executable
    └── _internal/              # Shared runtime and libraries

Entry points:
    - main.py           Gateway (API + SSE)
    - mcp_main.py       MCP Gateway
    - monitor_main.py   Monitor (event-driven message queue consumer)
    - launcher_main.py  Launcher Worker
    - collector_main.py Collector Worker
    - executor_main.py  Executor Worker (LLM/Tool execution)
    - health_main.py    Health Monitor
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
    ['novaic_main.py'],  # Unified entry point
    pathex=[],
    binaries=binaries,
    datas=datas + [
        # ===== Gateway modules =====
        ('config', 'config'),
        ('core', 'core'),
        ('api', 'api'),
        ('db', 'db'),
        ('vm', 'vm'),
        ('mcp_servers', 'mcp_servers'),
        ('mcp_gateway', 'mcp_gateway'),
        ('executor', 'executor'),
        ('agent', 'agent'),
        ('skills', 'skills'),
        ('sse', 'sse'),
        ('process', 'process'),
        # ===== Services (Three-Task Architecture) =====
        ('services', 'services'),
        ('sdk', 'sdk'),
        # ===== Worker modules =====
        # worker/ 已合并到 services/executors/
        # ===== Utils =====
        ('utils', 'utils'),
        # ===== Entry points (for imports) =====
        ('main.py', '.'),
        ('mcp_main.py', '.'),
        ('monitor_main.py', '.'),
        ('launcher_main.py', '.'),
        ('collector_main.py', '.'),
        ('executor_main.py', '.'),
        ('health_main.py', '.'),
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
