#!/usr/bin/env python3
"""
VSOCK to TCP Proxy for NovAIC MCP Server

This proxy runs inside the VM and:
1. Listens on VSOCK (AF_VSOCK) for connections from the host
2. Forwards requests to the local MCP server (localhost:8080)

Usage:
    python -m novaic_core.vsock_proxy

The proxy handles the MCP protocol (JSON-RPC over HTTP).
"""

import asyncio
import socket
import os
import sys
import signal
from typing import Optional

# VSOCK constants
VMADDR_CID_ANY = -1  # 0xFFFFFFFF
VMADDR_CID_HOST = 2

# Default configuration
VSOCK_PORT = int(os.getenv("NOVAIC_VSOCK_PORT", "8080"))
MCP_HOST = os.getenv("NOVAIC_MCP_HOST", "127.0.0.1")
MCP_PORT = int(os.getenv("NOVAIC_MCP_PORT", "8080"))

# Buffer size for data transfer
BUFFER_SIZE = 65536


class VSockProxy:
    """VSOCK to TCP proxy for MCP traffic"""
    
    def __init__(
        self,
        vsock_port: int = VSOCK_PORT,
        mcp_host: str = MCP_HOST,
        mcp_port: int = MCP_PORT,
    ):
        self.vsock_port = vsock_port
        self.mcp_host = mcp_host
        self.mcp_port = mcp_port
        self.running = False
        self._server_socket: Optional[socket.socket] = None
    
    def check_vsock_support(self) -> bool:
        """Check if VSOCK is supported on this system"""
        if not hasattr(socket, 'AF_VSOCK'):
            print("[VSockProxy] AF_VSOCK not supported on this system")
            return False
        return True
    
    async def handle_connection(
        self,
        vsock_reader: asyncio.StreamReader,
        vsock_writer: asyncio.StreamWriter,
    ):
        """Handle a single VSOCK connection by proxying to MCP server"""
        peer = vsock_writer.get_extra_info('peername')
        print(f"[VSockProxy] New connection from CID={peer[0] if peer else 'unknown'}")
        
        tcp_reader: Optional[asyncio.StreamReader] = None
        tcp_writer: Optional[asyncio.StreamWriter] = None
        
        try:
            # Connect to local MCP server
            tcp_reader, tcp_writer = await asyncio.open_connection(
                self.mcp_host, self.mcp_port
            )
            print(f"[VSockProxy] Connected to MCP server at {self.mcp_host}:{self.mcp_port}")
            
            # Bidirectional proxy
            async def forward(
                src: asyncio.StreamReader,
                dst: asyncio.StreamWriter,
                name: str,
            ):
                try:
                    while True:
                        data = await src.read(BUFFER_SIZE)
                        if not data:
                            break
                        dst.write(data)
                        await dst.drain()
                except Exception as e:
                    print(f"[VSockProxy] {name} error: {e}")
                finally:
                    try:
                        dst.close()
                        await dst.wait_closed()
                    except:
                        pass
            
            # Run both directions concurrently
            await asyncio.gather(
                forward(vsock_reader, tcp_writer, "vsock->tcp"),
                forward(tcp_reader, vsock_writer, "tcp->vsock"),
            )
            
        except ConnectionRefusedError:
            print(f"[VSockProxy] MCP server not available at {self.mcp_host}:{self.mcp_port}")
        except Exception as e:
            print(f"[VSockProxy] Error handling connection: {e}")
        finally:
            # Cleanup
            if tcp_writer:
                try:
                    tcp_writer.close()
                    await tcp_writer.wait_closed()
                except:
                    pass
            try:
                vsock_writer.close()
                await vsock_writer.wait_closed()
            except:
                pass
            print("[VSockProxy] Connection closed")
    
    async def start(self):
        """Start the VSOCK proxy server"""
        if not self.check_vsock_support():
            print("[VSockProxy] VSOCK not supported, exiting")
            return
        
        print(f"""
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║   🔌 NovAIC VSOCK Proxy                                       ║
║                                                               ║
║   VSOCK: port {self.vsock_port}                                           ║
║   Forwarding to: {self.mcp_host}:{self.mcp_port}                             ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
        """)
        
        # Create VSOCK server socket
        try:
            self._server_socket = socket.socket(socket.AF_VSOCK, socket.SOCK_STREAM)
            self._server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._server_socket.bind((VMADDR_CID_ANY, self.vsock_port))
            self._server_socket.listen(5)
            self._server_socket.setblocking(False)
            
            print(f"[VSockProxy] Listening on VSOCK port {self.vsock_port}")
            self.running = True
            
            loop = asyncio.get_event_loop()
            
            while self.running:
                try:
                    # Accept connection with timeout
                    conn, addr = await asyncio.wait_for(
                        loop.sock_accept(self._server_socket),
                        timeout=1.0
                    )
                    
                    # Wrap socket in StreamReader/Writer
                    reader, writer = await asyncio.open_connection(sock=conn)
                    
                    # Handle connection in background
                    asyncio.create_task(self.handle_connection(reader, writer))
                    
                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    if self.running:
                        print(f"[VSockProxy] Accept error: {e}")
                        await asyncio.sleep(1)
                        
        except Exception as e:
            print(f"[VSockProxy] Server error: {e}")
        finally:
            self.stop()
    
    def stop(self):
        """Stop the proxy server"""
        self.running = False
        if self._server_socket:
            try:
                self._server_socket.close()
            except:
                pass
            self._server_socket = None
        print("[VSockProxy] Stopped")


def main():
    """Main entry point"""
    proxy = VSockProxy()
    
    # Handle signals for graceful shutdown
    def signal_handler(sig, frame):
        print("\n[VSockProxy] Shutting down...")
        proxy.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Run the proxy
    try:
        asyncio.run(proxy.start())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
