# backend/main.py
#
# Backend da aplicação usando FastAPI e Supabase
# para gerenciar o upload em massa de dados de um arquivo Excel.
#
# Para rodar este código:
# 1. Instale as bibliotecas necessárias:
#    pip install fastapi "uvicorn[standard]" python-dotenv supabase pandas openpyxl
#
# 2. Crie um arquivo .env na pasta backend com suas credenciais do Supabase:
#    SUPABASE_URL="SEU_URL_DO_SUPABASE"
#    SUPABASE_KEY="SUA_CHAVE_DE_SERVICO_SUPABASE"
#
# 3. No terminal, rode a aplicação:
#    uvicorn main:app --reload

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from supabase import create_client, Client
import pandas as pd
from dotenv import load_dotenv
import os
import io
import json
import base64
from datetime import datetime

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# Inicializa o cliente Supabase usando variáveis de ambiente
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Variáveis de ambiente do Supabase não encontradas. Por favor, configure SUPABASE_URL e SUPABASE_KEY no seu arquivo .env.")

# Conecta ao Supabase com as credenciais
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Define o nome da tabela no Supabase
TABLE_NAME = "pecas"

# Inicializa a aplicação FastAPI
app = FastAPI(
    title="Gerenciador de Peças API",
    description="API para gerenciamento de peças com upload de Excel",
    version="1.0.0"
)

# Configuração CORS para permitir comunicação com o frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especifique apenas os domínios permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Montar arquivos estáticos da pasta frontend
app.mount("/static", StaticFiles(directory="../frontend"), name="static")

def clean_data_for_supabase(data_list):
    """Limpa e valida dados antes de enviar para o Supabase"""
    cleaned_data = []
    
    # Definir tipos esperados para cada coluna
    column_types = {
        'id': 'ignore',  # Ignorar coluna ID - deixar o Supabase gerar automaticamente
        'part_number': 'string',
        'chinese_description': 'string', 
        'description': 'string',
        'ncm': 'string',
        'date_of_creation': 'date',
        'review_date': 'date',
        'process': 'string',
        'machine': 'string',
        'created_at': 'ignore'  # Ignorar - será gerado automaticamente
    }
    

    
    for row_index, row in enumerate(data_list):
        cleaned_row = {}
        
        for key, value in row.items():
            # Determinar o tipo esperado para esta coluna
            expected_type = column_types.get(key.lower(), 'string')
            
            # Ignorar colunas que não devem ser enviadas
            if expected_type == 'ignore':
                continue
            
            # Tratar valores NaN/None
            if pd.isna(value) or value is None:
                cleaned_row[key] = None
                continue
            
            try:
                if expected_type == 'integer':
                    # Tentar converter para inteiro
                    if isinstance(value, str) and value.strip():
                        # Verificar se é um número válido
                        if value.replace('.', '').replace('-', '').isdigit():
                            cleaned_row[key] = int(float(value))
                        else:
                            cleaned_row[key] = None
                    else:
                        try:
                            cleaned_row[key] = int(value) if value else None
                        except (ValueError, TypeError):
                            cleaned_row[key] = None
                
                elif expected_type == 'date':
                    # Tratar datas
                    if isinstance(value, pd.Timestamp):
                        cleaned_row[key] = value.strftime('%Y-%m-%d') if pd.notna(value) else None
                    elif isinstance(value, str) and value.strip():
                        # Tentar converter string para data
                        try:
                            pd_date = pd.to_datetime(value, errors='coerce')
                            cleaned_row[key] = pd_date.strftime('%Y-%m-%d') if pd.notna(pd_date) else None
                        except:
                            cleaned_row[key] = None
                    else:
                        cleaned_row[key] = None
                
                elif expected_type == 'timestamp':
                    # Tratar timestamps
                    if isinstance(value, pd.Timestamp):
                        cleaned_row[key] = value.strftime('%Y-%m-%d %H:%M:%S') if pd.notna(value) else None
                    else:
                        cleaned_row[key] = None
                
                else:
                    # Para strings e outros tipos
                    if isinstance(value, (int, float, str, bool)):
                        cleaned_row[key] = str(value) if value is not None else None
                    else:
                        # Converter para string se não for um tipo básico
                        try:
                            cleaned_row[key] = str(value) if value is not None else None
                        except:
                            cleaned_row[key] = None
                            
            except (ValueError, TypeError) as e:
                # Se falhar na conversão, definir como None
                cleaned_row[key] = None
        
        cleaned_data.append(cleaned_row)
        

    

    return cleaned_data

