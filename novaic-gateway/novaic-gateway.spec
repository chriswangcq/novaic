# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
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
    ],
    hiddenimports=[
        'uvicorn.logging', 
        'uvicorn.protocols.http', 
        'uvicorn.protocols.http.auto', 
        'uvicorn.protocols.websockets', 
        'uvicorn.protocols.websockets.auto', 
        'uvicorn.lifespan.on', 
        'uvicorn.lifespan.off', 
        'httpx',
        'aiosqlite',
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
