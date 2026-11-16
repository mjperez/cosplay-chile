"""Formulario de contacto (RF-40). Público: lo usa también una cuenta suspendida (UC-01, exc. 2)."""
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, status
from pydantic import BaseModel, EmailStr, StringConstraints

from app.core.deps import DbSession, Gestor, UsuarioOpcional
from app.models.enums import TipoContacto
from app.models.interaccion import Contacto
from app.patterns.observer import Eventos
from app.schemas.comun import Mensaje

router = APIRouter(prefix="/api/contacto", tags=["Moderación y seguridad"])


class ContactoIn(BaseModel):
    nombre: Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=120)]
    email: EmailStr
    tipo: TipoContacto = TipoContacto.DUDA
    asunto: Annotated[str, StringConstraints(strip_whitespace=True, min_length=3, max_length=200)]
    mensaje: Annotated[str, StringConstraints(strip_whitespace=True, min_length=10, max_length=5000)]


@router.post("", response_model=Mensaje, status_code=status.HTTP_201_CREATED, summary="Enviar un mensaje al equipo")
async def enviar_contacto(datos: ContactoIn, db: DbSession, gestor: Gestor, tareas: BackgroundTasks,
                          usuario: UsuarioOpcional):
    contacto = Contacto(**datos.model_dump(), usuario_id=usuario.id if usuario else None)
    db.add(contacto)
    await db.commit()
    gestor.notificar_en_segundo_plano(
        tareas, Eventos.CONTACTO_RECIBIDO,
        {"contacto_id": contacto.id, "asunto": contacto.asunto, "tipo": contacto.tipo},
        actor_id=usuario.id if usuario else None,
    )
    return Mensaje(mensaje="Recibimos tu mensaje. El equipo de moderación te responderá por correo.")
