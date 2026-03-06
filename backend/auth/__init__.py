"""Módulo de autenticação"""
from auth.router import router
from auth.deps import get_current_user, require_permission

__all__ = ["router", "get_current_user", "require_permission"]
