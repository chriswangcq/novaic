# -*- mode: python ; coding: utf-8 -*-

# NovAIC Backend - Unified Entry Point
# Uses main_novaic.py which handles all subcommands:
# - gateway, tools-server, queue-service
# - watchdog, task-worker, saga-worker, health, scheduler

a = Analysis(
    ['main_novaic.py'],  # Unified entry point
    pathex=[],
    binaries=[],
    datas=[
        ('config', 'config'),
        ('common', 'common'),
        ('gateway', 'gateway'),
        ('task_queue', 'task_queue'),
        ('queue_service', 'queue_service'),
        ('tools_server', 'tools_server'),
        ('mcp_client', 'mcp_client'),
        ('file_service', 'file_service'),
        ('tool_result_service', 'tool_result_service'),
        # Include individual main files for imports
        ('main_gateway.py', '.'),
        ('main_tools.py', '.'),
        ('main_saga.py', '.'),
        ('main_task.py', '.'),
        ('main_watchdog.py', '.'),
        ('main_health.py', '.'),
        ('main_runtime_orchestrator.py', '.'),
    ],
    hiddenimports=[
        # FastAPI and dependencies
        'fastapi',
        'fastapi.applications',
        'fastapi.routing',
        'fastapi.responses',
        'fastapi.staticfiles',
        'fastapi.middleware',
        'fastapi.middleware.cors',
        'pydantic',
        'pydantic.fields',
        # Uvicorn
        'uvicorn',
        'uvicorn.main',
        'uvicorn.lifespan.on', 
        'uvicorn.lifespan.off', 
        'uvicorn.lifespan', 
        'uvicorn.protocols.websockets.auto', 
        'uvicorn.protocols.websockets.wsproto_impl', 
        'uvicorn.protocols.websockets.websockets_impl', 
        'uvicorn.protocols.http.auto', 
        'uvicorn.protocols.http.h11_impl', 
        'uvicorn.protocols.http.httptools_impl', 
        'uvicorn.logging',
        # PIL
        'PIL', 
        'PIL.Image',
        # SQLite
        'sqlite3', 
        '_sqlite3',
        # AsyncSSH (SSH for qemu_ssh_exec)
        'asyncssh',
        # Paramiko (SSH)
        'paramiko',
        'paramiko.transport',
        'paramiko.sftp',
        'paramiko.sftp_client',
        'paramiko.ssh_exception',
        # Cryptography (for paramiko)
        'cryptography',
        'cryptography.hazmat.primitives.kdf.pbkdf2',
        'cryptography.hazmat.backends',
        # bcrypt (for paramiko)
        'bcrypt',
        # nacl (for paramiko)
        'nacl',
        'nacl.bindings',
        # httpx
        'httpx',
        'httpx._transports',
        'httpx._transports.default',
        # anyio
        'anyio',
        'anyio._backends._asyncio',
        # Starlette
        'starlette',
        'starlette.responses',
        'starlette.staticfiles',
        'starlette.routing',
        'starlette.middleware',
        # SSE
        'sse_starlette',
        'sse_starlette.sse',
        # Queue service
        'queue_service',
        'queue_service.main',
        # Task queue workers
        'task_queue.workers',
        'task_queue.workers.watchdog',
        'task_queue.workers.task_worker_sync',
        'task_queue.workers.health_worker_sync',
        'task_queue.workers.scheduler_worker_sync',
        'task_queue.handlers',
        # Tools server
        'tools_server',
        'tools_server.api',
        'tools_server.executor',
        'tools_server.tools',
        'tools_server.runtime_manager',
        # File service
        'file_service',
        'file_service.main',
        'file_service.routes',
        'file_service.storage',
        # Tool result service
        'tool_result_service',
        'tool_result_service.main',
        'tool_result_service.api',
        'tool_result_service.storage',
        'tool_result_service.normalizer',
        'tool_result_service.resolver',
        'tool_result_service.clients',
        # MCP client
        'mcp_client',
        'mcp_client.mcp_client',
        'mcp_client.registry',
        # Main modules
        'main_gateway',
        'main_tools',
        'main_saga',
        'main_runtime_orchestrator',
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
