#!/usr/bin/env python3
"""
Script simples para testar se o servidor está rodando
"""

import socket
import time

def test_server_connection():
    """Testa se o servidor está rodando na porta 8000"""
    print("🔍 Testando conexão com servidor...")
    
    # Tentar conectar na porta 8000
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5)
    
    try:
        result = sock.connect_ex(('localhost', 8000))
        if result == 0:
            print("✅ Servidor está rodando na porta 8000")
            return True
        else:
            print("❌ Servidor não está rodando na porta 8000")
            return False
    except Exception as e:
        print(f"❌ Erro ao testar conexão: {e}")
        return False
    finally:
        sock.close()

def test_uvicorn_import():
    """Testa se o uvicorn pode ser importado"""
    try:
        import uvicorn
        print("✅ Uvicorn pode ser importado")
        return True
    except ImportError as e:
        print(f"❌ Uvicorn não pode ser importado: {e}")
        return False

def test_main_import():
    """Testa se o módulo main pode ser importado"""
    try:
        import main
        print("✅ Módulo main pode ser importado")
        return True
    except Exception as e:
        print(f"❌ Erro ao importar main: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Teste de diagnóstico do servidor")
    print("=" * 40)
    
    # Testar imports
    print("\n1. Testando imports...")
    uvicorn_ok = test_uvicorn_import()
    main_ok = test_main_import()
    
    # Testar conexão
    print("\n2. Testando conexão...")
    server_ok = test_server_connection()
    
    # Resumo
    print("\n" + "=" * 40)
    print("📊 RESUMO:")
    print(f"   Uvicorn: {'✅' if uvicorn_ok else '❌'}")
    print(f"   Módulo main: {'✅' if main_ok else '❌'}")
    print(f"   Servidor rodando: {'✅' if server_ok else '❌'}")
    
    if not server_ok:
        print("\n🚀 Para iniciar o servidor:")
        print("   python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000")
        print("   ou")
        print("   uvicorn main:app --reload --host 0.0.0.0 --port 8000")

