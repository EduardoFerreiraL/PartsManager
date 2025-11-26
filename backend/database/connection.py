"""Conexões com banco de dados"""
from supabase import create_client, Client
from config.settings import SUPABASE_URL, SUPABASE_KEY, DIRECT_URL

# Conecta ao Supabase com as credenciais
_supabase_client: Client = None

def get_supabase_client() -> Client:
    """Retorna o cliente Supabase (singleton)"""
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
    return _supabase_client

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

