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
    UsuarioAdminResponse,
    AtualizarNivelRequest,
    RedefinirSenhaRequest,
)
from auth.deps import get_current_user, require_permission
from auth.jwt import create_access_token

router = APIRouter(prefix="/auth", tags=["Auth"])


def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _check_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))


def _can_assign_level(
    actor_level: int, target_current_level: int | None, new_level: int, *, is_approval: bool
) -> bool:
    """Valida regras de atribuição/alteração de nível por perfil logado."""
    if actor_level == 0:
        return True
    if actor_level != 1:
        return False

    # Nível 1 nunca pode atribuir níveis 0 ou 1
    if new_level in (0, 1):
        return False

    # Aprovação de pendente por nível 1: apenas 2 ou 3
    if is_approval:
        return True

    # Alteração em usuário já aprovado por nível 1: somente 2 <-> 3
    if target_current_level not in (2, 3):
        return False
    return new_level in (2, 3)


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
    """Aprova um usuário e atribui nivelPermissao. Apenas níveis 0 e 1 podem aprovar.
    Regra: nível 0 atribui 0..3; nível 1 atribui apenas 2 ou 3.
    """
    nivel_logado = current_user["nivelPermissao"]
    supabase = get_supabase_client()
    r = (
        supabase.table(LOGIN_TABLE_NAME)
        .select("id, nivelPermissao")
        .eq("id", user_id)
        .execute()
    )
    if not r.data or len(r.data) == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado")
    target_level = r.data[0].get("nivelPermissao")
    if target_level is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuário já foi aprovado",
        )
    if not _can_assign_level(nivel_logado, target_level, body.nivelPermissao, is_approval=True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não tem permissão para atribuir este nível",
        )
    supabase.table(LOGIN_TABLE_NAME).update(
        {"nivelPermissao": body.nivelPermissao}
    ).eq("id", user_id).execute()
    return {"message": "Usuário aprovado com sucesso"}


@router.get("/usuarios", response_model=list[UsuarioAdminResponse])
def listar_usuarios(current_user: dict = Depends(require_permission(1))):
    """Lista todos os usuários (pendentes e aprovados). Apenas níveis 0 e 1."""
    supabase = get_supabase_client()
    r = (
        supabase.table(LOGIN_TABLE_NAME)
        .select("id, nome, email, nivelPermissao, created_at")
        .order("id", desc=False)
        .execute()
    )
    out = []
    for row in (r.data or []):
        out.append(
            UsuarioAdminResponse(
                id=row["id"],
                nome=row["nome"],
                email=row["email"],
                nivelPermissao=row.get("nivelPermissao"),
                created_at=row.get("created_at"),
            )
        )
    return out


@router.patch("/usuarios/{user_id}/nivel")
def atualizar_nivel_usuario(
    user_id: int,
    body: AtualizarNivelRequest,
    current_user: dict = Depends(require_permission(1)),
):
    """Atualiza nível de usuário já aprovado.
    Regra: nível 0 atribui 0..3; nível 1 altera apenas entre 2 e 3.
    """
    supabase = get_supabase_client()
    nivel_logado = current_user["nivelPermissao"]
    logged_id = current_user["id"]

    r = (
        supabase.table(LOGIN_TABLE_NAME)
        .select("id, nivelPermissao")
        .eq("id", user_id)
        .execute()
    )
    if not r.data or len(r.data) == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado")

    target_level = r.data[0].get("nivelPermissao")
    if target_level is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuário pendente. Use a aprovação inicial.",
        )

    if user_id == logged_id and body.nivelPermissao != target_level:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não é permitido alterar o próprio nível de permissão",
        )

    if not _can_assign_level(nivel_logado, target_level, body.nivelPermissao, is_approval=False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não tem permissão para definir este nível",
        )

    supabase.table(LOGIN_TABLE_NAME).update(
        {"nivelPermissao": body.nivelPermissao}
    ).eq("id", user_id).execute()
    return {"message": "Nível de permissão atualizado com sucesso"}


@router.delete("/usuarios/{user_id}")
def excluir_usuario(
    user_id: int,
    current_user: dict = Depends(require_permission(1)),
):
    """Exclui usuário com regras de segurança.
    - Sem autoexclusão
    - Não permite excluir o último usuário nível 0
    """
    supabase = get_supabase_client()
    logged_id = current_user["id"]

    if user_id == logged_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não é permitido excluir o próprio usuário",
        )

    r = (
        supabase.table(LOGIN_TABLE_NAME)
        .select("id, nivelPermissao")
        .eq("id", user_id)
        .execute()
    )
    if not r.data or len(r.data) == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado")

    target_level = r.data[0].get("nivelPermissao")
    if target_level == 0:
        lvl0 = (
            supabase.table(LOGIN_TABLE_NAME)
            .select("id", count="exact")
            .eq("nivelPermissao", 0)
            .execute()
        )
        total_lvl0 = lvl0.count or 0
        if total_lvl0 <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Não é permitido excluir o último usuário de nível 0",
            )

    supabase.table(LOGIN_TABLE_NAME).delete().eq("id", user_id).execute()
    return {"message": "Usuário excluído com sucesso"}


@router.patch("/usuarios/{user_id}/senha")
def redefinir_senha_usuario(
    user_id: int,
    body: RedefinirSenhaRequest,
    current_user: dict = Depends(require_permission(0)),
):
    """Redefine senha de outro usuário.
    Apenas nível 0 pode redefinir senha e somente para alvos níveis 1, 2 ou 3.
    """
    supabase = get_supabase_client()
    logged_id = current_user["id"]

    if user_id == logged_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Use a opção de troca de senha da própria conta",
        )

    r = (
        supabase.table(LOGIN_TABLE_NAME)
        .select("id, nivelPermissao")
        .eq("id", user_id)
        .execute()
    )
    if not r.data or len(r.data) == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado")

    target_level = r.data[0].get("nivelPermissao")
    if target_level not in (1, 2, 3):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Redefinição permitida apenas para usuários níveis 1, 2 ou 3",
        )

    hashed = _hash_password(body.newPassword)
    supabase.table(LOGIN_TABLE_NAME).update({"password": hashed}).eq("id", user_id).execute()
    return {"message": "Senha redefinida com sucesso"}
