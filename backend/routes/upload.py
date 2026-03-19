"""Rotas de upload de arquivos Excel"""
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
import pandas as pd
import io
from database.connection import get_supabase_client
from config.settings import TABLE_NAME
from services.excel_service import ExcelService
from services.validation_service import ValidationService
from services.pecas_service import PecasService
from routes import stats
from auth.deps import require_permission

router = APIRouter()
excel_service = ExcelService()
validation_service = ValidationService()
pecas_service = PecasService()
supabase = get_supabase_client()

@router.post("/upload-excel", summary="Upload e Inserção de Dados")
async def upload_excel(file: UploadFile = File(...), current_user: dict = Depends(require_permission(2))):
    """Recebe arquivo Excel e insere dados no banco"""
    if not file.filename.endswith('.xlsx'):
        raise HTTPException(status_code=400, detail="Apenas arquivos .xlsx são aceitos")
    
    try:
        # Ler o arquivo Excel
        contents = await file.read()
        df = pd.read_excel(io.BytesIO(contents))
        
        # Verificar a estrutura da tabela
        table_structure = stats.get_table_structure_impl()
        if table_structure["status"] == "success" and table_structure["colunas_encontradas"]:
            available_columns = table_structure["colunas_encontradas"]
        else:
            available_columns = [
                "part_number", "chinese_description", "description", "ncm", "origin",
                "date_of_creation", "review_date", "requester", "machine", "Situation_OSGT"
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
        column_mapping = {}
        
        # Renomear colunas se houver mapeamento
        if column_mapping:
            df_filtered = df_filtered.rename(columns=column_mapping)
        
        # Converter DataFrame para lista de dicionários
        data_to_insert = df_filtered.to_dict('records')
        
        # Validar dados antes de processar
        validation_errors, validation_warnings = validation_service.validate_excel_data(data_to_insert)
        
        # Se há erros de validação, retornar erro detalhado
        if validation_errors:
            return {
                "status": "validation_error",
                "message": f"Encontrados {len(validation_errors)} erros de validação na planilha",
                "filename": file.filename,
                "total_linhas": len(data_to_insert),
                "erros_validacao": validation_errors,
                "avisos_validacao": validation_warnings,
                "resumo_erros": {
                    "total_erros": len(validation_errors),
                    "total_avisos": len(validation_warnings),
                    "linhas_com_erro": [e['linha'] for e in validation_errors]
                }
            }
        
        # Limpar dados antes de inserir
        cleaned_data = excel_service.clean_data_for_supabase(data_to_insert, assign_positions=True)

        # Carimba pelo usuário logado (JWT) quando a coluna existir.
        table_structure = stats.get_table_structure_impl()
        has_added_modified = False
        if table_structure.get("status") == "success":
            cols = [c.lower() for c in (table_structure.get("colunas_encontradas") or []) if isinstance(c, str)]
            has_added_modified = "added_modified" in cols

        if has_added_modified:
            user_name = current_user.get("nome")
            for row in cleaned_data:
                row["added_modified"] = user_name
        
        # Verificar duplicatas dentro do próprio arquivo primeiro
        seen_pns = set()
        duplicates_in_file = []
        for i, row in enumerate(cleaned_data):
            pn = str(row.get('part_number')) if row.get('part_number') else None
            if pn:
                if pn in seen_pns:
                    duplicates_in_file.append({
                        'part_number': pn,
                        'linha_planilha': i + 1,
                        'status': 'Duplicado no arquivo'
                    })
                else:
                    seen_pns.add(pn)
        
        # Remover duplicatas do arquivo (manter apenas a primeira ocorrência)
        if duplicates_in_file:
            unique_data = []
            seen_pns_clean = set()
            for row in cleaned_data:
                pn = str(row.get('part_number')) if row.get('part_number') else None
                if pn and pn not in seen_pns_clean:
                    unique_data.append(row)
                    seen_pns_clean.add(pn)
                elif not pn:
                    # Manter linhas sem part_number (serão rejeitadas na validação, mas não causam erro aqui)
                    unique_data.append(row)
            cleaned_data = unique_data
        
        # Verificar se part_numbers já existem no banco
        existing_pns = set()
        try:
            response = supabase.table(TABLE_NAME).select("part_number").execute()
            existing_pns = {str(row['part_number']) for row in response.data if row.get('part_number')}
        except Exception as e:
            print(f"Erro ao verificar part_numbers existentes: {e}")
        
        # Verificar conflitos com o banco
        conflicts = []
        conflicts.extend(duplicates_in_file)  # Adicionar duplicatas do arquivo aos conflitos
        
        for i, row in enumerate(cleaned_data):
            pn = str(row.get('part_number')) if row.get('part_number') else None
            if pn and pn in existing_pns:
                conflicts.append({
                    'part_number': pn,
                    'linha_planilha': i + 1,
                    'status': 'Já existe no banco'
                })
        
        conflicts_excel = None
        if conflicts:
            # Gerar planilha de conflitos
            conflicts_excel = excel_service.generate_conflicts_excel(conflicts, file.filename)
            
            # Filtrar apenas os que não existem no banco E não são duplicados no arquivo
            seen_conflicts = {c['part_number'] for c in conflicts}
            cleaned_data = [
                row for row in cleaned_data 
                if not (row.get('part_number') and str(row.get('part_number')) in seen_conflicts)
            ]
            
            # Se não há dados para inserir, retornar apenas os conflitos
            if not cleaned_data:
                return {
                    "status": "conflicts_only",
                    "message": f"Nenhum item foi inserido. {len(conflicts)} Part Numbers já existem no banco ou são duplicados no arquivo.",
                    "rows_inserted": 0,
                    "filename": file.filename,
                    "conflicts_found": len(conflicts),
                    "total_original": len(data_to_insert),
                    "conflicts_excel": conflicts_excel
                }
        
        # Inserir dados no Supabase em lotes para melhor tratamento de erros
        inserted_data = []
        failed_inserts = []
        
        if cleaned_data:
            try:
                # Tentar inserir todos de uma vez primeiro
                response = supabase.table(TABLE_NAME).insert(cleaned_data).execute()
                inserted_data = response.data if response.data else []
            except Exception as insert_error:
                # Se falhar, pode ser por duplicata ou outro erro
                error_str = str(insert_error)
                if "duplicate key" in error_str.lower() or "23505" in error_str:
                    # Se houver erro de duplicata, tentar inserir um por um
                    print(f"Erro de duplicata detectado, tentando inserção individual...")
                    for row in cleaned_data:
                        try:
                            response = supabase.table(TABLE_NAME).insert([row]).execute()
                            if response.data:
                                inserted_data.extend(response.data)
                        except Exception as individual_error:
                            pn = row.get('part_number')
                            failed_inserts.append({
                                'part_number': str(pn) if pn else 'N/A',
                                'linha_planilha': cleaned_data.index(row) + 1,
                                'status': f'Erro na inserção: {str(individual_error)[:100]}'
                            })
                    # Adicionar falhas aos conflitos
                    if failed_inserts:
                        conflicts.extend(failed_inserts)
                        conflicts_excel = excel_service.generate_conflicts_excel(conflicts, file.filename)
                else:
                    # Outro tipo de erro, relançar
                    raise insert_error
        
        # Filtrar a coluna position dos dados retornados
        filtered_data = pecas_service.filter_position_from_data(inserted_data) if inserted_data else []
        
        rows_inserted = len(inserted_data)
        conflicts_found = len(conflicts)
        
        # Determinar status e mensagem
        if rows_inserted > 0 and conflicts_found > 0:
            status = "success"
            message = f"Arquivo processado parcialmente! {rows_inserted} peça(s) inserida(s) com sucesso, {conflicts_found} item(s) não puderam ser inseridos."
        elif rows_inserted > 0:
            status = "success"
            message = f"Arquivo processado com sucesso! {rows_inserted} peça(s) inserida(s)."
        else:
            status = "conflicts_only"
            message = f"Nenhum item foi inserido. {conflicts_found} Part Number(s) já existem no banco ou são duplicados."
        
        return {
            "status": status,
            "message": message,
            "rows_inserted": rows_inserted,
            "filename": file.filename,
            "colunas_processadas": list(df_filtered.columns),
            "colunas_ignoradas": [col for col in df.columns if col not in existing_columns],
            "total_colunas": len(df_filtered.columns),
            "total_linhas": len(df_filtered),
            "estrutura_tabela": available_columns,
            "conflicts_found": conflicts_found,
            "total_original": len(data_to_insert),
            "conflicts_excel": conflicts_excel,
            "dados_inseridos": filtered_data
        }
        
    except Exception as e:
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

@router.post("/analyze-excel", summary="Analisar Planilha Excel")
async def analyze_excel(file: UploadFile = File(...), current_user: dict = Depends(require_permission(2))):
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
                max_length = col_data.astype(str).str.len().max()
                if max_length > 1000:
                    column_analysis[col]["problemas_potenciais"].append(f"Valores muito longos (máx: {max_length} chars)")
                
                numeric_like = col_data.astype(str).str.match(r'^\d+\.?\d*$').sum()
                if numeric_like > 0:
                    column_analysis[col]["problemas_potenciais"].append(f"{numeric_like} valores parecem números")
            
            elif data_type == "numérico":
                if (col_data < 0).any():
                    column_analysis[col]["problemas_potenciais"].append("Contém valores negativos")
                
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

