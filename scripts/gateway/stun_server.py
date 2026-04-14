#!/usr/bin/env python3
"""
RFC 5389 STUN 服务器 — 自建 STUN，用于 P2P 打洞时获取客户端外网地址。

当 stun.l.google.com 被墙或 UDP 受限时，可部署到自有服务器（如 api.gradievo.com）。

Usage:
  python3 scripts/stun_server.py [--port 3478] [--host 0.0.0.0]

部署后需：
  1. 防火墙放行 UDP port（默认 3478）
  2. 客户端配置：在 novaic-app 中设置 STUN 服务器为 stun.api.gradievo.com:3478
"""
import argparse
import socket
import struct
import sys

MAGIC_COOKIE = b"\x21\x12\xa4\x42"


def build_binding_response(transaction_id: bytes, mapped_addr: tuple[str, int]) -> bytes:
    """RFC 5389: Binding Response + XOR-MAPPED-ADDRESS"""
    ip_str, port = mapped_addr
    ip_bytes = bytes(int(x) for x in ip_str.split("."))
    # XOR with magic cookie
    port_xor = port ^ 0x2112
    ip_xor = bytes(ip_bytes[i] ^ MAGIC_COOKIE[i] for i in range(4))

    # XOR-MAPPED-ADDRESS (0x0020): family(2) + port(2) + ip(4) = 8 bytes
    attr_value = struct.pack(">HH", 0x01, port_xor) + ip_xor  # family=IPv4
    attr_len = len(attr_value)
    attr = struct.pack(">HH", 0x0020, attr_len) + attr_value
    # 4-byte align
    if attr_len % 4:
        attr += b"\x00" * (4 - attr_len % 4)

    # Binding Response: 0x0101
    msg_len = len(attr)
    header = struct.pack(">HH", 0x0101, msg_len) + MAGIC_COOKIE + transaction_id
    return header + attr


def main():
    parser = argparse.ArgumentParser(description="RFC 5389 STUN server")
    parser.add_argument("--host", default="0.0.0.0", help="Bind host")
    parser.add_argument("--port", type=int, default=3478, help="UDP port")
    args = parser.parse_args()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((args.host, args.port))
    print(f"[STUN] Listening on {args.host}:{args.port} (UDP)", file=sys.stderr)

    while True:
        data, addr = sock.recvfrom(512)
        if len(data) < 20:
            continue
        msg_type = struct.unpack(">H", data[0:2])[0]
        if msg_type != 0x0001:  # Binding Request
            continue
        trans_id = data[8:20]
        resp = build_binding_response(trans_id, (addr[0], addr[1]))
        sock.sendto(resp, addr)


if __name__ == "__main__":
    main()
