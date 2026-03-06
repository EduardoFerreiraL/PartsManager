"""Rotas administrativas e de debug"""
from fastapi import APIRouter, HTTPException, Depends
import os
import pandas as pd
from datetime import datetime
from database.connection import get_supabase_client, get_direct_connection
from config.settings import TABLE_NAME, DIRECT_URL
from services.validation_service import ValidationService
from routes import stats
from auth.deps import get_current_user

router = APIRouter()
supabase = get_supabase_client()
validation_service = ValidationService()

@router.get("/test-model-compatibility", summary="Testar Compatibilidade do Modelo")
def test_model_compatibility(current_user: dict = Depends(get_current_user)):
    """Testa se o sistema está pronto para receber o arquivo model.xlsx atualizado"""
    try:
        if not os.path.exists("model.xlsx"):
            return {
                "status": "error",
                "message": "Arquivo model.xlsx não encontrado",
                "ready": False
            }
        
        df = pd.read_excel("model.xlsx", engine='openpyxl')
        
        table_structure = stats.get_table_structure_impl()
        if table_structure["status"] == "success" and table_structure["colunas_encontradas"]:
            available_columns = table_structure["colunas_encontradas"]
        else:
            available_columns = [
                "part_number", "chinese_description", "description", "ncm", "origin",
                "date_of_creation", "review_date", "requester", "machine", "Situation_OSGT"
            ]
        
        model_columns = [col.lower() for col in df.columns]
        compatible_columns = [col for col in model_columns if col in [ac.lower() for ac in available_columns]]
        incompatible_columns = [col for col in model_columns if col not in [ac.lower() for ac in available_columns]]
        
        required_fields = ['part_number', 'description', 'ncm']
        missing_required = [field for field in required_fields if field not in model_columns]
        
        sample_data = df.head(2).to_dict('records')
        validation_errors, validation_warnings = validation_service.validate_excel_data(sample_data)
        
        return {
            "status": "success",
            "ready": len(missing_required) == 0 and len(validation_errors) == 0,
            "message": "Sistema pronto para receber o arquivo model.xlsx atualizado" if len(missing_required) == 0 and len(validation_errors) == 0 else "Sistema precisa de ajustes",
            "details": {
                "model_columns": list(df.columns),
                "available_columns": available_columns,
                "compatible_columns": compatible_columns,
                "incompatible_columns": incompatible_columns,
                "missing_required": missing_required,
                "validation_errors": len(validation_errors),
                "validation_warnings": len(validation_warnings),
                "sample_data_rows": len(sample_data)
            },
            "recommendations": [
                "✅ Arquivo model.xlsx encontrado" if os.path.exists("model.xlsx") else "❌ Arquivo model.xlsx não encontrado",
                "✅ Colunas compatíveis" if len(compatible_columns) > 0 else "❌ Nenhuma coluna compatível",
                "✅ Campos obrigatórios presentes" if len(missing_required) == 0 else f"❌ Campos obrigatórios ausentes: {missing_required}",
                "✅ Validação passou" if len(validation_errors) == 0 else f"❌ {len(validation_errors)} erros de validação encontrados"
            ]
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Erro ao testar compatibilidade: {str(e)}",
            "ready": False,
            "error_details": str(e)
        }

