"""Serviço de gerenciamento de peças"""
from database.connection import get_supabase_client
from config.settings import TABLE_NAME
from utils.retry import retry_with_backoff

class PecasService:
    """Serviço para operações com peças"""
    
    def __init__(self):
        self.supabase = get_supabase_client()
        self.table_name = TABLE_NAME
    
    @retry_with_backoff(max_retries=3, base_delay=1)
    def get_next_position(self):
        """Obtém a próxima posição disponível para ordenação"""
        try:
            # Buscar a maior posição atual
            response = self.supabase.table(self.table_name).select("position").order("position", desc=True).limit(1).execute()
            
            if response.data and response.data[0].get('position'):
                return response.data[0]['position'] + 1
            else:
                return 1  # Primeira posição
        except Exception as e:
            print(f"Erro ao obter próxima posição: {e}")
            return 1
    
    def filter_position_from_data(self, data):
        """Remove a coluna position dos dados retornados"""
        if isinstance(data, list):
            return [{k: v for k, v in item.items() if k != 'position'} for item in data]
        elif isinstance(data, dict):
            return {k: v for k, v in data.items() if k != 'position'}
        return data

