"""Reglas de negocio de registro y autenticación."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.security import hash_password, verificar_password, verificar_senuelo
from app.models.usuario import Usuario
from app.repositories import intento_login as repo_intentos
from app.repositories import usuario as repo_usuarios
from app.schemas.auth import RegistroEntrada

# Política de bloqueo: cinco fallos en quince minutos.
MAX_INTENTOS_FALLIDOS = 5
VENTANA_BLOQUEO = timedelta(minutes=15)


class CorreoYaRegistrado(Exception):
    """El correo ya existe. Solo se usa en el registro."""


class CredencialesInvalidas(Exception):
    """Correo inexistente o contraseña incorrecta. No distingue cuál."""


class CuentaBloqueada(Exception):
    """Demasiados fallos recientes. Lleva los segundos que faltan."""

    def __init__(self, segundos: int) -> None:
        self.segundos = max(int(segundos), 1)
        super().__init__(f"cuenta bloqueada por {self.segundos} segundos")


class CuentaInactiva(Exception):
    """La cuenta existe pero está deshabilitada."""


def registrar(sesion: Session, datos: RegistroEntrada, settings: Settings) -> Usuario:
    if repo_usuarios.obtener_por_correo(sesion, datos.correo) is not None:
        raise CorreoYaRegistrado(datos.correo)

    return repo_usuarios.crear(
        sesion,
        nombre=datos.nombre,
        correo=datos.correo,
        password_hash=hash_password(datos.password, settings),
        rol=datos.rol,
        region=datos.region,
        consentimiento_fecha=datetime.now(timezone.utc),
        consentimiento_version=datos.consentimiento_version,
    )


def _segundos_de_bloqueo(sesion: Session, correo: str, desde: datetime, ahora: datetime) -> int:
    primero = repo_intentos.primer_fallido_desde(sesion, correo, desde)
    if primero is None:
        return 0
    # SQLite devuelve la marca sin zona horaria; se asume UTC porque así se
    # escribió.
    if primero.tzinfo is None:
        primero = primero.replace(tzinfo=timezone.utc)
    return int((primero + VENTANA_BLOQUEO - ahora).total_seconds())


def _registrar_fallo(sesion: Session, correo: str, ip: str | None) -> None:
    """Guarda el intento fallido y lo confirma de inmediato.

    El endpoint va a responder 401, y eso hace que la sesión se revierta al
    salir. Si el intento no se confirma aquí, el contador de bloqueo nunca
    avanza y la política de cinco intentos no se cumple.
    """
    repo_intentos.registrar(sesion, correo=correo, ip=ip, exitoso=False)
    sesion.commit()


def autenticar(
    sesion: Session,
    *,
    correo: str,
    password: str,
    ip: str | None,
    settings: Settings,
) -> Usuario:
    ahora = datetime.now(timezone.utc)
    desde = ahora - VENTANA_BLOQUEO

    if repo_intentos.contar_fallidos_desde(sesion, correo, desde) >= MAX_INTENTOS_FALLIDOS:
        raise CuentaBloqueada(_segundos_de_bloqueo(sesion, correo, desde, ahora))

    usuario = repo_usuarios.obtener_por_correo(sesion, correo)

    if usuario is None:
        # Mismo costo de CPU que una verificación real: sin esto se puede
        # enumerar correos midiendo la latencia de la respuesta.
        verificar_senuelo(password)
        _registrar_fallo(sesion, correo, ip)
        raise CredencialesInvalidas()

    if not verificar_password(password, usuario.password_hash):
        _registrar_fallo(sesion, correo, ip)
        raise CredencialesInvalidas()

    if not usuario.activo:
        raise CuentaInactiva()

    repo_intentos.registrar(sesion, correo=correo, ip=ip, exitoso=True)
    repo_intentos.borrar_fallidos(sesion, correo)
    return usuario
