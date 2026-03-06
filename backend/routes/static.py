"""Rotas para servir arquivos estáticos"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import os

router = APIRouter()

# Caminho absoluto para o frontend (independente do diretório de trabalho do uvicorn)
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FRONTEND_DIR = os.path.join(_BASE_DIR, "frontend")

@router.get("/config.js", response_class=FileResponse)
def serve_config_js():
    """Serve o arquivo config.js"""
    return FileResponse(os.path.join(FRONTEND_DIR, "config.js"))

@router.get("/auth.js", response_class=FileResponse)
def serve_auth_js():
    """Serve o arquivo auth.js"""
    return FileResponse(os.path.join(FRONTEND_DIR, "auth.js"))

@router.get("/navbar.js", response_class=FileResponse)
def serve_navbar_js():
    """Serve o arquivo navbar.js"""
    return FileResponse(os.path.join(FRONTEND_DIR, "navbar.js"))

@router.get("/script.js", response_class=FileResponse)
def serve_script_js():
    """Serve o arquivo script.js"""
    return FileResponse(os.path.join(FRONTEND_DIR, "script.js"))

@router.get("/imagens/{filename:path}", response_class=FileResponse)
def serve_images(filename: str):
    """Serve imagens da pasta imagens"""
    image_path = os.path.join(FRONTEND_DIR, "imagens", filename)
    if os.path.isfile(image_path):
        return FileResponse(image_path)
    raise HTTPException(status_code=404, detail="Imagem não encontrada")

@router.get("/components/{filename:path}", response_class=FileResponse)
def serve_components(filename: str):
    """Serve arquivos da pasta components"""
    component_path = os.path.join(FRONTEND_DIR, "components", filename)
    if os.path.isfile(component_path):
        return FileResponse(component_path)
    raise HTTPException(status_code=404, detail="Arquivo não encontrado")





