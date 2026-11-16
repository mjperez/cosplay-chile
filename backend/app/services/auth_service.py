"""Caso de Uso Cero: Identificarse (Tabla 5, Fig. 12) — registro, login, recuperación."""
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import (
    generar_token_recuperacion,
    hash_password,
    hash_token,
    verificar_password,
)
from app.models.directorio import DirectorioItem
from app.models.enums import EstadoUsuario
from app.models.interaccion import Favorito, Notificacion
from app.models.usuario import Perfil, TokenRecuperacion, Usuario
from app.schemas.auth import RegistroIn
from app.services.correo import enviar_correo_simulado
from app.services.directorio_sync import sincronizar_ficha

DATOS_INCORRECTOS = "Datos incorrectos"  # Excepción 1: no indica qué campo está mal
MENSAJE_SUSPENDIDA = (
    "Tu cuenta no está habilitada. Si crees que se trata de un error, "
    "escríbenos mediante el formulario de contacto."
)


def normalizar_email(email: str) -> str:
    return email.strip().lower()


async def buscar_por_email(db: AsyncSession, email: str) -> Usuario | None:
    return (
        await db.execute(select(Usuario).where(func.lower(Usuario.email) == normalizar_email(email)))
    ).scalar_one_or_none()


async def registrar(db: AsyncSession, datos: RegistroIn) -> Usuario:
    if await buscar_por_email(db, datos.email) is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Ya existe una cuenta con ese correo")
    usuario = Usuario(
        nombre=datos.nombre,
        email=normalizar_email(datos.email),
        password_hash=hash_password(datos.password),
        consentimiento_at=datetime.now(timezone.utc),
    )
    usuario.perfil = Perfil(
        tipo_perfil=datos.tipo_perfil,
        region=datos.region,
        perfil_publico=datos.perfil_publico,
        redes_sociales=[],
        portafolio=[],
    )
    db.add(usuario)
    await db.flush()
    await sincronizar_ficha(db, usuario)
    return usuario


async def autenticar(db: AsyncSession, email: str, password: str) -> Usuario:
    """Pasos 3-4 de UC-01. Lanza 401 genérico o 403 si la cuenta está suspendida.

    OWASP A07: tras N intentos fallidos consecutivos (login_max_intentos),
    la cuenta se bloquea temporalmente durante login_bloqueo_minutos.
    """
    s = get_settings()
    ahora = datetime.now(timezone.utc)
    usuario = await buscar_por_email(db, email)

    # Si la cuenta existe y está bloqueada, rechazar sin procesar la contraseña
    if usuario is not None and usuario.bloqueado_hasta is not None and usuario.bloqueado_hasta > ahora:
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            {
                "codigo": "CUENTA_BLOQUEADA",
                "mensaje": (
                    f"Demasiados intentos fallidos. Intenta nuevamente en "
                    f"{int((usuario.bloqueado_hasta - ahora).total_seconds() // 60) + 1} minutos."
                ),
            },
        )

    valido = verificar_password(password, usuario.password_hash if usuario else None)
    if usuario is None or not valido or usuario.estado == EstadoUsuario.ELIMINADO:
        # Incrementar contador solo si el usuario existe (no revela correos no registrados)
        if usuario is not None and usuario.estado != EstadoUsuario.ELIMINADO:
            usuario.intentos_fallidos += 1
            if usuario.intentos_fallidos >= s.login_max_intentos:
                usuario.bloqueado_hasta = ahora + timedelta(minutes=s.login_bloqueo_minutos)
            await db.flush()
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, DATOS_INCORRECTOS)

    # Login exitoso: reiniciar contador
    usuario.intentos_fallidos = 0
    usuario.bloqueado_hasta = None
    await db.flush()

    # La suspensión se revela solo con credenciales correctas (no filtra qué correos existen)
    if usuario.estado == EstadoUsuario.SUSPENDIDO:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            {"codigo": "CUENTA_SUSPENDIDA", "mensaje": MENSAJE_SUSPENDIDA},
        )
    return usuario


async def solicitar_recuperacion(db: AsyncSession, email: str) -> Usuario | None:
    """Flujo 3b: envía el enlace (simulado) solo si la cuenta existe y está activa."""
    usuario = await buscar_por_email(db, email)
    if usuario is None or usuario.estado != EstadoUsuario.ACTIVO:
        return None
    s = get_settings()
    # Invalida tokens anteriores sin usar
    await db.execute(
        update(TokenRecuperacion)
        .where(TokenRecuperacion.usuario_id == usuario.id, TokenRecuperacion.usado.is_(False))
        .values(usado=True)
    )
    token, token_hash = generar_token_recuperacion()
    db.add(
        TokenRecuperacion(
            usuario_id=usuario.id,
            token_hash=token_hash,
            expira_at=datetime.now(timezone.utc) + timedelta(minutes=s.recuperacion_expira_minutos),
        )
    )
    enlace = f"{s.frontend_url}/restablecer?token={token}"
    enviar_correo_simulado(
        usuario.email,
        "Restablece tu contraseña de Cosplay Chile",
        f"Hola {usuario.nombre}:\nPara crear una nueva contraseña abre este enlace "
        f"(vence en {s.recuperacion_expira_minutos} minutos):\n{enlace}\n"
        "Si no lo pediste, ignora este mensaje.",
    )
    return usuario


async def restablecer(db: AsyncSession, token: str, nueva_password: str) -> Usuario:
    registro = (
        await db.execute(select(TokenRecuperacion).where(TokenRecuperacion.token_hash == hash_token(token)))
    ).scalar_one_or_none()
    ahora = datetime.now(timezone.utc)
    if registro is None or registro.usado or registro.expira_at < ahora:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "El enlace no es válido o ya expiró. Solicita uno nuevo.")
    usuario = await db.get(Usuario, registro.usuario_id)
    if usuario is None or usuario.estado != EstadoUsuario.ACTIVO:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "El enlace no es válido o ya expiró. Solicita uno nuevo.")
    usuario.password_hash = hash_password(nueva_password)
    registro.usado = True
    return usuario


async def eliminar_cuenta(db: AsyncSession, usuario: Usuario) -> None:
    """Derecho a supresión (RNF-11, Ley 21.719): se anonimizan los datos personales.

    Las publicaciones se conservan para no romper hilos ajenos, pero quedan
    firmadas como 'Usuario eliminado'.
    """
    usuario.nombre = "Usuario eliminado"
    usuario.email = f"eliminado-{usuario.id}@cosplaychile.invalid"
    usuario.password_hash = hash_password(secrets.token_urlsafe(32))
    usuario.estado = EstadoUsuario.ELIMINADO
    if usuario.perfil:
        p = usuario.perfil
        p.biografia = None
        p.redes_sociales = []
        p.portafolio = []
        p.especialidad = None
        p.disponibilidad = None
        p.avatar_url = None
        p.region = None
        p.perfil_publico = False
    await db.execute(update(DirectorioItem).where(DirectorioItem.usuario_id == usuario.id)
                     .values(activo=False, usuario_id=None, contacto=None))
    for modelo in (Favorito, Notificacion, TokenRecuperacion):
        await db.execute(modelo.__table__.delete().where(modelo.usuario_id == usuario.id))
