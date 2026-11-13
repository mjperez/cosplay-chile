"""Consultas exclusivas del panel de administración.

Se mantienen separadas de los repositorios públicos por una razón de
seguridad: los listados de la bandeja editorial **deben** poder ver los
borradores y los temas ocultos, mientras que los repositorios públicos los
filtran a propósito. Mezclar ambos en una misma función con una bandera
`incluir_ocultos` deja un interruptor olvidable en código que sirve a
visitantes anónimos.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Select, delete, func, select
from sqlalchemy.orm import Session

from app.models.comunidad import DesafioMensual, ForoRespuesta, ForoTema
from app.models.contenido import CategoriaContenido, Contenido
from app.models.directorio import ComunidadGrupo, DondeComprar, Proveedor
from app.models.evento import EventoCosplay, ParticipacionEvento
from app.models.usuario import Usuario


def _contar(sesion: Session, modelo: type, condicion=None) -> int:
    consulta = select(func.count()).select_from(modelo)
    if condicion is not None:
        consulta = consulta.where(condicion)
    return sesion.scalar(consulta) or 0


def resumen(sesion: Session) -> dict:
    """Un conteo por tabla. Se devuelve como dict y el schema lo valida."""
    return {
        "usuarios": _contar(sesion, Usuario),
        "usuarios_activos": _contar(sesion, Usuario, Usuario.activo.is_(True)),
        "contenido_pendiente": _contar(sesion, Contenido, Contenido.estado == "pendiente"),
        "contenido_publicado": _contar(sesion, Contenido, Contenido.estado == "publicado"),
        "contenido_rechazado": _contar(sesion, Contenido, Contenido.estado == "rechazado"),
        "eventos": _contar(sesion, EventoCosplay),
        "inscripciones": _contar(sesion, ParticipacionEvento),
        "temas": _contar(sesion, ForoTema),
        "temas_abiertos": _contar(sesion, ForoTema, ForoTema.estado == "abierto"),
        "respuestas": _contar(sesion, ForoRespuesta),
        "desafios": _contar(sesion, DesafioMensual),
        "tiendas": _contar(sesion, DondeComprar),
        "grupos": _contar(sesion, ComunidadGrupo),
        "proveedores": _contar(sesion, Proveedor),
        "categorias": _contar(sesion, CategoriaContenido),
        "generado_en": datetime.now(timezone.utc).replace(tzinfo=None),
    }


def _conteo_respuestas():
    """Subconsulta correlacionada: mismo patrón que el repositorio público."""
    return (
        select(func.count())
        .select_from(ForoRespuesta)
        .where(ForoRespuesta.id_tema == ForoTema.id_tema)
        .correlate(ForoTema)
        .scalar_subquery()
    )


def _consulta_temas() -> Select:
    return select(ForoTema, Usuario.nombre, _conteo_respuestas()).join(
        Usuario, Usuario.id_usuario == ForoTema.id_creador
    )


def listar_temas(
    sesion: Session,
    *,
    estado: str | None = None,
    limite: int = 50,
    desplazamiento: int = 0,
) -> tuple[int, list[tuple[ForoTema, str, int]]]:
    """Lista **todos** los temas, incluidos los ocultos, para moderación."""
    condicion = ForoTema.estado == estado if estado else None

    total = _contar(sesion, ForoTema, condicion)

    # Se ordena y pagina en SQL, no en Python, para no traer todo el foro.
    consulta = _consulta_temas()
    if condicion is not None:
        consulta = consulta.where(condicion)
    filas = sesion.execute(
        consulta.order_by(ForoTema.creado_en.desc())
        .limit(limite)
        .offset(desplazamiento)
    ).all()
    return total, [(fila[0], fila[1], fila[2] or 0) for fila in filas]


def obtener_tema(sesion: Session, id_tema: uuid.UUID) -> tuple[ForoTema, str, int] | None:
    """A diferencia del repositorio público, encuentra también un tema oculto."""
    fila = sesion.execute(
        _consulta_temas().where(ForoTema.id_tema == id_tema)
    ).first()
    if fila is None:
        return None
    return fila[0], fila[1], fila[2] or 0


def obtener_contenido(sesion: Session, id_contenido: uuid.UUID) -> Contenido | None:
    """Sin filtro de estado: la bandeja editorial necesita los borradores."""
    return sesion.get(Contenido, id_contenido)


def obtener_evento(sesion: Session, id_evento: uuid.UUID) -> EventoCosplay | None:
    return sesion.get(EventoCosplay, id_evento)


def eliminar_evento(sesion: Session, evento: EventoCosplay) -> None:
    """Borra primero las inscripciones: el cascade de la FK no está activo en SQLite."""
    sesion.execute(
        delete(ParticipacionEvento).where(ParticipacionEvento.id_evento == evento.id_evento)
    )
    sesion.delete(evento)
    sesion.flush()
