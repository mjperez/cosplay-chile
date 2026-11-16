"""Gestionar Perfil (UC4, RF-07, RF-08, RF-10) y derecho a supresión (RNF-11)."""
import uuid

from fastapi import APIRouter, BackgroundTasks, HTTPException, status

from app.core.deps import DbSession, Gestor, UsuarioActual
from app.models.enums import EstadoUsuario
from app.models.usuario import Usuario
from app.patterns.observer import Eventos
from app.schemas.auth import PerfilPublicoOut, PerfilUpdate, UsuarioOut
from app.schemas.comun import Mensaje
from app.services import auth_service
from app.services.directorio_sync import sincronizar_ficha

router = APIRouter(prefix="/api/perfil", tags=["Perfil"])


@router.put("", response_model=UsuarioOut, summary="Actualizar mi perfil")
async def actualizar_perfil(datos: PerfilUpdate, usuario: UsuarioActual, db: DbSession):
    cambios = datos.model_dump(exclude_unset=True, mode="json")
    if "nombre" in cambios:
        usuario.nombre = cambios.pop("nombre")
    for campo, valor in cambios.items():
        setattr(usuario.perfil, campo, valor)
    await db.flush()
    await sincronizar_ficha(db, usuario)
    await db.commit()
    await db.refresh(usuario)
    return usuario


@router.delete("", response_model=Mensaje, summary="Eliminar mi cuenta (derecho a supresión)")
async def eliminar_mi_cuenta(usuario: UsuarioActual, db: DbSession, gestor: Gestor, tareas: BackgroundTasks):
    usuario_id = usuario.id
    await auth_service.eliminar_cuenta(db, usuario)
    await db.commit()
    gestor.notificar_en_segundo_plano(tareas, Eventos.CUENTA_ELIMINADA, {"usuario_id": usuario_id})
    return Mensaje(mensaje="Tu cuenta y tus datos personales fueron eliminados.")


@router.get("/{usuario_id}", response_model=PerfilPublicoOut, summary="Perfil público de otra persona")
async def perfil_publico(usuario_id: uuid.UUID, db: DbSession):
    usuario = await db.get(Usuario, usuario_id)
    if usuario is None or usuario.estado != EstadoUsuario.ACTIVO or not usuario.perfil.perfil_publico:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Este perfil no es público")
    return PerfilPublicoOut(id=usuario.id, nombre=usuario.nombre, perfil=usuario.perfil)
