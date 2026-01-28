#!/usr/bin/env python3
"""
Virtio-Serial to TCP Proxy for NovAIC MCP Server

This proxy runs inside the VM and:
1. Listens on virtio-serial port (/dev/virtio-ports/mcp) for connections from the host
2. Forwards requests to the local MCP server (localhost:8080)

Usage:
    python -m novaic_core.virtio_proxy

The proxy handles the MCP protocol (JSON-RPC over HTTP).
Works on both macOS (HVF) and Linux (KVM).
"""

import asyncio
import os
import sys
import signal
from pathlib import Path
from typing import Optional

# Default configuration
VIRTIO_PORT_PATH = os.getenv("NOVAIC_VIRTIO_PORT", "/dev/virtio-ports/mcp")
MCP_HOST = os.getenv("NOVAIC_MCP_HOST", "127.0.0.1")
MCP_PORT = int(os.getenv("NOVAIC_MCP_PORT", "8080"))

# Buffer size for data transfer
BUFFER_SIZE = 65536


class VirtioSerialProxy:
    """Virtio-serial to TCP proxy for MCP traffic"""
    
    def __init__(
        self,
        virtio_port: str = VIRTIO_PORT_PATH,
        mcp_host: str = MCP_HOST,
        mcp_port: int = MCP_PORT,
    ):
        self.virtio_port = virtio_port
        self.mcp_host = mcp_host
        self.mcp_port = mcp_port
        self.running = False
        self._virtio_fd: Optional[int] = None
    
    def check_virtio_port(self) -> bool:
        """Check if virtio port exists"""
        if not Path(self.virtio_port).exists():
            print(f"[VirtioProxy] Port not found: {self.virtio_port}")
            print("[VirtioProxy] Waiting for virtio-serial device...")
            return False
        return True
    
    async def handle_connection(self, virtio_reader, virtio_writer):
        """Handle connection by proxying to MCP server"""
        print("[VirtioProxy] New connection from host")
        
        tcp_reader: Optional[asyncio.StreamReader] = None
        tcp_writer: Optional[asyncio.StreamWriter] = None
        
        try:
            # Connect to local MCP server
            tcp_reader, tcp_writer = await asyncio.open_connection(
                self.mcp_host, self.mcp_port
            )
            print(f"[VirtioProxy] Connected to MCP server at {self.mcp_host}:{self.mcp_port}")
            
            # Bidirectional proxy
            async def forward(src, dst, name: str):
                try:
                    while True:
                        data = await src.read(BUFFER_SIZE)
                        if not data:
                            break
                        dst.write(data)
                        await dst.drain()
                except Exception as e:
                    print(f"[VirtioProxy] {name} error: {e}")
                finally:
                    try:
                        dst.close()
                        await dst.wait_closed()
                    except:
                        pass
            
            # Run both directions concurrently
            await asyncio.gather(
                forward(virtio_reader, tcp_writer, "virtio->tcp"),
                forward(tcp_reader, virtio_writer, "tcp->virtio"),
            )
            
        except ConnectionRefusedError:
            print(f"[VirtioProxy] MCP server not available at {self.mcp_host}:{self.mcp_port}")
        except Exception as e:
            print(f"[VirtioProxy] Error handling connection: {e}")
        finally:
            if tcp_writer:
                try:
                    tcp_writer.close()
                    await tcp_writer.wait_closed()
                except:
                    pass
            print("[VirtioProxy] Connection closed")
    
    async def start(self):
        """Start the virtio-serial proxy"""
        print(f"""
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║   🔌 NovAIC Virtio-Serial Proxy                               ║
║                                                               ║
║   Port: {self.virtio_port}                        ║
║   Forwarding to: {self.mcp_host}:{self.mcp_port}                             ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
        """)
        
        # Wait for virtio port to appear
        while not self.check_virtio_port():
            await asyncio.sleep(2)
        
        self.running = True
        print(f"[VirtioProxy] Opening {self.virtio_port}")
        
        try:
            # Open virtio-serial port as a file
            # Use asyncio to handle the character device
            reader, writer = await asyncio.open_connection(
                path=self.virtio_port  # This won't work directly...
            )
        except TypeError:
            # asyncio.open_connection doesn't support path for char devices
            # Use a different approach: open as file descriptor
            pass
        
        # For virtio-serial, we need to use file I/O
        # The device is a character device, we can read/write directly
        try:
            # Open in read-write binary mode
            self._virtio_fd = os.open(self.virtio_port, os.O_RDWR | os.O_NONBLOCK)
            
            loop = asyncio.get_event_loop()
            
            # Create async streams from fd
            reader = asyncio.StreamReader()
            read_protocol = asyncio.StreamReaderProtocol(reader)
            read_transport, _ = await loop.create_connection(
                lambda: read_protocol,
                sock=self._create_socket_from_fd(self._virtio_fd)
            )
            
            writer_transport, writer_protocol = await loop.create_connection(
                asyncio.Protocol,
                sock=self._create_socket_from_fd(self._virtio_fd)
            )
            writer = asyncio.StreamWriter(writer_transport, writer_protocol, reader, loop)
            
            await self.handle_connection(reader, writer)
            
        except Exception as e:
            print(f"[VirtioProxy] Error: {e}")
            # Fallback: simple blocking I/O in thread
            await self._run_blocking_proxy()
        finally:
            self.stop()
    
    async def _run_blocking_proxy(self):
        """Fallback: run proxy with blocking I/O in executor"""
        import concurrent.futures
        
        loop = asyncio.get_event_loop()
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)
        
        def proxy_thread():
            """Blocking proxy thread"""
            import select
            
            try:
                virtio_fd = os.open(self.virtio_port, os.O_RDWR)
                
                while self.running:
                    # Wait for data from virtio port
                    readable, _, _ = select.select([virtio_fd], [], [], 1.0)
                    
                    if virtio_fd in readable:
                        # Read request from host
                        data = os.read(virtio_fd, BUFFER_SIZE)
                        if data:
                            # Forward to MCP server
                            import socket
                            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                                sock.connect((self.mcp_host, self.mcp_port))
                                sock.sendall(data)
                                
                                # Read response
                                response = b""
                                while True:
                                    chunk = sock.recv(BUFFER_SIZE)
                                    if not chunk:
                                        break
                                    response += chunk
                                    # Check for complete HTTP response
                                    if b"\r\n\r\n" in response:
                                        header_end = response.find(b"\r\n\r\n")
                                        headers = response[:header_end].decode('utf-8', errors='ignore')
                                        body_start = header_end + 4
                                        
                                        content_length = 0
                                        for line in headers.split("\r\n"):
                                            if line.lower().startswith("content-length:"):
                                                content_length = int(line.split(":")[1].strip())
                                                break
                                        
                                        if len(response) >= body_start + content_length:
                                            break
                                
                                # Send response back to host
                                os.write(virtio_fd, response)
                                
            except Exception as e:
                print(f"[VirtioProxy] Thread error: {e}")
            finally:
                try:
                    os.close(virtio_fd)
                except:
                    pass
        
        await loop.run_in_executor(executor, proxy_thread)
    
    def stop(self):
        """Stop the proxy"""
        self.running = False
        if self._virtio_fd is not None:
            try:
                os.close(self._virtio_fd)
            except:
                pass
            self._virtio_fd = None
        print("[VirtioProxy] Stopped")


def main():
    """Main entry point"""
    proxy = VirtioSerialProxy()
    
    # Handle signals for graceful shutdown
    def signal_handler(sig, frame):
        print("\n[VirtioProxy] Shutting down...")
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
