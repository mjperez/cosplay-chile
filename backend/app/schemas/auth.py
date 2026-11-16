import re
import uuid
from typing import Annotated

from pydantic import BaseModel, EmailStr, Field, StringConstraints, field_validator

from app.models.enums import EstadoUsuario, Region, Rol, TipoPerfil
from app.schemas.comun import ImagenRef, ModeloOrm, RedSocial, UrlSegura

Nombre = Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=120)]


def _password_robusta(valor: str) -> str:
    if len(valor) < 8:
        raise ValueError("La contraseña debe tener al menos 8 caracteres")
    if not re.search(r"[A-Za-zÁÉÍÓÚÑáéíóúñ]", valor) or not re.search(r"\d", valor):
        raise ValueError("La contraseña debe combinar letras y números")
    return valor


class RegistroIn(BaseModel):
    nombre: Nombre
    email: EmailStr
    password: str = Field(max_length=128)
    tipo_perfil: TipoPerfil = TipoPerfil.COSPLAYER
    region: Region | None = None
    # RF-10: opt-in al directorio público (por defecto NO)
    perfil_publico: bool = False
    # RNF-11 / Ley 21.719: consentimiento explícito
    acepta_privacidad: bool

    _v_password = field_validator("password")(_password_robusta)

    @field_validator("acepta_privacidad")
    @classmethod
    def _consentimiento(cls, valor: bool) -> bool:
        if not valor:
            raise ValueError("Debes aceptar la política de privacidad para crear tu cuenta")
        return valor


class LoginIn(BaseModel):
    email: Annotated[str, StringConstraints(strip_whitespace=True, max_length=254)]
    password: Annotated[str, StringConstraints(max_length=128)]


class RecuperarIn(BaseModel):
    email: EmailStr


class RestablecerIn(BaseModel):
    token: Annotated[str, StringConstraints(min_length=10, max_length=200)]
    password: str = Field(max_length=128)

    _v_password = field_validator("password")(_password_robusta)


class PerfilOut(ModeloOrm):
    tipo_perfil: TipoPerfil
    biografia: str | None = None
    region: Region | None = None
    redes_sociales: list[RedSocial] = []
    portafolio: list[ImagenRef] = []
    especialidad: str | None = None
    disponibilidad: str | None = None
    avatar_url: str | None = None
    perfil_publico: bool = False


class UsuarioOut(ModeloOrm):
    id: uuid.UUID
    nombre: str
    email: str
    rol: Rol
    estado: EstadoUsuario
    perfil: PerfilOut | None = None


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expira_en: int
    usuario: UsuarioOut


class PerfilUpdate(BaseModel):
    nombre: Nombre | None = None
    tipo_perfil: TipoPerfil | None = None
    biografia: Annotated[str, StringConstraints(strip_whitespace=True, max_length=2000)] | None = None
    region: Region | None = None
    redes_sociales: list[RedSocial] | None = Field(default=None, max_length=10)
    portafolio: list[ImagenRef] | None = Field(default=None, max_length=20)
    especialidad: Annotated[str, StringConstraints(strip_whitespace=True, max_length=120)] | None = None
    disponibilidad: Annotated[str, StringConstraints(strip_whitespace=True, max_length=120)] | None = None
    avatar_url: UrlSegura | None = None
    perfil_publico: bool | None = None


class PerfilPublicoOut(BaseModel):
    id: uuid.UUID
    nombre: str
    perfil: PerfilOut