@router.get("/download-model", summary="Download da Planilha Modelo")
def download_model_excel(current_user: dict = Depends(get_current_user)):
    """Endpoint para download da planilha modelo"""
    try:
        model_path = "model.xlsx"
        
        if not os.path.exists(model_path):
            raise HTTPException(status_code=404, detail="Arquivo modelo não encontrado")
        
        with open(model_path, "rb") as file:
            file_content = file.read()
        
        # Gerar nome do arquivo com data e hora
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"modelo_pecas_{timestamp}.xlsx"
        
        from fastapi.responses import Response
        return Response(
            content=file_content,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Length": str(len(file_content))
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao baixar arquivo modelo: {str(e)}")

@router.get("/check-table", summary="Verificar/Criar Tabela")
def check_and_create_table(current_user: dict = Depends(get_current_user)):
    """Verifica se a tabela existe e cria se necessário"""
    try:
        response = supabase.table(TABLE_NAME).select("*").limit(1).execute()
        
        return {
            "status": "success",
            "message": "Tabela existe e está acessível",
            "tabela": TABLE_NAME,
            "existe": True
        }
        
    except Exception as e:
        error_msg = str(e)
        
        if "relation" in error_msg.lower() and "does not exist" in error_msg.lower():
            create_table_sql = f"""
            CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
                id SERIAL PRIMARY KEY,
                part_number VARCHAR(255),
                chinese_description TEXT,
                description TEXT,
                ncm VARCHAR(100),
                date_of_creation DATE,
                review_date DATE,
                process VARCHAR(255),
                machine VARCHAR(255),
                created_at TIMESTAMP DEFAULT NOW()
            );
            """
            
            return {
                "status": "warning",
                "message": "Tabela não existe. Crie manualmente no Supabase com a estrutura:",
                "tabela": TABLE_NAME,
                "existe": False,
                "sql_para_criar": create_table_sql,
                "instrucoes": [
                    "1. Acesse o painel do Supabase",
                    "2. Vá para SQL Editor",
                    "3. Execute o SQL fornecido acima",
                    "4. Ou crie a tabela via interface gráfica"
                ]
            }
        
        return {
            "status": "error",
            "message": "Erro ao verificar tabela",
            "tabela": TABLE_NAME,
            "existe": False,
            "erro": error_msg
        }

@router.post("/optimize-database", summary="Otimizar Banco de Dados")
def optimize_database(current_user: dict = Depends(get_current_user)):
    """Cria índices no banco de dados para otimizar consultas com grandes volumes"""
    try:
        indexes_to_create = [
            {
                "name": "idx_pecas_part_number",
                "sql": "CREATE INDEX IF NOT EXISTS idx_pecas_part_number ON pecas(part_number);",
                "description": "Índice para busca rápida por Part Number"
            },
            {
                "name": "idx_pecas_ncm", 
                "sql": "CREATE INDEX IF NOT EXISTS idx_pecas_ncm ON pecas(ncm);",
                "description": "Índice para busca rápida por NCM"
            },
            {
                "name": "idx_pecas_date_creation",
                "sql": "CREATE INDEX IF NOT EXISTS idx_pecas_date_creation ON pecas(date_of_creation);",
                "description": "Índice para ordenação por data de criação"
            },
            {
                "name": "idx_pecas_description",
                "sql": "CREATE INDEX IF NOT EXISTS idx_pecas_description ON pecas USING gin(to_tsvector('portuguese', description));",
                "description": "Índice de texto completo para descrição"
            },
            {
                "name": "idx_pecas_chinese_description",
                "sql": "CREATE INDEX IF NOT EXISTS idx_pecas_chinese_description ON pecas USING gin(to_tsvector('simple', chinese_description));",
                "description": "Índice de texto completo para descrição chinesa"
            },
            {
                "name": "idx_pecas_origin",
                "sql": "CREATE INDEX IF NOT EXISTS idx_pecas_origin ON pecas(origin);",
                "description": "Índice para busca por origem"
            },
            {
                "name": "idx_pecas_machine",
                "sql": "CREATE INDEX IF NOT EXISTS idx_pecas_machine ON pecas(machine);",
                "description": "Índice para busca por máquina"
            }
        ]
        
        results = []
        
        if DIRECT_URL:
            conn = get_direct_connection()
            if conn:
                try:
                    with conn.cursor() as cursor:
                        for index_info in indexes_to_create:
                            try:
                                cursor.execute(index_info["sql"])
                                results.append({
                                    "index": index_info["name"],
                                    "status": "created",
                                    "description": index_info["description"]
                                })
                            except Exception as e:
                                results.append({
                                    "index": index_info["name"],
                                    "status": "error",
                                    "description": index_info["description"],
                                    "error": str(e)
                                })
                    conn.commit()
                    conn.close()
                    
                    return {
                        "status": "success",
                        "message": "Otimização do banco de dados concluída",
                        "indexes_created": results,
                        "total_indexes": len(indexes_to_create),
                        "successful_indexes": len([r for r in results if r["status"] == "created"])
                    }
                except Exception as e:
                    conn.close()
                    raise e
        
        return {
            "status": "info",
            "message": "Conexão direta não disponível. Execute os comandos SQL manualmente no Supabase:",
            "instructions": [
                "1. Acesse o painel do Supabase",
                "2. Vá para SQL Editor", 
                "3. Execute os comandos SQL abaixo:"
            ],
            "sql_commands": [idx["sql"] for idx in indexes_to_create],
            "indexes_info": indexes_to_create
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Erro ao otimizar banco de dados: {str(e)}",
            "error_details": str(e)
        }

@router.get("/database-performance", summary="Verificar Performance do Banco")
def check_database_performance(current_user: dict = Depends(get_current_user)):
    """Verifica a performance atual do banco de dados"""
    try:
        if DIRECT_URL:
            conn = get_direct_connection()
            if conn:
                try:
                    with conn.cursor() as cursor:
                        cursor.execute("""
                            SELECT 
                                indexname, 
                                tablename, 
                                indexdef 
                            FROM pg_indexes 
                            WHERE tablename = 'pecas' 
                            ORDER BY indexname;
                        """)
                        indexes = cursor.fetchall()
                        
                        cursor.execute("""
                            SELECT 
                                schemaname,
                                tablename,
                                attname,
                                n_distinct,
                                correlation
                            FROM pg_stats 
                            WHERE tablename = 'pecas'
                            ORDER BY attname;
                        """)
                        stats = cursor.fetchall()
                        
                        cursor.execute("SELECT COUNT(*) FROM pecas;")
                        total_records = cursor.fetchone()[0]
                        
                        conn.close()
                        
                        return {
                            "status": "success",
                            "total_records": total_records,
                            "existing_indexes": [
                                {
                                    "name": idx[0],
                                    "table": idx[1], 
                                    "definition": idx[2]
                                } for idx in indexes
                            ],
                            "table_statistics": [
                                {
                                    "column": stat[2],
                                    "distinct_values": stat[3],
                                    "correlation": stat[4]
                                } for stat in stats
                            ],
                            "performance_recommendations": [
                                "✅ Índices existentes encontrados" if indexes else "⚠️ Nenhum índice encontrado",
                                f"📊 Total de registros: {total_records:,}",
                                "💡 Considere executar /api/optimize-database para melhorar performance" if total_records > 10000 else "✅ Performance adequada para volume atual"
                            ]
                        }
                except Exception as e:
                    conn.close()
                    raise e
        
        response = supabase.table(TABLE_NAME).select("id", count="exact").execute()
        total_records = response.count if response.count is not None else 0
        
        return {
            "status": "info",
            "total_records": total_records,
            "message": "Conexão direta não disponível para análise detalhada",
            "recommendations": [
                f"📊 Total de registros: {total_records:,}",
                "💡 Configure DIRECT_URL para análise detalhada de performance",
                "💡 Considere executar /api/optimize-database para grandes volumes" if total_records > 10000 else "✅ Volume atual adequado"
            ]
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Erro ao verificar performance: {str(e)}",
            "error_details": str(e)
        }

@router.get("/debug-structure", summary="Debug da Estrutura")
def debug_structure(current_user: dict = Depends(get_current_user)):
    """Endpoint de debug para verificar a estrutura da tabela"""
    try:
        print("🔍 Iniciando debug da estrutura...")
        
        response = supabase.table(TABLE_NAME).select("*").limit(1).execute()
        
        print(f"📊 Resposta do Supabase: {response}")
        print(f"📊 Dados: {response.data}")
        
        if response.data:
            first_row = response.data[0]
            columns = list(first_row.keys())
            
            print(f"📋 Colunas encontradas: {columns}")
            
            return {
                "status": "success",
                "tabela": TABLE_NAME,
                "colunas_encontradas": columns,
                "total_colunas": len(columns),
                "exemplo_dados": first_row,
                "debug_info": {
                    "response_type": str(type(response)),
                    "data_type": str(type(response.data)),
                    "data_length": len(response.data) if response.data else 0
                }
            }
        else:
            return {
                "status": "success",
                "tabela": TABLE_NAME,
                "colunas_encontradas": [],
                "total_colunas": 0,
                "mensagem": "Tabela vazia - não foi possível determinar a estrutura",
                "debug_info": {
                    "response_type": str(type(response)),
                    "data_type": str(type(response.data)),
                    "data_length": len(response.data) if response.data else 0
                }
            }
            
    except Exception as e:
        print(f"❌ Erro no debug: {e}")
        return {
            "status": "error",
            "tabela": TABLE_NAME,
            "erro": str(e),
            "debug_info": {
                "exception_type": str(type(e)),
                "exception_args": str(e.args)
            }
        }

@router.post("/reload-schema-cache", summary="Recarregar Cache de Esquema")
def reload_schema_cache(current_user: dict = Depends(get_current_user)):
    """Recarrega o cache de esquema do PostgREST para resolver erro PGRST205"""
    try:
        if DIRECT_URL:
            conn = get_direct_connection()
            if conn:
                try:
                    with conn.cursor() as cursor:
                        cursor.execute("NOTIFY pgrst, 'reload schema';")
                        conn.commit()
                        conn.close()
                        
                        return {
                            "status": "success",
                            "message": "Cache de esquema recarregado com sucesso",
                            "metodo": "NOTIFY pgrst",
                            "instrucoes": [
                                "O cache foi recarregado usando NOTIFY",
                                "Tente acessar a aplicação novamente",
                                "Se o problema persistir, aguarde alguns minutos"
                            ]
                        }
                except Exception as e:
                    conn.close()
                    raise e
        
        return {
            "status": "warning",
            "message": "Não foi possível recarregar automaticamente. Execute manualmente:",
            "metodo": "manual",
            "instrucoes": [
                "1. Acesse o painel do Supabase",
                "2. Vá para SQL Editor",
                "3. Execute: NOTIFY pgrst, 'reload schema';",
                "4. Ou aguarde alguns minutos para o cache atualizar automaticamente"
            ],
            "sql_para_executar": "NOTIFY pgrst, 'reload schema';"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": "Erro ao recarregar cache de esquema",
            "erro": str(e),
            "instrucoes_alternativas": [
                "1. Aguarde 5-10 minutos para o cache atualizar automaticamente",
                "2. Reinicie o servidor Supabase se possível",
                "3. Execute manualmente no SQL Editor: NOTIFY pgrst, 'reload schema';"
            ]
        }

@router.post("/migrate-position-field", summary="Migrar Campo Position")
def migrate_position_field(current_user: dict = Depends(get_current_user)):
    """Adiciona campo position aos registros existentes"""
    try:
        if DIRECT_URL:
            conn = get_direct_connection()
            if conn:
                try:
                    with conn.cursor() as cursor:
                        cursor.execute("""
                            SELECT column_name 
                            FROM information_schema.columns 
                            WHERE table_name = 'pecas' AND column_name = 'position'
                        """)
                        field_exists = cursor.fetchone()
                        
                        if not field_exists:
                            cursor.execute("""
                                ALTER TABLE pecas 
                                ADD COLUMN position SERIAL
                            """)
                            conn.commit()
                            
                            return {
                                "status": "success",
                                "message": "Campo 'position' adicionado com sucesso",
                                "field_added": True,
                                "instructions": [
                                    "O campo position foi adicionado à tabela",
                                    "Todos os registros existentes receberam posições sequenciais",
                                    "Novos registros terão automaticamente a próxima posição",
                                    "A ordenação padrão agora é por position DESC (mais novos primeiro)"
                                ]
                            }
                        else:
                            conn.close()
                            return {
                                "status": "info",
                                "message": "Campo 'position' já existe na tabela",
                                "field_exists": True
                            }
                except Exception as e:
                    conn.close()
                    raise e
        
        return {
            "status": "warning",
            "message": "Execute manualmente no Supabase SQL Editor:",
            "sql_command": "ALTER TABLE pecas ADD COLUMN position SERIAL;",
            "instructions": [
                "1. Acesse o Supabase Dashboard",
                "2. Vá para SQL Editor", 
                "3. Execute: ALTER TABLE pecas ADD COLUMN position SERIAL;",
                "4. Isso criará o campo position com valores sequenciais"
            ]
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": "Erro ao adicionar campo position",
            "erro": str(e),
            "manual_solution": {
                "sql": "ALTER TABLE pecas ADD COLUMN position SERIAL;",
                "instructions": "Execute este SQL no Supabase SQL Editor"
            }
        }

