"""Configurações e variáveis de ambiente"""
import os
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# Inicializa o cliente Supabase usando variáveis de ambiente
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
DIRECT_URL = os.getenv("DIRECT_URL")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError(
        "Variáveis de ambiente do Supabase não encontradas. "
        "Por favor, configure SUPABASE_URL e SUPABASE_KEY no seu arquivo .env."
    )

# Define o nome da tabela no Supabase
TABLE_NAME = "pecas"

