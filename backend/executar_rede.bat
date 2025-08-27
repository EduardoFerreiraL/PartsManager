@echo off
chcp 65001 >nul
title Gerenciador de Peças - Servidor de Rede

echo.
echo ========================================
echo   GERENCIADOR DE PEÇAS - REDE LOCAL
echo ========================================
echo.

echo 🚀 Iniciando servidor para acesso em rede...
echo.

echo 📋 Verificando ambiente...
if not exist ".env" (
    echo ❌ ARQUIVO .env NÃO ENCONTRADO!
    echo.
    echo 📝 Crie um arquivo .env com suas credenciais:
    echo    SUPABASE_URL=sua_url_do_supabase
    echo    SUPABASE_KEY=sua_chave_do_supabase
    echo.
    pause
    exit /b 1
)

echo ✅ Arquivo .env encontrado
echo.

echo 🔧 Ativando ambiente virtual...
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
    echo ✅ Ambiente virtual ativado
) else (
    echo ⚠️  Ambiente virtual não encontrado
    echo    Instalando dependências globalmente...
    pip install -r requirements.txt
)

echo.
echo 🌐 Iniciando servidor em modo de rede...
echo 📱 Outros dispositivos na mesma rede poderão acessar
echo.
echo 🛑 Para parar: Ctrl+C
echo.

python run_network.py --reload

echo.
echo 🛑 Servidor parado
pause
