"""Serviço de processamento de Excel"""
import pandas as pd
import io
import base64
from datetime import datetime
from services.pecas_service import PecasService
from config.settings import TABLE_NAME

class ExcelService:
    """Serviço para processamento de arquivos Excel"""
    
    def __init__(self):
        self.pecas_service = PecasService()
    
    def clean_data_for_supabase(self, data_list, assign_positions=True):
        """Limpa e valida dados antes de enviar para o Supabase"""
        cleaned_data = []
        
        # Definir tipos esperados para cada coluna
        column_types = {
            'id': 'ignore',  # Ignorar coluna ID - deixar o Supabase gerar automaticamente
            'part_number': 'int8',
            'chinese_description': 'string',
            'description': 'string',
            'ncm': 'int8',
            'origin': 'int2',
            'date_of_creation': 'date',
            'review_date': 'date',
            'requester': 'string',
            'machine': 'string',
            'created_at': 'ignore',  # Ignorar - será gerado automaticamente
            'position': 'ignore'  # Ignorar - será atribuído automaticamente
        }
        
        # Obter posição inicial se necessário
        current_position = self.pecas_service.get_next_position() if assign_positions else None
        
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
                        # Tratar datas (aceitar formato M/D/YYYY da imagem)
                        if isinstance(value, pd.Timestamp):
                            cleaned_row[key] = value.strftime('%Y-%m-%d') if pd.notna(value) else None
                        elif isinstance(value, str) and value.strip():
                            # Tentar converter string para data (priorizando M/D/YYYY)
                            try:
                                # Tentar formato M/D/YYYY primeiro (da imagem)
                                if '/' in value and len(value.split('/')) == 3:
                                    parts = value.split('/')
                                    if len(parts[0]) <= 2 and len(parts[1]) <= 2:  # M/D/YYYY
                                        pd_date = pd.to_datetime(value, format='%m/%d/%Y', errors='coerce')
                                    else:  # YYYY/MM/DD
                                        pd_date = pd.to_datetime(value, format='%Y/%m/%d', errors='coerce')
                                else:
                                    # Tentar parsing automático
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
                        elif isinstance(value, str) and value.strip():
                            # Tentar converter string para timestamp
                            try:
                                pd_timestamp = pd.to_datetime(value, errors='coerce')
                                cleaned_row[key] = pd_timestamp.strftime('%Y-%m-%d %H:%M:%S') if pd.notna(pd_timestamp) else None
                            except:
                                cleaned_row[key] = None
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
            
            # Atribuir posição se necessário
            if assign_positions and current_position is not None:
                cleaned_row['position'] = current_position
                current_position += 1
            
            cleaned_data.append(cleaned_row)
        
        return cleaned_data
    
    def generate_conflicts_excel(self, conflicts, filename):
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

