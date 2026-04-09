"""Conexões com banco de dados"""
from typing import Optional

import httpx
from httpx import HTTPTransport, Limits, Timeout
from supabase import create_client, Client
from supabase.lib.client_options import SyncClientOptions

from config.settings import SUPABASE_URL, SUPABASE_KEY, DIRECT_URL

_supabase_client: Optional[Client] = None
_httpx_client: Optional[httpx.Client] = None


def _build_httpx_client() -> httpx.Client:
    """Cliente HTTP estável para PostgREST: HTTP/1.1, retries e poucos keep-alive (evita RemoteProtocolError em HTTP/2)."""
    transport = HTTPTransport(
        http1=True,
        http2=False,
        retries=3,
        limits=Limits(
            max_connections=100,
            max_keepalive_connections=1,
            keepalive_expiry=30.0,
        ),
    )
    return httpx.Client(transport=transport, timeout=Timeout(120.0))


def get_supabase_client() -> Client:
    """Retorna o cliente Supabase (singleton)."""
    global _supabase_client, _httpx_client
    if _supabase_client is None:
        _httpx_client = _build_httpx_client()
        options = SyncClientOptions(httpx_client=_httpx_client)
        _supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY, options=options)
    return _supabase_client


def reset_supabase_client() -> None:
    """Fecha o cliente HTTP e força recriação na próxima chamada (útil após falhas transitórias)."""
    global _supabase_client, _httpx_client
    _supabase_client = None
    if _httpx_client is not None:
        try:
            _httpx_client.close()
        except Exception:
            pass
        _httpx_client = None


def get_direct_connection():
    """Retorna uma conexão direta ao PostgreSQL usando DIRECT_URL"""
    if not DIRECT_URL:
        return None

    try:
        import psycopg2
        return psycopg2.connect(DIRECT_URL)
    except ImportError:
        print("⚠️  psycopg2 não instalado. Para usar DIRECT_URL, instale: pip install psycopg2-binary")
        return None
    except Exception as e:
        print(f"⚠️  Erro ao conectar via DIRECT_URL: {e}")
        return None


def execute_direct_sql(query, params=None):
    """Executa uma consulta SQL diretamente no PostgreSQL usando DIRECT_URL"""
    conn = get_direct_connection()
    if not conn:
        return None

    try:
        with conn.cursor() as cursor:
            cursor.execute(query, params)
            if query.strip().upper().startswith('SELECT'):
                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()
                return [dict(zip(columns, row)) for row in rows]
            else:
                conn.commit()
                return {"affected_rows": cursor.rowcount}
    except Exception as e:
        print(f"❌ Erro ao executar SQL direto: {e}")
        return None
    finally:
        conn.close()
