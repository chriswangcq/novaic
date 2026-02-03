"""
Gateway SDK Exceptions
"""


class GatewayError(Exception):
    """Base exception for Gateway SDK errors."""
    
    def __init__(self, message: str, status_code: int = None, response: dict = None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class GatewayConnectionError(GatewayError):
    """Connection to Gateway failed."""
    pass


class GatewayTimeoutError(GatewayError):
    """Request to Gateway timed out."""
    pass


class GatewayNotFoundError(GatewayError):
    """Requested resource not found (404)."""
    pass


class GatewayConflictError(GatewayError):
    """Conflict error (409), e.g., idempotency key conflict."""
    pass


class GatewayValidationError(GatewayError):
    """Request validation error (400/422)."""
    pass


class GatewayServerError(GatewayError):
    """Server error (5xx)."""
    pass
