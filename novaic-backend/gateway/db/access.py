"""
Database access helpers (centralized).
"""

from .database import get_database


def get_db():
    return get_database()
