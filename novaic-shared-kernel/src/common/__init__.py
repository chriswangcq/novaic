"""
Installable common namespace for multi-repo migration.

Round 002 now includes migrated core modules in this package.
Unmigrated modules still resolve through the fallback path during transition.
"""

from pathlib import Path
from pkgutil import extend_path

__path__ = extend_path(__path__, __name__)  # type: ignore[name-defined]

_repo_common = Path(__file__).resolve().parents[3] / "novaic-backend" / "common"
if _repo_common.exists():
    _repo_common_str = str(_repo_common)
    if _repo_common_str not in __path__:
        __path__.append(_repo_common_str)

__version__ = "0.1.0rc1"

from .exceptions import (  # noqa: E402
    BusinessError,
    ValidationError,
    NotFoundError,
    StateConflictError,
    ConfigurationError,
)

__all__ = [
    "BusinessError",
    "ValidationError",
    "NotFoundError",
    "StateConflictError",
    "ConfigurationError",
]
