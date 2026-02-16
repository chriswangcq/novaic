"""
Backward-compatibility shim for task_queue.utils.image_storage.

Image storage implementation has been moved to common.utils.image_storage.
This module re-exports from there to keep existing task_queue imports working.

Prefer: from common.utils.image_storage import ImageStorage, get_image_storage, ...
"""

from common.utils.image_storage import (
    ImageStorage,
    get_image_storage,
    set_image_storage,
    save_image_if_large,
    is_image_url,
    resolve_image_to_base64,
)

__all__ = [
    "ImageStorage",
    "get_image_storage",
    "set_image_storage",
    "save_image_if_large",
    "is_image_url",
    "resolve_image_to_base64",
]
