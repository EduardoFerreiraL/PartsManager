"""Rotas da API"""
from fastapi import APIRouter

# Criar router principal
api_router = APIRouter()

# Importar e incluir todas as rotas
from . import pecas, upload, stats, admin, pages, static, update_bulk, dashboard

api_router.include_router(pecas.router, prefix="/api", tags=["Peças"])
api_router.include_router(dashboard.router, prefix="/api", tags=["Dashboard"])
api_router.include_router(upload.router, prefix="/api", tags=["Upload"])
api_router.include_router(update_bulk.router, prefix="/api", tags=["Atualização em massa"])
api_router.include_router(stats.router, prefix="/api", tags=["Estatísticas"])
api_router.include_router(admin.router, prefix="/api", tags=["Admin"])
api_router.include_router(pages.router, tags=["Páginas"])
api_router.include_router(static.router, tags=["Estáticos"])

__all__ = ['api_router']





