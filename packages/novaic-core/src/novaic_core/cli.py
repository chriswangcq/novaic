"""
NovAIC CLI - Command line interface
"""

import argparse
import uvicorn

from .config import settings


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="NovAIC - Linux Desktop MCP Server"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # serve command
    serve_parser = subparsers.add_parser("serve", help="Start the MCP server")
    serve_parser.add_argument(
        "--host", 
        default=settings.host,
        help=f"Host to bind (default: {settings.host})"
    )
    serve_parser.add_argument(
        "--port", 
        type=int, 
        default=settings.port,
        help=f"Port to bind (default: {settings.port})"
    )
    serve_parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for development"
    )
    
    # version command
    subparsers.add_parser("version", help="Show version")
    
    # info command
    subparsers.add_parser("info", help="Show server info and available tools")
    
    args = parser.parse_args()
    
    if args.command == "serve" or args.command is None:
        # Default to serve
        host = getattr(args, 'host', settings.host)
        port = getattr(args, 'port', settings.port)
        reload = getattr(args, 'reload', False)
        
        print(f"""
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║   🐧 NovAIC - Linux Desktop MCP Server                     ║
║                                                               ║
║   MCP Endpoint: http://{host}:{port}/mcp                      ║
║   Health Check: http://{host}:{port}/health                   ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
        """)
        
        uvicorn.run(
            "novaic_core.main:app",
            host=host,
            port=port,
            reload=reload
        )
    
    elif args.command == "version":
        from . import __version__
        print(f"linux2mcp {__version__}")
    
    elif args.command == "info":
        from .main import MCP_TOOLS
        print(f"\nNovAIC - {len(MCP_TOOLS)} tools available:\n")
        
        categories = {}
        for tool in MCP_TOOLS:
            if tool.name.startswith("browser_"):
                cat = "Browser"
            elif tool.name in ["screenshot", "mouse", "keyboard"]:
                cat = "Desktop"
            elif tool.name in ["run_command", "run_python"]:
                cat = "Shell"
            elif tool.name in ["read_file", "write_file", "list_files", "file_info"]:
                cat = "Files"
            else:
                cat = "Windows"
            
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(tool)
        
        for cat, tools in categories.items():
            print(f"  {cat}:")
            for tool in tools:
                print(f"    - {tool.name}: {tool.description[:50]}...")
            print()


if __name__ == "__main__":
    main()