def generate_conflicts_excel(conflicts, filename):
    """Gera uma planilha Excel com informações sobre conflitos encontrados"""
    try:
        # Criar DataFrame com os conflitos
        conflicts_data = []
        for conflict in conflicts:
            conflicts_data.append({
                'Part Number': conflict['part_number'],
                'Linha na Planilha': conflict['linha_planilha'],
                'Status': conflict['status'],
                'Data da Verificação': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
        
        df_conflicts = pd.DataFrame(conflicts_data)
        
        # Criar um buffer de bytes para o Excel
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_conflicts.to_excel(writer, sheet_name='Conflitos', index=False)
            
            # Adicionar informações gerais
            info_data = {
                'Informação': [
                    'Arquivo Original',
                    'Total de Itens na Planilha',
                    'Conflitos Encontrados',
                    'Itens Únicos para Inserir',
                    'Data/Hora da Verificação'
                ],
                'Valor': [
                    filename,
                    len(conflicts) + len([c for c in conflicts if c.get('status') == 'Já existe no banco']),
                    len(conflicts),
                    len([c for c in conflicts if c.get('status') == 'Já existe no banco']),
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                ]
            }
            
            df_info = pd.DataFrame(info_data)
            df_info.to_excel(writer, sheet_name='Resumo', index=False)
        
        output.seek(0)
        excel_data = output.read()
        
        # Converter para base64 para envio via JSON
        excel_base64 = base64.b64encode(excel_data).decode('utf-8')
        
        return {
            'status': 'success',
            'excel_base64': excel_base64,
            'filename': f'conflitos_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        }
        
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Erro ao gerar planilha: {str(e)}'
        }

@app.get("/", response_class=HTMLResponse, summary="Página Principal")
def read_root():
    """Retorna a página principal do Gerenciador de Peças"""
    try:
        # Tentar ler o arquivo HTML do frontend
        with open("../frontend/index.html", "r", encoding="utf-8") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    except FileNotFoundError:
        # Fallback: HTML básico se o arquivo não existir
        return HTMLResponse(content="""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Gerenciador de Peças</title>
        </head>
        <body>
            <h1>Gerenciador de Peças</h1>
            <p>Arquivo frontend/index.html não encontrado.</p>
            <p>Certifique-se de que o arquivo existe na pasta frontend.</p>
        </body>
        </html>
        """)

@app.get("/adicionar", response_class=HTMLResponse, summary="Página de Adicionar Itens")
def adicionar_page():
    """Retorna a página de adicionar itens"""
    try:
        with open("../frontend/adicionar.html", "r", encoding="utf-8") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    except FileNotFoundError:
        return HTMLResponse(content="""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Adicionar Itens - Gerenciador de Peças</title>
        </head>
        <body>
            <h1>Adicionar Itens</h1>
            <p>Arquivo frontend/adicionar.html não encontrado.</p>
            <p><a href="/">Voltar ao menu principal</a></p>
        </body>
        </html>
        """)

@app.get("/visualizar", response_class=HTMLResponse, summary="Página de Visualizar Itens")
def visualizar_page():
    """Retorna a página de visualizar itens"""
    try:
        with open("../frontend/visualizar.html", "r", encoding="utf-8") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    except FileNotFoundError:
        return HTMLResponse(content="""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Visualizar Itens - Gerenciador de Peças</title>
        </head>
        <body>
            <h1>Visualizar Itens</h1>
            <p>Arquivo frontend/visualizar.html não encontrado.</p>
            <p><a href="/">Voltar ao menu principal</a></p>
        </body>
        </html>
        """)

@app.get("/api/health", summary="Verificar Status da API")
def health_check():
    """Verifica o status da API e conexão com o banco de dados"""
    try:
        # Testar conexão com o Supabase usando uma coluna que existe
        response = supabase.table(TABLE_NAME).select("part_number").limit(1).execute()
        return {
            "status": "healthy",
            "message": "API funcionando e conectada ao banco de dados",
            "timestamp": pd.Timestamp.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "message": f"Erro na conexão com o banco: {str(e)}",
            "timestamp": pd.Timestamp.now().isoformat()
        }



@app.get("/api/stats", summary="Estatísticas do Banco")
def get_stats():
    """Retorna estatísticas do banco de dados"""
    try:
        # Contar total de peças usando uma coluna que existe
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

@app.get("/api/table-structure", summary="Estrutura da Tabela")
def get_table_structure():
    """Retorna a estrutura real da tabela no Supabase"""
    try:
        # Tentar fazer uma consulta simples para ver a estrutura
        response = supabase.table(TABLE_NAME).select("*").limit(1).execute()
        
        if response.data:
            # Pegar a primeira linha para ver as colunas
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



@app.post("/api/upload-excel", summary="Upload e Inserção de Dados")
async def upload_excel(file: UploadFile = File(...)):
    """Recebe arquivo Excel e insere dados no banco"""
    if not file.filename.endswith('.xlsx'):
        raise HTTPException(status_code=400, detail="Apenas arquivos .xlsx são aceitos")
    
    try:
        # Ler o arquivo Excel
        contents = await file.read()
        df = pd.read_excel(io.BytesIO(contents))
        

        
        # Primeiro, verificar a estrutura da tabela
        table_structure = get_table_structure()
        if table_structure["status"] == "success" and table_structure["colunas_encontradas"]:
            available_columns = table_structure["colunas_encontradas"]
        else:
            # Se não conseguir verificar, usar as colunas padrão esperadas
            available_columns = [
                "part_number",
                "chinese_description", 
                "description",
                "ncm",
                "date_of_creation",
                "review_date",
                "process",
                "machine"
            ]
        

        
        # Filtrar apenas as colunas que existem na tabela
        existing_columns = [col for col in df.columns if col.lower() in [ac.lower() for ac in available_columns]]
        
        if not existing_columns:
            raise HTTPException(
                status_code=400, 
                detail=f"Nenhuma coluna da planilha corresponde às colunas da tabela. Colunas da planilha: {list(df.columns)}, Colunas da tabela: {available_columns}"
            )
        

        
        # Manter apenas as colunas que existem na tabela
        df_filtered = df[existing_columns]
        
        # Mapear colunas do Excel para as colunas do banco (se necessário)
        column_mapping = {
            # Exemplo: se sua planilha tem "PN" mas o banco tem "part_number"
            # "PN": "part_number",
            # "Descrição": "description",
            # etc.
        }
        
        # Renomear colunas se houver mapeamento
        if column_mapping:
            df_filtered = df_filtered.rename(columns=column_mapping)
        
        # Converter DataFrame para lista de dicionários
        data_to_insert = df_filtered.to_dict('records')
        
        # Limpar dados antes de inserir usando a função especializada
        cleaned_data = clean_data_for_supabase(data_to_insert)
        
        # Verificar se há valores problemáticos antes de enviar

        
        # Verificar part_numbers duplicados
        part_numbers = [row.get('part_number') for row in cleaned_data if row.get('part_number')]
        duplicates = {}
        for i, pn in enumerate(part_numbers):
            if pn in duplicates:
                duplicates[pn].append(i + 1)  # +1 para linha da planilha (1-indexed)
            else:
                duplicates[pn] = [i + 1]
        
        # Filtrar apenas os que aparecem mais de uma vez
        duplicates = {pn: lines for pn, lines in duplicates.items() if len(lines) > 1}
        
        if duplicates:
            # Part Numbers duplicados encontrados na planilha
            pass

        
        # Verificar se part_numbers já existem no banco

        existing_pns = set()
        try:
            # Buscar todos os part_numbers existentes no banco
            response = supabase.table(TABLE_NAME).select("part_number").execute()
            existing_pns = {str(row['part_number']) for row in response.data if row.get('part_number')}
        except Exception as e:
            pass
        
        # Verificar conflitos
        conflicts = []
        for i, row in enumerate(cleaned_data):
            pn = str(row.get('part_number')) if row.get('part_number') else None
            if pn and pn in existing_pns:
                conflicts.append({
                    'part_number': pn,
                    'linha_planilha': i + 1,
                    'status': 'Já existe no banco'
                })
        
        if conflicts:
            # Part Numbers já existem no banco
            
            # Gerar planilha de conflitos
            conflicts_excel = generate_conflicts_excel(conflicts, file.filename)
            
            # Filtrar apenas os que não existem no banco
            cleaned_data = [row for row in cleaned_data if not (row.get('part_number') and str(row.get('part_number')) in existing_pns)]

            
            # Se não há dados para inserir, retornar apenas os conflitos
            if not cleaned_data:
                return {
                    "status": "conflicts_only",
                    "message": f"Nenhum item foi inserido. {len(conflicts)} Part Numbers já existem no banco.",
                    "rows_inserted": 0,
                    "filename": file.filename,
                    "conflicts_found": len(conflicts),
                    "total_original": len(data_to_insert),
                    "conflicts_excel": conflicts_excel
                }
        
        # Inserir dados no Supabase

        response = supabase.table(TABLE_NAME).insert(cleaned_data).execute()
        

        
        return {
            "status": "success",
            "message": f"Arquivo processado com sucesso! {len(cleaned_data)} peças inseridas.",
            "rows_inserted": len(cleaned_data),
            "filename": file.filename,
            "colunas_processadas": list(df_filtered.columns),
            "colunas_ignoradas": [col for col in df.columns if col not in existing_columns],
            "total_colunas": len(df_filtered.columns),
            "total_linhas": len(df_filtered),
            "estrutura_tabela": available_columns,
            "conflicts_found": len(conflicts) if 'conflicts' in locals() else 0,
            "total_original": len(data_to_insert),
            "conflicts_excel": conflicts_excel if 'conflicts' in locals() and conflicts else None
        }
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()

        
        # Verificar se é erro de serialização
        if "JSON serializable" in str(e) or "Timestamp" in str(e):
            error_message = f"Erro de serialização de dados: {str(e)}. Verifique se há colunas com datas ou tipos de dados não suportados."
        elif "column" in str(e).lower() and "not found" in str(e).lower():
            error_message = f"Erro de coluna: {str(e)}. Verifique se os nomes das colunas da planilha correspondem às colunas da tabela."
        elif "invalid input syntax" in str(e).lower():
            error_message = f"Erro de tipo de dados: {str(e)}. Uma coluna está recebendo dados do tipo incorreto. Verifique o log no terminal para mais detalhes."
        else:
            error_message = f"Erro ao processar arquivo: {str(e)}"
        
        raise HTTPException(status_code=500, detail=error_message)

@app.post("/api/analyze-excel", summary="Analisar Planilha Excel")
async def analyze_excel(file: UploadFile = File(...)):
    """Analisa a planilha Excel antes do upload para identificar problemas"""
    if not file.filename.endswith('.xlsx'):
        raise HTTPException(status_code=400, detail="Apenas arquivos .xlsx são aceitos")
    
    try:
        # Ler o arquivo Excel
        contents = await file.read()
        df = pd.read_excel(io.BytesIO(contents))
        
        # Analisar cada coluna
        column_analysis = {}
        for col in df.columns:
            col_data = df[col].dropna()
            
            # Determinar tipo de dados
            if col_data.empty:
                data_type = "vazio"
                sample_values = []
            else:
                # Verificar se é numérico
                if pd.api.types.is_numeric_dtype(col_data):
                    data_type = "numérico"
                    sample_values = col_data.head(5).tolist()
                elif pd.api.types.is_datetime64_any_dtype(col_data):
                    data_type = "data"
                    sample_values = col_data.head(5).dt.strftime('%Y-%m-%d').tolist()
                else:
                    data_type = "texto"
                    sample_values = col_data.head(5).astype(str).tolist()
            
            column_analysis[col] = {
                "tipo_detectado": data_type,
                "total_valores": len(col_data),
                "valores_vazios": df[col].isna().sum(),
                "exemplos": sample_values,
                "problemas_potenciais": []
            }
            
            # Identificar problemas potenciais
            if data_type == "texto":
                # Verificar se há valores muito longos
                max_length = col_data.astype(str).str.len().max()
                if max_length > 1000:
                    column_analysis[col]["problemas_potenciais"].append(f"Valores muito longos (máx: {max_length} chars)")
                
                # Verificar se há valores que parecem números em colunas de texto
                numeric_like = col_data.astype(str).str.match(r'^\d+\.?\d*$').sum()
                if numeric_like > 0:
                    column_analysis[col]["problemas_potenciais"].append(f"{numeric_like} valores parecem números")
            
            elif data_type == "numérico":
                # Verificar se há valores negativos onde não deveria
                if (col_data < 0).any():
                    column_analysis[col]["problemas_potenciais"].append("Contém valores negativos")
                
                # Verificar se há valores muito grandes
                if col_data.max() > 1e9:
                    column_analysis[col]["problemas_potenciais"].append("Contém valores muito grandes")
        
        return {
            "status": "success",
            "filename": file.filename,
            "total_linhas": len(df),
            "total_colunas": len(df.columns),
            "analise_colunas": column_analysis,
            "recomendacoes": [
                "Verifique se os tipos de dados estão corretos",
                "Colunas numéricas não devem conter texto",
                "Colunas de data devem estar no formato correto",
                "Valores vazios serão convertidos para NULL"
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao analisar arquivo: {str(e)}")

@app.get("/api/pecas", summary="Buscar Peças")
def search_pecas(
    part_number: str = None,
    description: str = None,
    ncm: str = None,
    date_of_creation: str = None,
    review_date: str = None,
    limit: int = 100
):
    """Busca peças com filtros opcionais"""
    try:
        query = supabase.table(TABLE_NAME).select("*")
        
        # Aplicar filtros usando as colunas reais
        if part_number:
            # Para part_number que pode ser bigint, usar igualdade exata
            try:
                # Tentar converter para inteiro primeiro
                part_number_int = int(part_number)
                query = query.eq("part_number", part_number_int)
            except ValueError:
                # Se não for número, usar busca de texto (cast para text)
                query = query.ilike("part_number::text", f"%{part_number}%")
        
        if description:
            query = query.ilike("description", f"%{description}%")
        
        if ncm:
            # Para NCM que pode ser bigint, usar cast para text
            try:
                ncm_int = int(ncm)
                query = query.eq("ncm", ncm_int)
            except ValueError:
                query = query.ilike("ncm::text", f"%{ncm}%")
        
        if date_of_creation:
            query = query.eq("date_of_creation", date_of_creation)
        
        if review_date:
            query = query.eq("review_date", review_date)
        
        # Limitar resultados
        query = query.limit(limit)
        
        response = query.execute()
        
        return {
            "status": "success",
            "pecas": response.data,
            "total_encontrado": len(response.data),
            "filtros_aplicados": {
                "part_number": part_number,
                "description": description,
                "ncm": ncm,
                "date_of_creation": date_of_creation,
                "review_date": review_date
            }
        }
        
    except Exception as e:
        # Retornar erro mais amigável
        error_message = str(e)
        if "operator does not exist" in error_message:
            return {
                "status": "error",
                "message": "Erro de tipo de dados nos filtros. O sistema está tentando converter automaticamente os tipos.",
                "detail": error_message,
                "suggestion": "Tente usar números para Part Number e NCM, ou texto para Descrição"
            }
        else:
            raise HTTPException(status_code=500, detail=f"Erro na busca: {error_message}")



@app.get("/api/download-model", summary="Download da Planilha Modelo")
def download_model_excel():
    """Endpoint para download da planilha modelo"""
    try:
        # Caminho para o arquivo modelo
        model_path = "model.xlsx"
        
        # Verificar se o arquivo existe
        if not os.path.exists(model_path):
            raise HTTPException(status_code=404, detail="Arquivo modelo não encontrado")
        
        # Ler o arquivo
        with open(model_path, "rb") as file:
            file_content = file.read()
        
        # Retornar o arquivo como resposta
        from fastapi.responses import Response
        return Response(
            content=file_content,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename=model.xlsx",
                "Content-Length": str(len(file_content))
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao baixar arquivo modelo: {str(e)}")

@app.get("/api/check-table", summary="Verificar/Criar Tabela")
def check_and_create_table():
    """Verifica se a tabela existe e cria se necessário"""
    try:
        # Tentar fazer uma consulta simples
        response = supabase.table(TABLE_NAME).select("*").limit(1).execute()
        
        return {
            "status": "success",
            "message": "Tabela existe e está acessível",
            "tabela": TABLE_NAME,
            "existe": True
        }
        
    except Exception as e:
        error_msg = str(e)
        
        # Se a tabela não existe, tentar criar
        if "relation" in error_msg.lower() and "does not exist" in error_msg.lower():
            try:
                # Criar tabela com a estrutura esperada
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
                
                # Executar SQL via Supabase (se suportado)
                # Como alternativa, vamos retornar instruções para criar manualmente
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
                
            except Exception as create_error:
                return {
                    "status": "error",
                    "message": "Erro ao tentar criar tabela",
                    "tabela": TABLE_NAME,
                    "existe": False,
                    "erro": str(create_error),
                    "sql_para_criar": f"""
                    CREATE TABLE {TABLE_NAME} (
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
                }
        
        return {
            "status": "error",
            "message": "Erro ao verificar tabela",
            "tabela": TABLE_NAME,
            "existe": False,
            "erro": error_msg
        }

@app.put("/api/pecas/part_number/{part_number}", summary="Atualizar Peça por Part Number")
def update_peca_by_part_number(part_number: int, peca_data: dict):
    """Atualiza uma peça específica no banco de dados usando part_number como identificador"""
    try:
        # Validar dados recebidos
        allowed_fields = {
            'chinese_description', 'description', 'ncm',
            'date_of_creation', 'review_date', 'process', 'machine'
        }
        
        # Filtrar apenas campos permitidos
        update_data = {k: v for k, v in peca_data.items() if k in allowed_fields}
        
        if not update_data:
            raise HTTPException(status_code=400, detail="Nenhum campo válido para atualização")
        
        # Atualizar no Supabase usando part_number
        response = supabase.table(TABLE_NAME).update(update_data).eq("part_number", part_number).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail=f"Peça com part_number {part_number} não encontrada")
        
        return {
            "status": "success",
            "message": "Peça atualizada com sucesso",
            "peca_atualizada": response.data[0]
        }
        
    except Exception as e:
        error_message = str(e)
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar peça: {error_message}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
