# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import copy_metadata, collect_data_files, collect_submodules, collect_all

# Collect package metadata for packages that use importlib.metadata
datas = copy_metadata('fastmcp')
datas += copy_metadata('mcp')
datas += copy_metadata('aiohttp')
datas += copy_metadata('aiofiles')
datas += copy_metadata('httpx')
datas += copy_metadata('uvicorn')
datas += copy_metadata('fastapi')
datas += copy_metadata('starlette')
datas += copy_metadata('pydantic')
datas += copy_metadata('anyio')
datas += copy_metadata('websockets')

# Collect ALL files from fakeredis (includes model/, commands_mixins/, etc.)
fakeredis_datas, fakeredis_binaries, fakeredis_hiddenimports = collect_all('fakeredis')
datas += fakeredis_datas

# Collect ALL files from lupa (includes lua libraries)
lupa_datas, lupa_binaries, lupa_hiddenimports = collect_all('lupa')
datas += lupa_datas

# Collect ALL files from docket (FastMCP session management dependency)
docket_datas, docket_binaries, docket_hiddenimports = collect_all('docket')
datas += docket_datas

# Collect binaries
binaries = fakeredis_binaries + lupa_binaries + docket_binaries

# Collect hidden imports
extra_hiddenimports = fakeredis_hiddenimports + lupa_hiddenimports + docket_hiddenimports

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas + [
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
        ('worker', 'worker'),
        ('process', 'process'),
        ('master', 'master'),
        ('sse', 'sse'),
    ],
    hiddenimports=[
        # uvicorn
        'uvicorn.logging', 
        'uvicorn.protocols.http', 
        'uvicorn.protocols.http.auto', 
        'uvicorn.protocols.websockets', 
        'uvicorn.protocols.websockets.auto', 
        'uvicorn.lifespan.on', 
        'uvicorn.lifespan.off', 
        # http clients
        'httpx',
        'aiohttp',
        # async io
        'aiosqlite',
        'aiofiles',
        # fastapi & pydantic
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
        # fastmcp & mcp
        'fastmcp',
        'fastmcp.server',
        'fastmcp.server.server',
        'fastmcp.server.http',
        'mcp',
        'mcp.server',
        'mcp.server.streamable_http',
        'mcp.server.streamable_http_manager',
        # other
        'anyio',
        'anyio._backends',
        'anyio._backends._asyncio',
        'websockets',
        'websockets.legacy',
        'websockets.server',
        # lupa (lua bindings)
        'lupa',
        'lupa.lua51',
        'lupa.lua52',
        'lupa.lua53',
        'lupa.lua54',
        'lupa.luajit20',
        'lupa.luajit21',
    ] + extra_hiddenimports,
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
    name='novaic-gateway',
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
