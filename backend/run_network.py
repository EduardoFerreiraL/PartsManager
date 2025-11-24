#!/usr/bin/env python3
"""
Script para executar o servidor FastAPI em modo de rede local.
Permite que outros dispositivos na mesma rede acessem a aplicação.

Uso:
    python run_network.py

Ou:
    python run_network.py --host 0.0.0.0 --port 8000
"""

import uvicorn
import argparse
import socket
import os
from pathlib import Path

def get_local_ip():
    """Obtém o IP local da máquina"""
    try:
        # Conecta a um endereço externo para descobrir o IP local
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        return "127.0.0.1"

def main():
    parser = argparse.ArgumentParser(description="Executar servidor FastAPI em modo de rede")
    parser.add_argument("--host", default="0.0.0.0", help="Host para bind (padrão: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8000, help="Porta para o servidor (padrão: 8000)")
    parser.add_argument("--reload", action="store_true", help="Ativar modo reload para desenvolvimento")
    
    args = parser.parse_args()
    
    # Obter IP local
    local_ip = get_local_ip()
    
    print("🚀 Iniciando servidor FastAPI em modo de rede...")
    print(f"📍 IP Local da sua máquina: {local_ip}")
    print(f"🌐 Host configurado: {args.host}")
    print(f"🔌 Porta: {args.port}")
    print(f"🔄 Modo reload: {'Ativado' if args.reload else 'Desativado'}")
    print()
    print("📱 Para acessar de outros dispositivos na mesma rede:")
    print(f"   http://{local_ip}:{args.port}")
    print()
    print("💻 Para acessar localmente:")
    print(f"   http://localhost:{args.port}")
    print()
    print("⚠️  IMPORTANTE:")
    print("   - Certifique-se de que o firewall permite conexões na porta", args.port)
    print("   - Apenas dispositivos na mesma rede Wi-Fi/LAN poderão acessar")
    print("   - Para segurança, use apenas em redes confiáveis")
    print()
    print("🛑 Para parar o servidor: Ctrl+C")
    print("-" * 60)
    
    # Verificar se o arquivo .env existe
    env_file = Path(".env")
    if not env_file.exists():
        print("❌ AVISO: Arquivo .env não encontrado!")
        print("   Crie um arquivo .env com suas credenciais do Supabase:")
        print("   SUPABASE_URL=sua_url_do_supabase")
        print("   SUPABASE_KEY=sua_chave_do_supabase")
        print()
    
    # Definir variável de ambiente com a porta para o evento de startup detectar
    os.environ['UVICORN_PORT'] = str(args.port)
    
    # Iniciar o servidor
    try:
        uvicorn.run(
            "main:app",
            host=args.host,
            port=args.port,
            reload=args.reload,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n🛑 Servidor parado pelo usuário")
    except Exception as e:
        print(f"❌ Erro ao iniciar servidor: {e}")

if __name__ == "__main__":
    main()

