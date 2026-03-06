"""Rotas de autenticação"""
import bcrypt
from fastapi import APIRouter, Depends, HTTPException, status
from database.connection import get_supabase_client
from config.settings import LOGIN_TABLE_NAME
from auth.schemas import (
    LoginRequest,
    LoginResponse,
    RegistroRequest,
    UserResponse,
    AprovarRequest,
    UsuarioPendenteResponse,
)
from auth.deps import get_current_user, require_permission
from auth.jwt import create_access_token

router = APIRouter(prefix="/auth", tags=["Auth"])


def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _check_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))


@router.post("/login", response_model=LoginResponse)
def login(body: LoginRequest):
    """Login com e-mail e senha. Retorna token e dados do usuário."""
    supabase = get_supabase_client()
    r = (
        supabase.table(LOGIN_TABLE_NAME)
        .select("id, nome, email, nivelPermissao, password")
        .eq("email", body.email.strip().lower())
        .execute()
    )
    if not r.data or len(r.data) == 0:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha incorretos",
        )
    row = r.data[0]
    if not _check_password(body.password, row["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha incorretos",
        )
    nivel = row.get("nivelPermissao")
    if nivel is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Aguardando aprovação dos administradores",
        )
    user = {
        "id": row["id"],
        "nome": row["nome"],
        "email": row["email"],
        "nivelPermissao": nivel,
    }
    token = create_access_token(
        {"sub": str(row["id"]), "email": row["email"], "nivel": nivel}
    )
    return LoginResponse(access_token=token, user=UserResponse(**user))


@router.post("/registro")
def registro(body: RegistroRequest):
    """Registro de novo usuário. Fica pendente até aprovação."""
    if len(body.password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A senha deve ter no mínimo 8 caracteres",
        )
    supabase = get_supabase_client()
    email = body.email.strip().lower()
    r = (
        supabase.table(LOGIN_TABLE_NAME)
        .select("id")
        .eq("email", email)
        .execute()
    )
    if r.data and len(r.data) > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Este e-mail já está cadastrado",
        )
    hashed = _hash_password(body.password)
    supabase.table(LOGIN_TABLE_NAME).insert(
        {
            "nome": body.nome.strip(),
            "email": email,
            "password": hashed,
            "nivelPermissao": None,
        }
    ).execute()
    return {"message": "Solicitação enviada aos administradores. Você poderá acessar o sistema após aprovação."}


@router.get("/me", response_model=UserResponse)
def me(current_user: dict = Depends(get_current_user)):
    """Retorna o usuário logado."""
    return UserResponse(**current_user)


@router.get("/pendentes", response_model=list[UsuarioPendenteResponse])
def listar_pendentes(current_user: dict = Depends(require_permission(1))):
    """Lista usuários aguardando aprovação. Apenas níveis 0 e 1."""
    supabase = get_supabase_client()
    r = (
        supabase.table(LOGIN_TABLE_NAME)
        .select("id, nome, email, created_at")
        .is_("nivelPermissao", "null")
        .execute()
    )
    out = []
    for row in (r.data or []):
        out.append(
            UsuarioPendenteResponse(
                id=row["id"],
                nome=row["nome"],
                email=row["email"],
                created_at=row.get("created_at"),
            )
        )
    return out


@router.patch("/aprovar/{user_id}")
def aprovar_usuario(
    user_id: int,
    body: AprovarRequest,
    current_user: dict = Depends(require_permission(1)),
):
    """Aprova um usuário e atribui nivelPermissao. Apenas níveis 0 e 1. Nível 0 só pode ser atribuído por usuário 0."""
    nivel_logado = current_user["nivelPermissao"]
    if body.nivelPermissao == 0 and nivel_logado != 0:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas administradores de nível 0 podem atribuir permissão 0",
        )
    supabase = get_supabase_client()
    r = (
        supabase.table(LOGIN_TABLE_NAME)
        .select("id, nivelPermissao")
        .eq("id", user_id)
        .execute()
    )
    if not r.data or len(r.data) == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado")
    if r.data[0].get("nivelPermissao") is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuário já foi aprovado",
        )
    supabase.table(LOGIN_TABLE_NAME).update(
        {"nivelPermissao": body.nivelPermissao}
    ).eq("id", user_id).execute()
    return {"message": "Usuário aprovado com sucesso"}
