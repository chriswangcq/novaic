"""
HTTP 客户端工厂

提供统一的 HTTP 客户端创建方法，自动处理代理配置：
- 本地地址 (localhost, 127.0.0.1, 内网 IP) 不走代理
- 外网地址 使用系统代理
"""

import httpx
from typing import Optional
from urllib.parse import urlparse

# 本地地址模式
LOCAL_PATTERNS = [
    'localhost',
    '127.0.0.1',
    '127.0.0.',
    '::1',
    '10.0.',
    '10.1.',
    '10.2.',
    '172.16.',
    '172.17.',
    '172.18.',
    '172.19.',
    '172.20.',
    '172.21.',
    '172.22.',
    '172.23.',
    '172.24.',
    '172.25.',
    '172.26.',
    '172.27.',
    '172.28.',
    '172.29.',
    '172.30.',
    '172.31.',
    '192.168.',
]


def is_local_url(url: str) -> bool:
    """判断 URL 是否为本地地址"""
    try:
        parsed = urlparse(url)
        host = parsed.hostname or ''
        return any(pattern in host for pattern in LOCAL_PATTERNS)
    except Exception:
        return any(pattern in url for pattern in LOCAL_PATTERNS)


def local_client(timeout: float = 30.0, **kwargs) -> httpx.AsyncClient:
    """
    创建用于本地服务的 HTTP 客户端（不使用代理）
    
    Args:
        timeout: 超时时间（秒）
        **kwargs: 其他 httpx.AsyncClient 参数
    
    Returns:
        配置好的 AsyncClient 实例
    """
    # 显式禁用代理
    transport = httpx.AsyncHTTPTransport(proxy=None)
    return httpx.AsyncClient(
        timeout=timeout,
        transport=transport,
        trust_env=False,  # 不读取环境变量代理
        **kwargs
    )


def external_client(timeout: float = 30.0, **kwargs) -> httpx.AsyncClient:
    """
    创建用于外网服务的 HTTP 客户端（使用系统代理）
    
    Args:
        timeout: 超时时间（秒）
        **kwargs: 其他 httpx.AsyncClient 参数
    
    Returns:
        配置好的 AsyncClient 实例
    """
    return httpx.AsyncClient(
        timeout=timeout,
        trust_env=True,  # 读取环境变量代理
        **kwargs
    )


def auto_client(url: str, timeout: float = 30.0, **kwargs) -> httpx.AsyncClient:
    """
    根据 URL 自动选择合适的客户端
    
    Args:
        url: 目标 URL
        timeout: 超时时间（秒）
        **kwargs: 其他 httpx.AsyncClient 参数
    
    Returns:
        配置好的 AsyncClient 实例
    """
    if is_local_url(url):
        return local_client(timeout=timeout, **kwargs)
    else:
        return external_client(timeout=timeout, **kwargs)


# 预配置的本地服务客户端参数
LOCAL_CLIENT_DEFAULTS = {
    'timeout': httpx.Timeout(connect=10.0, read=120.0, write=30.0, pool=10.0),
    'transport': httpx.AsyncHTTPTransport(proxy=None),
    'trust_env': False,
}
