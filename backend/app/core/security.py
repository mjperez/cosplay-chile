"""Hash de contraseñas y emisión de tokens JWT."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from app.core.config import Settings

# bcrypt solo considera los primeros 72 bytes. Se valida en el esquema para no
# aceptar contraseñas que en la práctica se truncan.
MAX_BYTES_PASSWORD = 72

_senuelo: bytes | None = None


def _hash_senuelo() -> bytes:
    """Hash de referencia para igualar tiempos cuando el correo no existe.

    Sin esto, comparar una contraseña contra un usuario inexistente responde
    en microsegundos y contra uno existente tarda lo que tarda bcrypt. Esa
    diferencia permite enumerar cuentas registradas midiendo la latencia.
    """
    global _senuelo
    if _senuelo is None:
        _senuelo = bcrypt.hashpw(b"senuelo-de-tiempo-constante", bcrypt.gensalt(rounds=4))
    return _senuelo


def hash_password(password: str, settings: Settings) -> str:
    """Devuelve el hash bcrypt de la contraseña. Nunca se guarda el original."""
    if len(password.encode("utf-8")) > MAX_BYTES_PASSWORD:
        raise ValueError("la contraseña supera los 72 bytes admitidos por bcrypt")
    sal = bcrypt.gensalt(rounds=settings.bcrypt_rounds)
    return bcrypt.hashpw(password.encode("utf-8"), sal).decode("utf-8")


def verificar_password(password: str, password_hash: str) -> bool:
    """Compara en tiempo constante. Un hash corrupto cuenta como fallo."""
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def verificar_senuelo(password: str) -> None:
    """Quema el mismo tiempo que una verificación real. Siempre falla."""
    try:
        bcrypt.checkpw(password.encode("utf-8"), _hash_senuelo())
    except (ValueError, TypeError):
        pass


def crear_token_acceso(
    *, id_usuario: uuid.UUID, rol: str, settings: Settings
) -> tuple[str, int]:
    """Emite un JWT firmado. Devuelve el token y su vigencia en segundos."""
    ahora = datetime.now(timezone.utc)
    expira = ahora + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {
        "sub": str(id_usuario),
        "rol": rol,
        "iat": int(ahora.timestamp()),
        "exp": int(expira.timestamp()),
        "jti": uuid.uuid4().hex,
    }
    token = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    return token, settings.jwt_expire_minutes * 60


def decodificar_token(token: str, settings: Settings) -> dict:
    """Valida firma y vigencia.

    Lanza `jwt.ExpiredSignatureError` si venció y `jwt.InvalidTokenError` si la
    firma no corresponde o el token está malformado.
    """
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
