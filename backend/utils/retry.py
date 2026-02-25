"""Decorator para retry com backoff exponencial"""
import time
import random
from functools import wraps

def retry_with_backoff(max_retries=3, base_delay=1, max_delay=60):
    """Decorator para retry com backoff exponencial"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    error_str = str(e)
                    # Verificar se é erro de socket não-bloqueante
                    if "10035" in error_str or "non-blocking socket" in error_str.lower():
                        if attempt == max_retries - 1:
                            raise e
                        
                        # Calcular delay com backoff exponencial + jitter
                        delay = min(base_delay * (2 ** attempt) + random.uniform(0, 1), max_delay)
                        print(f"⚠️ Erro de socket não-bloqueante (tentativa {attempt + 1}/{max_retries}). Aguardando {delay:.2f}s...")
                        time.sleep(delay)
                    else:
                        raise e
            return None
        return wrapper
    return decorator





