"""Utilitários do sistema"""
from .retry import retry_with_backoff
from .network import get_local_ip

__all__ = [
    'retry_with_backoff',
    'get_local_ip'
]





