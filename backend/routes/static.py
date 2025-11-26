"""Rotas para servir arquivos estáticos"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import os

router = APIRouter()

@router.get("/config.js", response_class=FileResponse)
def serve_config_js():
    """Serve o arquivo config.js"""
    return FileResponse("../frontend/config.js")

@router.get("/navbar.js", response_class=FileResponse)
def serve_navbar_js():
    """Serve o arquivo navbar.js"""
    return FileResponse("../frontend/navbar.js")

@router.get("/script.js", response_class=FileResponse)
def serve_script_js():
    """Serve o arquivo script.js"""
    return FileResponse("../frontend/script.js")

@router.get("/tailwind.config.js", response_class=FileResponse)
def serve_tailwind_config():
    """Serve o arquivo tailwind.config.js"""
    return FileResponse("../frontend/tailwind.config.js")

@router.get("/imagens/{filename:path}", response_class=FileResponse)
def serve_images(filename: str):
    """Serve imagens da pasta imagens"""
    image_path = os.path.join("../frontend/imagens", filename)
    if os.path.isfile(image_path):
        return FileResponse(image_path)
    raise HTTPException(status_code=404, detail="Imagem não encontrada")

@router.get("/components/{filename:path}", response_class=FileResponse)
def serve_components(filename: str):
    """Serve arquivos da pasta components"""
    component_path = os.path.join("../frontend/components", filename)
    if os.path.isfile(component_path):
        return FileResponse(component_path)
    raise HTTPException(status_code=404, detail="Arquivo não encontrado")

