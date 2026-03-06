"""Rotas de páginas HTML"""
from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()

@router.get("/", response_class=HTMLResponse, summary="Página Principal")
def read_root():
    """Retorna a página principal do Gerenciador de Peças"""
    try:
        with open("../frontend/index.html", "r", encoding="utf-8") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    except FileNotFoundError:
        return HTMLResponse(content="""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Gerenciador de Peças</title>
        </head>
        <body>
            <h1>Gerenciador de Peças</h1>
            <p>Arquivo frontend/index.html não encontrado.</p>
            <p>Certifique-se de que o arquivo existe na pasta frontend.</p>
        </body>
        </html>
        """)

@router.get("/adicionar", response_class=HTMLResponse, summary="Página de Adicionar Itens")
def adicionar_page():
    """Retorna a página de adicionar itens"""
    try:
        with open("../frontend/adicionar.html", "r", encoding="utf-8") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    except FileNotFoundError:
        return HTMLResponse(content="""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Adicionar Itens - Gerenciador de Peças</title>
        </head>
        <body>
            <h1>Adicionar Itens</h1>
            <p>Arquivo frontend/adicionar.html não encontrado.</p>
            <p><a href="/">Voltar ao menu principal</a></p>
        </body>
        </html>
        """)

@router.get("/visualizar", response_class=HTMLResponse, summary="Página de Visualizar Itens")
def visualizar_page():
    """Retorna a página de visualizar itens"""
    try:
        with open("../frontend/visualizar.html", "r", encoding="utf-8") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    except FileNotFoundError:
        return HTMLResponse(content="""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Visualizar Itens - Gerenciador de Peças</title>
        </head>
        <body>
            <h1>Visualizar Itens</h1>
            <p>Arquivo frontend/visualizar.html não encontrado.</p>
            <p><a href="/">Voltar ao menu principal</a></p>
        </body>
        </html>
        """)


@router.get("/atualizacao-em-massa", response_class=HTMLResponse, summary="Página de Atualização em Massa")
def atualizacao_em_massa_page():
    """Retorna a página de atualização em massa via planilha"""
    try:
        with open("../frontend/atualizacao-em-massa.html", "r", encoding="utf-8") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    except FileNotFoundError:
        return HTMLResponse(content="""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Atualização em Massa - Gerenciador de Peças</title>
        </head>
        <body>
            <h1>Atualização em Massa</h1>
            <p>Arquivo frontend/atualizacao-em-massa.html não encontrado.</p>
            <p><a href="/">Voltar ao menu principal</a></p>
        </body>
        </html>
        """)

@router.get("/dashboard", response_class=HTMLResponse, summary="Página de Dashboard")
def dashboard_page():
    """Retorna a página de dashboard de análise"""
    try:
        with open("../frontend/dashboard.html", "r", encoding="utf-8") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    except FileNotFoundError:
        return HTMLResponse(content="""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Dashboard - Gerenciador de Peças</title>
        </head>
        <body>
            <h1>Dashboard</h1>
            <p>Arquivo frontend/dashboard.html não encontrado.</p>
            <p><a href="/">Voltar ao menu principal</a></p>
        </body>
        </html>
        """)

@router.get("/login", response_class=HTMLResponse, summary="Página de Login")
def login_page():
    """Retorna a página de login"""
    try:
        with open("../frontend/login.html", "r", encoding="utf-8") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Login</h1><p>Arquivo frontend/login.html não encontrado.</p>")

@router.get("/novo-usuario", response_class=HTMLResponse, summary="Página de Novo Usuário")
def novo_usuario_page():
    """Retorna a página de cadastro de novo usuário"""
    try:
        with open("../frontend/novo-usuario.html", "r", encoding="utf-8") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Novo usuário</h1><p>Arquivo frontend/novo-usuario.html não encontrado.</p>")

@router.get("/aprovar-usuarios", response_class=HTMLResponse, summary="Página de Aprovar Usuários")
def aprovar_usuarios_page():
    """Retorna a página de aprovação de usuários (administradores)"""
    try:
        with open("../frontend/aprovar-usuarios.html", "r", encoding="utf-8") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Aprovar usuários</h1><p>Arquivo frontend/aprovar-usuarios.html não encontrado.</p>")





