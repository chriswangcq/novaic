#!/opt/novaic/venv/bin/python3
"""
NovAIC VMUSE Complete Server
完整的 VMUSE HTTP 服务器 - 不依赖 FastMCP
整合所有原始 VMUSE 工具：Browser, Desktop, Shell, Files, Windows, Context
"""

import os
import sys
import asyncio
import json
import logging
from aiohttp import web
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/vmuse_server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('vmuse_server')

# Import all tool modules (we'll create them)
from vmuse_tools.config import settings
from vmuse_tools.browser import get_browser_tools
from vmuse_tools.desktop import DesktopTools
from vmuse_tools.shell import ShellTools
from vmuse_tools.files import FileTools
from vmuse_tools.windows import WindowTools
from vmuse_tools.context import ContextTools


# ==================== API Handlers ====================

# Browser handlers
async def browser_navigate(request):
    """Navigate to URL"""
    try:
        data = await request.json()
        url = data.get('url')
        wait_until = data.get('wait_until', 'load')
        
        browser = get_browser_tools()
        result = await browser.navigate(url, wait_until)
        
        if result.get('success'):
            return web.json_response({
                'status': 'success',
                'url': result.get('url'),
                'title': result.get('title'),
                'data': result.get('structure')
            })
        else:
            return web.json_response({
                'status': 'error',
                'error': result.get('error')
            }, status=500)
    except Exception as e:
        logger.error(f"browser_navigate error: {e}", exc_info=True)
        return web.json_response({'status': 'error', 'error': str(e)}, status=500)


async def browser_click(request):
    """Click element"""
    try:
        data = await request.json()
        selector = data.get('selector')
        timeout = data.get('timeout', 5000)
        
        browser = get_browser_tools()
        result = await browser.click(selector, timeout)
        
        if result.get('success'):
            return web.json_response({
                'status': 'success',
                'url': result.get('url'),
                'data': result.get('new_tab')
            })
        else:
            return web.json_response({
                'status': 'error',
                'error': result.get('error')
            }, status=500)
    except Exception as e:
        logger.error(f"browser_click error: {e}", exc_info=True)
        return web.json_response({'status': 'error', 'error': str(e)}, status=500)


async def browser_type(request):
    """Type text into element"""
    try:
        data = await request.json()
        selector = data.get('selector')
        text = data.get('text')
        clear = data.get('clear', True)
        
        browser = get_browser_tools()
        result = await browser.type_text(selector, text, clear)
        
        if result.get('success'):
            return web.json_response({'status': 'success'})
        else:
            return web.json_response({
                'status': 'error',
                'error': result.get('error')
            }, status=500)
    except Exception as e:
        logger.error(f"browser_type error: {e}", exc_info=True)
        return web.json_response({'status': 'error', 'error': str(e)}, status=500)


async def browser_screenshot(request):
    """Take browser screenshot"""
    try:
        data = await request.json()
        full_page = data.get('full_page', False)
        
        browser = get_browser_tools()
        result = await browser.screenshot(full_page)
        
        if result.get('success'):
            return web.json_response({
                'status': 'success',
                'data': result.get('screenshot')
            })
        else:
            return web.json_response({
                'status': 'error',
                'error': result.get('error')
            }, status=500)
    except Exception as e:
        logger.error(f"browser_screenshot error: {e}", exc_info=True)
        return web.json_response({'status': 'error', 'error': str(e)}, status=500)


async def browser_scroll(request):
    """Scroll page"""
    try:
        data = await request.json()
        direction = data.get('direction')
        amount = data.get('amount', 500)
        selector = data.get('selector')
        
        browser = get_browser_tools()
        result = await browser.scroll(direction, amount, selector)
        
        if result.get('success'):
            return web.json_response({'status': 'success'})
        else:
            return web.json_response({
                'status': 'error',
                'error': result.get('error')
            }, status=500)
    except Exception as e:
        logger.error(f"browser_scroll error: {e}", exc_info=True)
        return web.json_response({'status': 'error', 'error': str(e)}, status=500)


