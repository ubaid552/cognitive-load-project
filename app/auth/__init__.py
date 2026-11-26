"""
CogniLoad — Auth Package
Handles user authentication, session management, and database operations.
"""
from app.auth.db import init_db
from app.auth.auth_manager import AuthManager, auth

__all__ = ["AuthManager", "auth", "init_db"]
