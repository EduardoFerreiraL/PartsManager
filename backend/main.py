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

import os
import sys
import subprocess
from pathlib import Path

# Se for executado diretamente com Python global sem o venv ativado, redireciona para o venv
if __name__ == "__main__" and sys.prefix == sys.base_prefix:
    root_dir = Path(__file__).resolve().parent.parent
    backend_dir = Path(__file__).resolve().parent
    candidates = [
        root_dir / "venv" / "Scripts" / "python.exe",
        backend_dir / "venv" / "Scripts" / "python.exe",
        root_dir / ".venv" / "Scripts" / "python.exe",
        backend_dir / ".venv" / "Scripts" / "python.exe",
    ]
    for venv_py in candidates:
        if venv_py.exists():
            print(f"[*] Redirecionando para o ambiente virtual: {venv_py}")
            try:
                result = subprocess.run([str(venv_py)] + sys.argv)
                sys.exit(result.returncode)
            except KeyboardInterrupt:
                sys.exit(0)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from utils.network import get_local_ip
from routes import api_router

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

# Incluir todas as rotas
app.include_router(api_router)

# Evento de startup para mostrar informações de acesso
@app.on_event("startup")
async def startup_event():
    """Exibe informações de acesso quando o servidor inicia"""
    local_ip = get_local_ip()
    port = 8000  # Porta padrão
    
    # Tentar obter a porta de várias fontes
    try:
        # Verificar argumentos da linha de comando
        if '--port' in sys.argv:
            port_idx = sys.argv.index('--port')
            if port_idx + 1 < len(sys.argv):
                port = int(sys.argv[port_idx + 1])
        # Verificar variável de ambiente
        elif 'PORT' in os.environ:
            port = int(os.environ['PORT'])
        # Verificar se há um servidor uvicorn rodando (via variável de ambiente)
        elif 'UVICORN_PORT' in os.environ:
            port = int(os.environ['UVICORN_PORT'])
    except:
        pass
    
    print("\n" + "="*70)
    print("🌐 SERVIDOR INICIADO COM SUCESSO!")
    print("="*70)
    print(f"📍 IP Local da sua máquina: {local_ip}")
    print(f"🔌 Porta: {port}")
    print()
    print("💻 Acesso local:")
    print(f"   → http://localhost:{port}")
    print()
    print("📱 Acesso de outros dispositivos na mesma rede:")
    print(f"   → http://{local_ip}:{port}")
    print()
    print("⚠️  Certifique-se de que o firewall permite conexões na porta", port)
    print("="*70 + "\n")

if __name__ == "__main__":
    import uvicorn
    reload = "--reload" in sys.argv
    port = 8000
    if "--port" in sys.argv:
        try:
            port = int(sys.argv[sys.argv.index("--port") + 1])
        except (ValueError, IndexError):
            pass
    os.environ['UVICORN_PORT'] = str(port)
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=reload)