async def browser_evaluate(request):
    """Execute JavaScript"""
    try:
        data = await request.json()
        script = data.get('script')
        
        browser = get_browser_tools()
        result = await browser.evaluate(script)
        
        if result.get('success'):
            return web.json_response({
                'status': 'success',
                'data': result.get('result')
            })
        else:
            return web.json_response({
                'status': 'error',
                'error': result.get('error')
            }, status=500)
    except Exception as e:
        logger.error(f"browser_evaluate error: {e}", exc_info=True)
        return web.json_response({'status': 'error', 'error': str(e)}, status=500)


# Desktop handlers
async def desktop_screenshot(request):
    """Take desktop screenshot"""
    try:
        data = await request.json()
        region = data.get('region')
        center = data.get('center')
        zoom_factor = data.get('zoom_factor')
        grid_density = data.get('grid_density')
        
        result = await DesktopTools.screenshot(
            region=region,
            center=center,
            zoom_factor=zoom_factor,
            grid_density=grid_density
        )
        
        if result.get('success'):
            return web.json_response({
                'status': 'success',
                'data': result.get('screenshot'),
                'width': result.get('width'),
                'height': result.get('height'),
                'hint': result.get('hint')
            })
        else:
            return web.json_response({
                'status': 'error',
                'error': result.get('error')
            }, status=500)
    except Exception as e:
        logger.error(f"desktop_screenshot error: {e}", exc_info=True)
        return web.json_response({'status': 'error', 'error': str(e)}, status=500)


async def desktop_mouse(request):
    """Mouse operations"""
    try:
        data = await request.json()
        action = data.get('action')
        x = data.get('x')
        y = data.get('y')
        zoom = data.get('zoom', 2.0)
        delta_x = data.get('delta_x')
        delta_y = data.get('delta_y')
        aim_id = data.get('aim_id')
        direction = data.get('direction')
        amount = data.get('amount', 3)
        
        result = await DesktopTools.mouse(
            action=action,
            x=x,
            y=y,
            zoom=zoom,
            delta_x=delta_x,
            delta_y=delta_y,
            aim_id=aim_id,
            direction=direction,
            amount=amount
        )
        
        if result.get('success'):
            response_data = {'status': 'success'}
            # Add all result fields
            for key, value in result.items():
                if key != 'success':
                    response_data[key] = value
            return web.json_response(response_data)
        else:
            return web.json_response({
                'status': 'error',
                'error': result.get('error')
            }, status=500)
    except Exception as e:
        logger.error(f"desktop_mouse error: {e}", exc_info=True)
        return web.json_response({'status': 'error', 'error': str(e)}, status=500)


async def desktop_keyboard(request):
    """Keyboard operations"""
    try:
        data = await request.json()
        action = data.get('action')
        text = data.get('text')
        keys = data.get('keys')
        
        result = await DesktopTools.keyboard(
            action=action,
            text=text,
            keys=keys
        )
        
        if result.get('success'):
            return web.json_response({'status': 'success'})
        else:
            return web.json_response({
                'status': 'error',
                'error': result.get('error')
            }, status=500)
    except Exception as e:
        logger.error(f"desktop_keyboard error: {e}", exc_info=True)
        return web.json_response({'status': 'error', 'error': str(e)}, status=500)


