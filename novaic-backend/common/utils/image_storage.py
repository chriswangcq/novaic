"""
Image Storage Service

Provides file-based storage for images to avoid storing large base64 data in the database.
Images are saved to disk and referenced by URL, which can be served via HTTP.

Usage:
    from common.utils.image_storage import ImageStorage

    storage = ImageStorage(base_dir="/path/to/images")

    # Save image and get URL
    url = storage.save_image(agent_id, base64_data)
    # Returns: "/api/images/agent_id/abc123.png"

    # Load image when needed (e.g., for LLM)
    base64_data = storage.load_image(url)
"""

import os
import base64
import hashlib
import time
import logging
from pathlib import Path
from typing import Optional, Tuple
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class ImageStorage:
    """
    File-based image storage service.

    Stores images as files and returns URL references that can be served via HTTP.
    Supports automatic cleanup of old images.
    """

    # Default threshold for storing as file (50KB)
    DEFAULT_SIZE_THRESHOLD = 50 * 1024

    # Maximum age for images before cleanup (7 days)
    DEFAULT_MAX_AGE_DAYS = 7

    def __init__(
        self,
        base_dir: Optional[str] = None,
        url_prefix: str = "/api/images",
        size_threshold: int = DEFAULT_SIZE_THRESHOLD,
    ):
        """
        Initialize image storage.

        Args:
            base_dir: Base directory for storing images. Defaults to ~/.novaic/images
            url_prefix: URL prefix for generated URLs
            size_threshold: Minimum size (bytes) to store as file instead of inline
        """
        if base_dir:
            self.base_dir = Path(base_dir)
        else:
            # Default to ~/.novaic/images or app data dir
            home = Path.home()
            self.base_dir = home / ".novaic" / "images"

        self.url_prefix = url_prefix.rstrip("/")
        self.size_threshold = size_threshold

        # Ensure base directory exists
        self.base_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"[ImageStorage] Initialized with base_dir={self.base_dir}")

    def _get_agent_dir(self, agent_id: str) -> Path:
        """Get or create agent-specific directory."""
        agent_dir = self.base_dir / agent_id
        agent_dir.mkdir(parents=True, exist_ok=True)
        return agent_dir

    def _generate_filename(self, data: bytes, extension: str = "png") -> str:
        """Generate unique filename based on content hash and timestamp."""
        # Use first 8 chars of MD5 hash + timestamp for uniqueness
        content_hash = hashlib.md5(data).hexdigest()[:8]
        timestamp = int(time.time() * 1000)
        return f"{timestamp}_{content_hash}.{extension}"

    def _detect_image_type(self, data: bytes) -> Tuple[str, str]:
        """
        Detect image type from binary data.

        Returns:
            Tuple of (extension, mime_type)
        """
        # PNG signature
        if data[:8] == b'\x89PNG\r\n\x1a\n':
            return "png", "image/png"
        # JPEG signature
        if data[:2] == b'\xff\xd8':
            return "jpg", "image/jpeg"
        # GIF signature
        if data[:6] in (b'GIF87a', b'GIF89a'):
            return "gif", "image/gif"
        # WebP signature
        if data[:4] == b'RIFF' and data[8:12] == b'WEBP':
            return "webp", "image/webp"
        # Default to PNG
        return "png", "image/png"

    def should_store_as_file(self, base64_data: str) -> bool:
        """
        Check if data should be stored as file based on size.

        Args:
            base64_data: Base64 encoded image data

        Returns:
            True if data exceeds threshold and should be stored as file
        """
        # Estimate decoded size (base64 is ~4/3 of original)
        estimated_size = len(base64_data) * 3 // 4
        return estimated_size > self.size_threshold

    def save_image(
        self,
        agent_id: str,
        base64_data: str,
        subagent_id: Optional[str] = None,
    ) -> str:
        """
        Save base64 image to file and return URL.

        Args:
            agent_id: Agent ID for organizing images
            base64_data: Base64 encoded image data (without data: prefix)
            subagent_id: Optional subagent ID for further organization

        Returns:
            URL path to access the image (e.g., "/api/images/agent_id/abc123.png")
        """
        try:
            # Remove data URL prefix if present
            if base64_data.startswith("data:"):
                # Format: data:image/png;base64,xxxxx
                base64_data = base64_data.split(",", 1)[1]

            # Decode base64
            image_data = base64.b64decode(base64_data)

            # Detect image type
            extension, _ = self._detect_image_type(image_data)

            # Generate filename
            filename = self._generate_filename(image_data, extension)

            # Get agent directory (optionally with subagent)
            if subagent_id:
                agent_dir = self._get_agent_dir(agent_id) / subagent_id
                agent_dir.mkdir(parents=True, exist_ok=True)
            else:
                agent_dir = self._get_agent_dir(agent_id)

            # Save file
            file_path = agent_dir / filename
            file_path.write_bytes(image_data)

            # Generate URL
            if subagent_id:
                url = f"{self.url_prefix}/{agent_id}/{subagent_id}/{filename}"
            else:
                url = f"{self.url_prefix}/{agent_id}/{filename}"

            logger.debug(f"[ImageStorage] Saved image: {file_path} -> {url}")
            return url

        except Exception as e:
            logger.error(f"[ImageStorage] Failed to save image: {e}")
            raise

    def load_image(self, url: str) -> Optional[str]:
        """
        Load image from URL and return as base64.

        Args:
            url: URL path (e.g., "/api/images/agent_id/abc123.png")

        Returns:
            Base64 encoded image data, or None if not found
        """
        try:
            # Parse URL to get file path
            if not url.startswith(self.url_prefix):
                logger.warning(f"[ImageStorage] Invalid URL prefix: {url}")
                return None

            relative_path = url[len(self.url_prefix):].lstrip("/")
            file_path = self.base_dir / relative_path

            if not file_path.exists():
                logger.warning(f"[ImageStorage] Image not found: {file_path}")
                return None

            # Read and encode
            image_data = file_path.read_bytes()
            return base64.b64encode(image_data).decode("utf-8")

        except Exception as e:
            logger.error(f"[ImageStorage] Failed to load image: {e}")
            return None

    def get_file_path(self, url: str) -> Optional[Path]:
        """
        Get the file system path for a URL.

        Args:
            url: URL path (e.g., "/api/images/agent_id/abc123.png")

        Returns:
            Path object, or None if invalid URL
        """
        if not url.startswith(self.url_prefix):
            return None

        relative_path = url[len(self.url_prefix):].lstrip("/")
        file_path = self.base_dir / relative_path

        # Security check: ensure path is within base_dir
        try:
            file_path.resolve().relative_to(self.base_dir.resolve())
            return file_path
        except ValueError:
            logger.warning(f"[ImageStorage] Path traversal attempt: {url}")
            return None

    def delete_image(self, url: str) -> bool:
        """
        Delete an image by URL.

        Args:
            url: URL path to the image

        Returns:
            True if deleted, False otherwise
        """
        file_path = self.get_file_path(url)
        if file_path and file_path.exists():
            try:
                file_path.unlink()
                logger.debug(f"[ImageStorage] Deleted: {file_path}")
                return True
            except Exception as e:
                logger.error(f"[ImageStorage] Failed to delete {file_path}: {e}")
        return False

    def cleanup_old_images(
        self,
        max_age_days: int = DEFAULT_MAX_AGE_DAYS,
        agent_id: Optional[str] = None,
    ) -> int:
        """
        Clean up images older than max_age_days.

        Args:
            max_age_days: Maximum age in days
            agent_id: Optional agent ID to limit cleanup scope

        Returns:
            Number of images deleted
        """
        deleted_count = 0
        cutoff_time = datetime.now() - timedelta(days=max_age_days)
        cutoff_timestamp = cutoff_time.timestamp()

        # Determine search directory
        search_dir = self._get_agent_dir(agent_id) if agent_id else self.base_dir

        for file_path in search_dir.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in (".png", ".jpg", ".jpeg", ".gif", ".webp"):
                try:
                    if file_path.stat().st_mtime < cutoff_timestamp:
                        file_path.unlink()
                        deleted_count += 1
                except Exception as e:
                    logger.warning(f"[ImageStorage] Failed to delete {file_path}: {e}")

        if deleted_count > 0:
            logger.info(f"[ImageStorage] Cleaned up {deleted_count} old images")

        return deleted_count

    def get_storage_stats(self, agent_id: Optional[str] = None) -> dict:
        """
        Get storage statistics.

        Args:
            agent_id: Optional agent ID to limit scope

        Returns:
            Dict with file_count, total_size_bytes, total_size_mb
        """
        search_dir = self._get_agent_dir(agent_id) if agent_id else self.base_dir

        file_count = 0
        total_size = 0

        for file_path in search_dir.rglob("*"):
            if file_path.is_file():
                file_count += 1
                total_size += file_path.stat().st_size

        return {
            "file_count": file_count,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
        }


