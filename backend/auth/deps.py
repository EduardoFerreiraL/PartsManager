"""Dependências FastAPI para autenticação e permissões"""
import time

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from auth.jwt import decode_token
from config.settings import LOGIN_TABLE_NAME
from database.connection import get_supabase_client, reset_supabase_client

security = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
):
    """Obtém o usuário atual a partir do token JWT. Levanta 401 se inválido ou ausente."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autenticação não fornecido",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = credentials.credentials
    payload = decode_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # Buscar usuário no banco para garantir que ainda existe e obter dados atualizados
    r = None
    for attempt in range(2):
        try:
            supabase = get_supabase_client()
            r = (
                supabase.table(LOGIN_TABLE_NAME)
                .select("id, nome, email, nivelPermissao")
                .eq("id", int(user_id))
                .execute()
            )
            break
        except (httpx.RemoteProtocolError, httpx.ConnectError, httpx.ReadTimeout) as e:
            reset_supabase_client()
            if attempt == 0:
                time.sleep(0.25)
                continue
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Serviço temporariamente indisponível. Tente novamente em instantes.",
            ) from e

    if r is None or not r.data or len(r.data) == 0:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não encontrado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    row = r.data[0]
    # Só permite acesso se tiver nível definido (aprovado); NULL = pendente
    nivel = row.get("nivelPermissao")
    if nivel is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Aguardando aprovação dos administradores",
        )
    return {
        "id": row["id"],
        "nome": row["nome"],
        "email": row["email"],
        "nivelPermissao": nivel,
    }


def require_permission(min_level: int):
    """
    Dependency factory: exige que o usuário tenha nivelPermissao <= min_level.
    (0 = máximo, 3 = mínimo)
    """

    def _require(current_user: dict = Depends(get_current_user)):
        nivel = current_user.get("nivelPermissao", 99)
        if nivel > min_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Sem permissão para esta ação",
            )
        return current_user

    return _require
