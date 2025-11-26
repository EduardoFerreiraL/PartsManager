"""Serviço de validação de dados"""
import pandas as pd

class ValidationService:
    """Serviço para validação de dados"""
    
    def validate_excel_data(self, data_list):
        """Valida dados do Excel e retorna erros detalhados"""
        errors = []
        warnings = []
        
        # Campos obrigatórios
        required_fields = ['part_number', 'description', 'ncm']
        
        for row_index, row in enumerate(data_list, 1):
            row_errors = []
            row_warnings = []
            
            # Verificar campos obrigatórios
            for field in required_fields:
                value = row.get(field)
                if not value or (isinstance(value, str) and value.strip() == ''):
                    row_errors.append({
                        'campo': field,
                        'problema': 'Campo obrigatório vazio',
                        'sugestao': f'Preencha o campo {field} na linha {row_index}'
                    })
            
            # Validar Part Number
            if row.get('part_number'):
                try:
                    pn = int(row['part_number'])
                    if pn <= 0:
                        row_errors.append({
                            'campo': 'part_number',
                            'problema': 'Part Number deve ser um número positivo',
                            'sugestao': f'Digite um número válido na linha {row_index}'
                        })
                except (ValueError, TypeError):
                    row_errors.append({
                        'campo': 'part_number',
                        'problema': 'Part Number deve ser um número',
                        'sugestao': f'Digite apenas números na linha {row_index}'
                    })
            
            # Validar NCM
            if row.get('ncm'):
                try:
                    ncm = int(row['ncm'])
                    if ncm <= 0 or len(str(ncm)) > 8:
                        row_errors.append({
                            'campo': 'ncm',
                            'problema': 'NCM deve ser um número positivo com máximo 8 dígitos',
                            'sugestao': f'Digite um NCM válido na linha {row_index}'
                        })
                except (ValueError, TypeError):
                    row_errors.append({
                        'campo': 'ncm',
                        'problema': 'NCM deve ser um número',
                        'sugestao': f'Digite apenas números na linha {row_index}'
                    })
            
            # Validar Origin
            if row.get('origin'):
                try:
                    origin = int(row['origin'])
                    if origin < 0 or origin > 9:
                        row_errors.append({
                            'campo': 'origin',
                            'problema': 'Origin deve ser um número de 0 a 9',
                            'sugestao': f'Digite um número de 0 a 9 na linha {row_index}'
                        })
                except (ValueError, TypeError):
                    row_errors.append({
                        'campo': 'origin',
                        'problema': 'Origin deve ser um número',
                        'sugestao': f'Digite apenas números na linha {row_index}'
                    })
            
            # Validar datas
            if row.get('date_of_creation'):
                try:
                    pd.to_datetime(row['date_of_creation'])
                except:
                    row_errors.append({
                        'campo': 'date_of_creation',
                        'problema': 'Data de criação inválida',
                        'sugestao': f'Use o formato DD/MM/AAAA ou AAAA-MM-DD na linha {row_index}'
                    })
            
            if row.get('review_date'):
                try:
                    pd.to_datetime(row['review_date'])
                except:
                    row_warnings.append({
                        'campo': 'review_date',
                        'problema': 'Data de revisão inválida',
                        'sugestao': f'Use o formato DD/MM/AAAA ou AAAA-MM-DD na linha {row_index}'
                    })
            
            # Adicionar erros e avisos da linha
            if row_errors:
                errors.append({
                    'linha': row_index,
                    'erros': row_errors
                })
            
            if row_warnings:
                warnings.append({
                    'linha': row_index,
                    'avisos': row_warnings
                })
        
        return errors, warnings

