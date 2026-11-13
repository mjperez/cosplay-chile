"""Panel de administración. Todos los endpoints exigen rol `administrador`.

La dependencia va en el router, no en cada endpoint: si mañana se agrega una
ruta acá, ya nace protegida. El prefijo `/admin` agrupa las operaciones de
gestión para que el cliente del panel hable con una sola raíz y no mezcle
rutas públicas con rutas privilegiadas.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_usuario_actual, requiere_admin
from app.core.database import get_db
from app.models.comunidad import DesafioMensual, ForoTema
from app.models.evento import EventoCosplay
from app.models.usuario import Usuario
from app.repositories import admin as repo_admin
from app.repositories import contenido as repo_contenido
from app.repositories import evento as repo_evento
from app.repositories import usuario as repo_usuarios
from app.schemas.admin import (
    EstadoTemaEntrada,
    EstadoUsuarioEntrada,
    GrupoEntrada,
    ResumenAdmin,
    TiendaEntrada,
)
from app.schemas.auth import PaginaUsuarios, UsuarioPublico
from app.schemas.comunidad import (
    DesafioEntrada,
    DesafioPublico,
    GanadorEntrada,
    PaginaDesafios,
    PaginaTemas,
    TemaPublico,
)
from app.schemas.contenido import (
    CategoriaEntrada,
    CategoriaPublica,
    ContenidoPublico,
    PaginaContenido,
)
from app.schemas.directorio import GrupoPublico, TiendaPublica
from app.schemas.evento import EventoEntrada, EventoPublico, PaginaEventos
from app.services import admin as servicio_admin
from app.services import comunidad as servicio_comunidad
from app.services import contenido as servicio_contenido
from app.services import evento as servicio_evento

router = APIRouter(
    prefix="/admin",
    tags=["administración"],
    dependencies=[Depends(requiere_admin)],
)


# --- Convertidores --------------------------------------------------------

def _evento_publico(sesion: Session, evento: EventoCosplay) -> EventoPublico:
    return EventoPublico(
        id_evento=evento.id_evento,
        nombre=evento.nombre,
        tipo=evento.tipo,
        fecha_inicio=evento.fecha_inicio,
        fecha_fin=evento.fecha_fin,
        lugar=evento.lugar,
        region=evento.region,
        enlace_oficial=evento.enlace_oficial,
        total_participantes=repo_evento.contar_participaciones(sesion, evento.id_evento),
        creado_en=evento.creado_en,
    )


def _tema_publico(tema: ForoTema, nombre: str, total: int) -> TemaPublico:
    return TemaPublico(
        id_tema=tema.id_tema,
        id_creador=tema.id_creador,
        titulo=tema.titulo,
        categoria=tema.categoria,
        contenido=tema.contenido,
        estado=tema.estado,
        nombre_autor=nombre,
        total_respuestas=total,
        creado_en=tema.creado_en,
    )


def _desafio_publico(desafio: DesafioMensual, nombre_ganador: str | None) -> DesafioPublico:
    return DesafioPublico(
        id_desafio=desafio.id_desafio,
        titulo=desafio.titulo,
        mes=desafio.mes,
        id_ganador=desafio.id_ganador,
        nombre_ganador=nombre_ganador,
        creado_en=desafio.creado_en,
    )


# --- Resumen --------------------------------------------------------------

@router.get(
    "/resumen",
    response_model=ResumenAdmin,
    summary="Contadores de la plataforma para la portada del panel",
)
def resumen(sesion: Session = Depends(get_db)) -> ResumenAdmin:
    return servicio_admin.resumen(sesion)


# --- Usuarios -------------------------------------------------------------

@router.get(
    "/usuarios",
    response_model=PaginaUsuarios,
    summary="Listar cuentas registradas",
)
def listar_usuarios(
    limite: int = Query(20, ge=1, le=100),
    desplazamiento: int = Query(0, ge=0),
    sesion: Session = Depends(get_db),
) -> PaginaUsuarios:
    total = repo_usuarios.contar(sesion)
    elementos = repo_usuarios.listar(sesion, limite=limite, desplazamiento=desplazamiento)
    return PaginaUsuarios(
        total=total,
        limite=limite,
        desplazamiento=desplazamiento,
        elementos=[UsuarioPublico.model_validate(u) for u in elementos],
    )


@router.patch(
    "/usuarios/{id_usuario}",
    response_model=UsuarioPublico,
    summary="Activar o desactivar una cuenta",
)
def cambiar_estado_usuario(
    id_usuario: uuid.UUID,
    datos: EstadoUsuarioEntrada,
    administrador: Usuario = Depends(get_usuario_actual),
    sesion: Session = Depends(get_db),
) -> UsuarioPublico:
    try:
        usuario = servicio_admin.cambiar_estado_usuario(
            sesion, id_usuario, datos.activo, administrador
        )
    except servicio_admin.UsuarioNoEncontrado:
        raise HTTPException(404, "usuario no encontrado")
    except servicio_admin.AutoBloqueo:
        raise HTTPException(409, "no puedes desactivar tu propia cuenta de administrador")
    return UsuarioPublico.model_validate(usuario)


# --- Bandeja editorial ----------------------------------------------------

@router.get(
    "/contenido",
    response_model=PaginaContenido,
    summary="Listar contenido en cualquier estado, incluidos los borradores",
)
def listar_contenido(
    estado: str | None = Query(None, description="pendiente, publicado o rechazado"),
    tipo: str | None = Query(None, description="guia, entrevista o articulo"),
    limite: int = Query(20, ge=1, le=100),
    desplazamiento: int = Query(0, ge=0),
    sesion: Session = Depends(get_db),
) -> PaginaContenido:
    """La bandeja editorial. Es el único lugar donde se ven los borradores."""
    total, elementos = repo_contenido.listar(
        sesion, estado=estado, tipo=tipo, limite=limite, desplazamiento=desplazamiento
    )
    return PaginaContenido(
        total=total,
        limite=limite,
        desplazamiento=desplazamiento,
        elementos=[ContenidoPublico.model_validate(c) for c in elementos],
    )


def _transicion_contenido(
    id_contenido: uuid.UUID, destino: str, sesion: Session
) -> ContenidoPublico:
    try:
        contenido = servicio_admin.cambiar_estado_contenido(sesion, id_contenido, destino)
    except servicio_admin.ContenidoNoEncontrado:
        raise HTTPException(404, "contenido no encontrado")
    except servicio_admin.TransicionInvalida as error:
        raise HTTPException(409, str(error))
    return ContenidoPublico.model_validate(contenido)


@router.post(
    "/contenido/{id_contenido}/publicar",
    response_model=ContenidoPublico,
    summary="Publicar un borrador",
)
def publicar_contenido(
    id_contenido: uuid.UUID, sesion: Session = Depends(get_db)
) -> ContenidoPublico:
    return _transicion_contenido(id_contenido, "publicado", sesion)


@router.post(
    "/contenido/{id_contenido}/rechazar",
    response_model=ContenidoPublico,
    summary="Rechazar un borrador",
)
def rechazar_contenido(
    id_contenido: uuid.UUID, sesion: Session = Depends(get_db)
) -> ContenidoPublico:
    return _transicion_contenido(id_contenido, "rechazado", sesion)


@router.post(
    "/contenido/{id_contenido}/borrador",
    response_model=ContenidoPublico,
    summary="Devolver un contenido a borrador",
)
def volver_a_borrador(
    id_contenido: uuid.UUID, sesion: Session = Depends(get_db)
) -> ContenidoPublico:
    return _transicion_contenido(id_contenido, "pendiente", sesion)


@router.get(
    "/categorias",
    response_model=list[CategoriaPublica],
    summary="Listar categorías editoriales",
)
def listar_categorias(sesion: Session = Depends(get_db)) -> list:
    return repo_contenido.listar_categorias(sesion)


@router.post(
    "/categorias",
    response_model=CategoriaPublica,
    status_code=status.HTTP_201_CREATED,
    summary="Crear una categoría editorial",
)
def crear_categoria(
    datos: CategoriaEntrada, sesion: Session = Depends(get_db)
) -> object:
    try:
        return servicio_contenido.crear_categoria(
            sesion, nombre=datos.nombre, descripcion=datos.descripcion
        )
    except servicio_contenido.CategoriaDuplicada as error:
        raise HTTPException(409, f"la categoría «{error.nombre}» ya existe")


# --- Calendario -----------------------------------------------------------

@router.get(
    "/eventos",
    response_model=PaginaEventos,
    summary="Listar todos los eventos con su número de inscritos",
)
def listar_eventos(
    limite: int = Query(50, ge=1, le=100),
    desplazamiento: int = Query(0, ge=0),
    sesion: Session = Depends(get_db),
) -> PaginaEventos:
    total, elementos = servicio_evento.listar(
        sesion, limite=limite, desplazamiento=desplazamiento
    )
    return PaginaEventos(
        total=total,
        limite=limite,
        desplazamiento=desplazamiento,
        elementos=[_evento_publico(sesion, e) for e in elementos],
    )


@router.post(
    "/eventos",
    response_model=EventoPublico,
    status_code=status.HTTP_201_CREATED,
    summary="Crear un evento",
)
def crear_evento(
    datos: EventoEntrada, sesion: Session = Depends(get_db)
) -> EventoPublico:
    return _evento_publico(sesion, servicio_evento.crear(sesion, datos))


@router.delete(
    "/eventos/{id_evento}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar un evento y sus inscripciones",
)
def eliminar_evento(
    id_evento: uuid.UUID, sesion: Session = Depends(get_db)
) -> Response:
    try:
        servicio_admin.eliminar_evento(sesion, id_evento)
    except servicio_admin.EventoNoEncontrado:
        raise HTTPException(404, "evento no encontrado")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# --- Moderación del foro --------------------------------------------------

@router.get(
    "/foro/temas",
    response_model=PaginaTemas,
    summary="Listar todos los temas, incluidos los ocultos",
)
def listar_temas(
    estado: str | None = Query(None, description="abierto, cerrado u oculto"),
    limite: int = Query(50, ge=1, le=100),
    desplazamiento: int = Query(0, ge=0),
    sesion: Session = Depends(get_db),
) -> PaginaTemas:
    total, filas = repo_admin.listar_temas(
        sesion, estado=estado, limite=limite, desplazamiento=desplazamiento
    )
    return PaginaTemas(
        total=total,
        limite=limite,
        desplazamiento=desplazamiento,
        elementos=[_tema_publico(t, n, c) for t, n, c in filas],
    )


@router.patch(
    "/foro/temas/{id_tema}",
    response_model=TemaPublico,
    summary="Abrir, cerrar u ocultar un tema",
)
def cambiar_estado_tema(
    id_tema: uuid.UUID,
    datos: EstadoTemaEntrada,
    sesion: Session = Depends(get_db),
) -> TemaPublico:
    try:
        fila = servicio_admin.cambiar_estado_tema(sesion, id_tema, datos.estado)
    except servicio_admin.TemaNoEncontrado:
        raise HTTPException(404, "tema no encontrado")
    return _tema_publico(*fila)


# --- Desafíos mensuales ---------------------------------------------------

@router.get(
    "/desafios",
    response_model=PaginaDesafios,
    summary="Historial de desafíos",
)
def listar_desafios(sesion: Session = Depends(get_db)) -> PaginaDesafios:
    filas = servicio_comunidad.listar_desafios(sesion)
    return PaginaDesafios(
        total=len(filas), elementos=[_desafio_publico(d, n) for d, n in filas]
    )


@router.post(
    "/desafios",
    response_model=DesafioPublico,
    status_code=status.HTTP_201_CREATED,
    summary="Crear un desafío mensual",
)
def crear_desafio(
    datos: DesafioEntrada, sesion: Session = Depends(get_db)
) -> DesafioPublico:
    try:
        fila = servicio_comunidad.crear_desafio(sesion, datos)
    except servicio_comunidad.MesDuplicado as error:
        raise HTTPException(409, f"ya existe un desafío para {error.mes}")
    return _desafio_publico(*fila)


@router.post(
    "/desafios/{id_desafio}/ganador",
    response_model=DesafioPublico,
    summary="Elegir el ganador de un desafío",
)
def elegir_ganador(
    id_desafio: uuid.UUID,
    datos: GanadorEntrada,
    sesion: Session = Depends(get_db),
) -> DesafioPublico:
    try:
        fila = servicio_comunidad.elegir_ganador(sesion, id_desafio, datos.id_usuario)
    except servicio_comunidad.DesafioNoEncontrado:
        raise HTTPException(404, "desafío no encontrado")
    except servicio_comunidad.UsuarioNoEncontrado:
        raise HTTPException(404, "usuario no encontrado")
    return _desafio_publico(*fila)


# --- Comunidad: tiendas y grupos ------------------------------------------

@router.post(
    "/tiendas",
    response_model=TiendaPublica,
    status_code=status.HTTP_201_CREATED,
    summary="Dar de alta una tienda de materiales",
)
def crear_tienda(
    datos: TiendaEntrada, sesion: Session = Depends(get_db)
) -> TiendaPublica:
    try:
        tienda = servicio_admin.crear_tienda(sesion, datos)
    except servicio_admin.NombreDuplicado as error:
        raise HTTPException(409, str(error))
    return TiendaPublica.model_validate(tienda)


@router.post(
    "/grupos",
    response_model=GrupoPublico,
    status_code=status.HTTP_201_CREATED,
    summary="Dar de alta un grupo de la comunidad",
)
def crear_grupo(
    datos: GrupoEntrada, sesion: Session = Depends(get_db)
) -> GrupoPublico:
    try:
        grupo = servicio_admin.crear_grupo(sesion, datos)
    except servicio_admin.NombreDuplicado as error:
        raise HTTPException(409, str(error))
    return GrupoPublico.model_validate(grupo)