# Shell handlers
async def shell_run_command(request):
    """Execute shell command"""
    try:
        data = await request.json()
        command = data.get('command')
        cwd = data.get('cwd')
        timeout = data.get('timeout')
        visible = data.get('visible', False)
        
        result = await ShellTools.run_command(
            command=command,
            cwd=cwd,
            timeout=timeout,
            visible=visible
        )
        
        if result.get('success'):
            return web.json_response({
                'status': 'success',
                'data': {
                    'stdout': result.get('stdout'),
                    'stderr': result.get('stderr'),
                    'exit_code': result.get('exit_code')
                }
            })
        else:
            return web.json_response({
                'status': 'error',
                'error': result.get('error'),
                'data': {
                    'stdout': result.get('stdout', ''),
                    'stderr': result.get('stderr', ''),
                    'exit_code': result.get('exit_code')
                }
            }, status=500)
    except Exception as e:
        logger.error(f"shell_run_command error: {e}", exc_info=True)
        return web.json_response({'status': 'error', 'error': str(e)}, status=500)


# File handlers
async def file_read(request):
    """Read file"""
    try:
        data = await request.json()
        path = data.get('path')
        
        result = await FileTools.read_file(path)
        
        if result.get('success'):
            return web.json_response({
                'status': 'success',
                'data': result.get('content')
            })
        else:
            return web.json_response({
                'status': 'error',
                'error': result.get('error')
            }, status=500)
    except Exception as e:
        logger.error(f"file_read error: {e}", exc_info=True)
        return web.json_response({'status': 'error', 'error': str(e)}, status=500)


async def file_write(request):
    """Write file"""
    try:
        data = await request.json()
        path = data.get('path')
        content = data.get('content')
        
        result = await FileTools.write_file(path, content)
        
        if result.get('success'):
            return web.json_response({'status': 'success'})
        else:
            return web.json_response({
                'status': 'error',
                'error': result.get('error')
            }, status=500)
    except Exception as e:
        logger.error(f"file_write error: {e}", exc_info=True)
        return web.json_response({'status': 'error', 'error': str(e)}, status=500)


async def file_list(request):
    """List directory"""
    try:
        data = await request.json()
        path = data.get('path', '.')
        
        result = await FileTools.list_files(path)
        
        if result.get('success'):
            return web.json_response({
                'status': 'success',
                'data': result.get('entries')
            })
        else:
            return web.json_response({
                'status': 'error',
                'error': result.get('error')
            }, status=500)
    except Exception as e:
        logger.error(f"file_list error: {e}", exc_info=True)
        return web.json_response({'status': 'error', 'error': str(e)}, status=500)


# Health check
async def health_check(request):
    """Health check endpoint"""
    return web.json_response({
        'status': 'ok',
        'service': 'vmuse-complete-server',
        'version': '1.0.0'
    })


# ==================== Main Application ====================

def create_app():
    """Create aiohttp application"""
    app = web.Application()
    
    # Browser routes
    app.router.add_post('/api/browser/navigate', browser_navigate)
    app.router.add_post('/api/browser/click', browser_click)
    app.router.add_post('/api/browser/type', browser_type)
    app.router.add_post('/api/browser/screenshot', browser_screenshot)
    app.router.add_post('/api/browser/scroll', browser_scroll)
    app.router.add_post('/api/browser/evaluate', browser_evaluate)
    
    # Desktop routes
    app.router.add_post('/api/desktop/screenshot', desktop_screenshot)
    app.router.add_post('/api/desktop/mouse', desktop_mouse)
    app.router.add_post('/api/desktop/keyboard', desktop_keyboard)
    
    # Shell routes
    app.router.add_post('/api/shell/command', shell_run_command)
    
    # File routes
    app.router.add_post('/api/file/read', file_read)
    app.router.add_post('/api/file/write', file_write)
    app.router.add_post('/api/file/list', file_list)
    
    # Health check
    app.router.add_get('/health', health_check)
    
    return app


def main():
    """Main entry point"""
    logger.info("Starting NovAIC VMUSE Complete Server...")
    logger.info(f"Listening on {settings.host}:{settings.port}")
    
    # Ensure work directory exists
    os.makedirs(settings.work_dir, exist_ok=True)
    
    app = create_app()
    web.run_app(app, host=settings.host, port=settings.port, access_log=logger)


if __name__ == '__main__':
    main()
