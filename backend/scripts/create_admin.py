"""
Script para criar o usuário Admin inicial (nivelPermissao 0).
Uso (a partir da pasta backend):
  python -m scripts.create_admin

Variáveis de ambiente:
  ADMIN_EMAIL  - e-mail do admin (obrigatório)
  ADMIN_PASSWORD - senha (obrigatório, mínimo 8 caracteres)
"""
import os
import sys

# Garantir que o backend está no path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

import bcrypt
from database.connection import get_supabase_client
from config.settings import LOGIN_TABLE_NAME


def main():
    email = os.getenv("ADMIN_EMAIL", "").strip().lower()
    password = os.getenv("ADMIN_PASSWORD", "")
    if not email or not password:
        print("Erro: defina ADMIN_EMAIL e ADMIN_PASSWORD no .env")
        sys.exit(1)
    if len(password) < 8:
        print("Erro: ADMIN_PASSWORD deve ter no mínimo 8 caracteres")
        sys.exit(1)

    supabase = get_supabase_client()
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    # Verificar se já existe admin com esse email
    r = supabase.table(LOGIN_TABLE_NAME).select("id").eq("email", email).execute()
    if r.data and len(r.data) > 0:
        print(f"Já existe um usuário com o e-mail {email}. Nenhuma alteração feita.")
        sys.exit(0)

    supabase.table(LOGIN_TABLE_NAME).insert({
        "nome": "Admin",
        "email": email,
        "password": hashed,
        "nivelPermissao": 0,
    }).execute()
    print("Usuário Admin criado com sucesso (nivelPermissao 0).")


if __name__ == "__main__":
    main()
