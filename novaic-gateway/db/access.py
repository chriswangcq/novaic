"""
Database access helpers (centralized for novaic-gateway).
"""

from db.database import get_database


def get_db():
    return get_database()
