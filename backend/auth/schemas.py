"""Schemas Pydantic para autenticação e usuários"""
from pydantic import BaseModel, Field
from typing import Optional


class LoginRequest(BaseModel):
    email: str
    password: str


class RegistroRequest(BaseModel):
    nome: str = Field(..., min_length=1)
    email: str
    password: str = Field(..., min_length=8)


class UserResponse(BaseModel):
    id: int
    nome: str
    email: str
    nivelPermissao: Optional[int]

    class Config:
        from_attributes = True


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class AprovarRequest(BaseModel):
    nivelPermissao: int = Field(..., ge=0, le=3)


class UsuarioPendenteResponse(BaseModel):
    id: int
    nome: str
    email: str
    created_at: Optional[str] = None

    class Config:
        from_attributes = True


class UsuarioAdminResponse(BaseModel):
    id: int
    nome: str
    email: str
    nivelPermissao: Optional[int]
    created_at: Optional[str] = None

    class Config:
        from_attributes = True


class AtualizarNivelRequest(BaseModel):
    nivelPermissao: int = Field(..., ge=0, le=3)
