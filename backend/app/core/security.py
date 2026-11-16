"""Hash de contraseñas (argon2, RNF-07) y tokens JWT (UC-01)."""
import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone

import jwt
from pwdlib import PasswordHash

from app.core.config import get_settings

_hasher = PasswordHash.recommended()  # argon2id

# Hash ficticio para igualar el tiempo de respuesta cuando el correo no existe
_HASH_FICTICIO = _hasher.hash("contraseña-inexistente-para-igualar-tiempos")


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verificar_password(password: str, password_hash: str | None) -> bool:
    if not password_hash:
        _hasher.verify(password, _HASH_FICTICIO)
        return False
    try:
        return _hasher.verify(password, password_hash)
    except Exception:
        return False


def crear_token_acceso(usuario_id: uuid.UUID, rol: str) -> tuple[str, int]:
    s = get_settings()
    expira_en = s.jwt_expira_minutos * 60
    ahora = datetime.now(timezone.utc)
    payload = {
        "sub": str(usuario_id),
        "rol": rol,
        "iat": ahora,
        "exp": ahora + timedelta(seconds=expira_en),
    }
    return jwt.encode(payload, s.jwt_secret, algorithm=s.jwt_algoritmo), expira_en


def decodificar_token(token: str) -> dict:
    s = get_settings()
    return jwt.decode(token, s.jwt_secret, algorithms=[s.jwt_algoritmo], options={"require": ["exp", "sub"]})


def generar_token_recuperacion() -> tuple[str, str]:
    """Devuelve (token en claro para el enlace, hash SHA-256 que se guarda en BD)."""
    token = secrets.token_urlsafe(32)
    return token, hash_token(token)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()