# Global instance
_image_storage: Optional[ImageStorage] = None


def get_image_storage(base_dir: Optional[str] = None) -> ImageStorage:
    """
    Get the global ImageStorage instance.

    Args:
        base_dir: Optional base directory (only used on first call)

    Returns:
        ImageStorage instance
    """
    global _image_storage
    if _image_storage is None:
        _image_storage = ImageStorage(base_dir=base_dir)
    return _image_storage


def set_image_storage(storage: ImageStorage):
    """Set the global ImageStorage instance."""
    global _image_storage
    _image_storage = storage


# Utility functions for common operations

def save_image_if_large(
    agent_id: str,
    base64_data: str,
    subagent_id: Optional[str] = None,
    threshold: Optional[int] = None,
) -> str:
    """
    Save image to file if it exceeds threshold, otherwise return original data.

    Args:
        agent_id: Agent ID
        base64_data: Base64 encoded image data
        subagent_id: Optional subagent ID
        threshold: Size threshold in bytes (default: 50KB)

    Returns:
        URL if saved to file, or original base64_data if below threshold
    """
    storage = get_image_storage()

    if threshold is None:
        threshold = storage.size_threshold

    # Check if should store as file
    estimated_size = len(base64_data) * 3 // 4
    if estimated_size > threshold:
        return storage.save_image(agent_id, base64_data, subagent_id)

    return base64_data


def is_image_url(value: str) -> bool:
    """Check if a string is an image URL (not base64 data)."""
    if not isinstance(value, str):
        return False
    return value.startswith("/api/images/") or value.startswith("http://") or value.startswith("https://")


def resolve_image_to_base64(value: str) -> str:
    """
    Resolve image reference to base64 data.

    If value is a URL, load from file. If already base64, return as-is.

    Args:
        value: Image URL or base64 data

    Returns:
        Base64 encoded image data
    """
    if is_image_url(value):
        if value.startswith("/api/images/"):
            storage = get_image_storage()
            loaded = storage.load_image(value)
            if loaded:
                return loaded
            logger.warning(f"[ImageStorage] Could not load image from URL: {value}")

    # Return as-is (assume it's already base64)
    return value
