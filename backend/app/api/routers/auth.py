"""Módulo Registro y Autenticación: UC-01 Identificarse (RF-07, RF-09, RF-10)."""
from fastapi import APIRouter, BackgroundTasks, status

from app.core.deps import DbSession, Gestor, UsuarioActual
from app.core.security import crear_token_acceso
from app.patterns.observer import Eventos
from app.schemas.auth import LoginIn, RecuperarIn, RegistroIn, RestablecerIn, TokenOut, UsuarioOut
from app.schemas.comun import Mensaje
from app.services import auth_service

router = APIRouter(prefix="/api/auth", tags=["Autenticación"])


def _token(usuario) -> TokenOut:
    token, expira = crear_token_acceso(usuario.id, usuario.rol.value)
    return TokenOut(access_token=token, expira_en=expira, usuario=UsuarioOut.model_validate(usuario))


@router.post("/registro", response_model=TokenOut, status_code=status.HTTP_201_CREATED,
             summary="Registrarse (flujo 3a de UC-01: queda con sesión iniciada)")
async def registro(datos: RegistroIn, db: DbSession, gestor: Gestor, tareas: BackgroundTasks):
    usuario = await auth_service.registrar(db, datos)
    await db.commit()
    gestor.notificar_en_segundo_plano(
        tareas, Eventos.USUARIO_REGISTRADO,
        {"usuario_id": usuario.id, "tipo_perfil": datos.tipo_perfil, "perfil_publico": datos.perfil_publico},
        actor_id=usuario.id,
    )
    return _token(usuario)


@router.post("/login", response_model=TokenOut,
             responses={401: {"description": "Datos incorrectos"}, 403: {"description": "Cuenta suspendida"}},
             summary="Iniciar sesión (UC-01)")
async def login(datos: LoginIn, db: DbSession):
    usuario = await auth_service.autenticar(db, datos.email, datos.password)
    return _token(usuario)


@router.post("/recuperar", response_model=Mensaje, status_code=status.HTTP_202_ACCEPTED,
             summary="Recuperar contraseña (flujo 3b de UC-01)")
async def recuperar(datos: RecuperarIn, db: DbSession, gestor: Gestor, tareas: BackgroundTasks):
    usuario = await auth_service.solicitar_recuperacion(db, datos.email)
    await db.commit()
    if usuario is not None:
        gestor.notificar_en_segundo_plano(tareas, Eventos.RECUPERACION_SOLICITADA,
                                          {"usuario_id": usuario.id}, actor_id=usuario.id)
    # Respuesta idéntica exista o no la cuenta (no revela correos registrados)
    return Mensaje(mensaje="Si el correo está registrado, te enviamos un enlace para restablecer tu contraseña.")


@router.post("/restablecer", response_model=Mensaje, summary="Definir nueva contraseña con el enlace recibido")
async def restablecer(datos: RestablecerIn, db: DbSession, gestor: Gestor, tareas: BackgroundTasks):
    usuario = await auth_service.restablecer(db, datos.token, datos.password)
    await db.commit()
    gestor.notificar_en_segundo_plano(tareas, Eventos.CONTRASENA_RESTABLECIDA,
                                      {"usuario_id": usuario.id}, actor_id=usuario.id)
    return Mensaje(mensaje="Tu contraseña fue actualizada. Ya puedes iniciar sesión.")


@router.get("/me", response_model=UsuarioOut, summary="Usuario de la sesión actual")
async def me(usuario: UsuarioActual):
    return usuario
