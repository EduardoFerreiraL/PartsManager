"""Rotas de estatísticas e informações do banco"""
from fastapi import APIRouter, HTTPException
import pandas as pd
from database.connection import get_supabase_client, get_direct_connection, execute_direct_sql
from config.settings import TABLE_NAME, DIRECT_URL
from utils.retry import retry_with_backoff

router = APIRouter()
supabase = get_supabase_client()

@router.get("/health", summary="Verificar Status da API")
@retry_with_backoff(max_retries=3, base_delay=1)
def health_check():
    """Verifica o status da API e conexão com o banco de dados"""
    try:
        response = supabase.table(TABLE_NAME).select("part_number").limit(1).execute()
        
        direct_url_status = "not_configured"
        if DIRECT_URL:
            direct_conn = get_direct_connection()
            if direct_conn:
                direct_conn.close()
                direct_url_status = "available"
            else:
                direct_url_status = "error"
        
        return {
            "status": "healthy",
            "message": "API funcionando e conectada ao banco de dados",
            "timestamp": pd.Timestamp.now().isoformat(),
            "supabase_connection": "ok",
            "direct_url_status": direct_url_status,
            "direct_url_configured": bool(DIRECT_URL)
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "message": f"Erro na conexão com o banco: {str(e)}",
            "timestamp": pd.Timestamp.now().isoformat(),
            "supabase_connection": "error",
            "direct_url_status": "not_checked",
            "direct_url_configured": bool(DIRECT_URL)
        }

@router.get("/direct-connection", summary="Testar Conexão Direta")
def test_direct_connection():
    """Testa a conexão direta ao PostgreSQL usando DIRECT_URL"""
    if not DIRECT_URL:
        return {
            "status": "error",
            "message": "DIRECT_URL não configurado no arquivo .env",
            "direct_url_configured": False
        }
    
    try:
        conn = get_direct_connection()
        if not conn:
            return {
                "status": "error",
                "message": "Não foi possível estabelecer conexão direta",
                "direct_url_configured": True,
                "suggestion": "Verifique se psycopg2-binary está instalado: pip install psycopg2-binary"
            }
        
        with conn.cursor() as cursor:
            cursor.execute("SELECT version()")
            version = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "status": "success",
            "message": "Conexão direta funcionando perfeitamente",
            "direct_url_configured": True,
            "postgresql_version": version,
            "connection_type": "Direct PostgreSQL"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Erro na conexão direta: {str(e)}",
            "direct_url_configured": True,
            "error_details": str(e)
        }

@router.get("/direct-query", summary="Executar Consulta SQL Direta")
def execute_direct_query(sql: str = "SELECT COUNT(*) as total FROM pecas"):
    """Executa uma consulta SQL diretamente no PostgreSQL"""
    if not DIRECT_URL:
        raise HTTPException(status_code=400, detail="DIRECT_URL não configurado")
    
    sql_upper = sql.strip().upper()
    if not sql_upper.startswith('SELECT'):
        raise HTTPException(status_code=400, detail="Apenas consultas SELECT são permitidas")
    
    try:
        result = execute_direct_sql(sql)
        if result is None:
            raise HTTPException(status_code=500, detail="Erro ao executar consulta")
        
        return {
            "status": "success",
            "query": sql,
            "result": result,
            "total_rows": len(result) if isinstance(result, list) else 1
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao executar consulta: {str(e)}")

@router.get("/stats", summary="Estatísticas do Banco")
def get_stats():
    """Retorna estatísticas do banco de dados"""
    try:
        response = supabase.table(TABLE_NAME).select("part_number", count="exact").execute()
        total_pecas = response.count if response.count is not None else 0
        
        return {
            "status": "success",
            "total_pecas": total_pecas,
            "tabela": TABLE_NAME,
            "colunas": [
                "part_number",
                "chinese_description", 
                "description",
                "ncm",
                "date_of_creation",
                "review_date",
                "process",
                "machine"
            ],
            "timestamp": pd.Timestamp.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter estatísticas: {str(e)}")

@router.get("/table-structure", summary="Estrutura da Tabela")
def get_table_structure():
    """Retorna a estrutura real da tabela no Supabase"""
    try:
        response = supabase.table(TABLE_NAME).select("*").limit(1).execute()
        
        if response.data:
            first_row = response.data[0]
            columns = list(first_row.keys())
            
            return {
                "status": "success",
                "tabela": TABLE_NAME,
                "colunas_encontradas": columns,
                "total_colunas": len(columns),
                "exemplo_dados": first_row
            }
        else:
            return {
                "status": "success",
                "tabela": TABLE_NAME,
                "colunas_encontradas": [],
                "total_colunas": 0,
                "mensagem": "Tabela vazia - não foi possível determinar a estrutura"
            }
            
    except Exception as e:
        return {
            "status": "error",
            "tabela": TABLE_NAME,
            "erro": str(e),
            "dica": "Verifique se a tabela existe e se tem dados"
        }

