"""Foro de la comunidad y desafíos mensuales."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_usuario_actual, requiere_admin
from app.core.database import get_db
from app.models.comunidad import DesafioMensual, ForoRespuesta, ForoTema
from app.models.usuario import Usuario
from app.repositories import comunidad as repo
from app.schemas.comunidad import (
    CATEGORIAS_FORO,
    DesafioEntrada,
    DesafioPublico,
    GanadorEntrada,
    PaginaDesafios,
    PaginaTemas,
    RespuestaEntrada,
    RespuestaPublica,
    TemaDetalle,
    TemaEntrada,
    TemaPublico,
)
from app.services import comunidad as servicio

router_foro = APIRouter(prefix="/foro", tags=["foro"])
router_desafios = APIRouter(prefix="/desafios", tags=["desafíos"])


def _tema(tema: ForoTema, nombre: str, total: int) -> TemaPublico:
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


def _respuesta(respuesta: ForoRespuesta, nombre: str) -> RespuestaPublica:
    return RespuestaPublica(
        id_respuesta=respuesta.id_respuesta,
        id_tema=respuesta.id_tema,
        contenido=respuesta.contenido,
        nombre_autor=nombre,
        creado_en=respuesta.creado_en,
    )


def _desafio(desafio: DesafioMensual, nombre_ganador: str | None) -> DesafioPublico:
    return DesafioPublico(
        id_desafio=desafio.id_desafio,
        titulo=desafio.titulo,
        mes=desafio.mes,
        id_ganador=desafio.id_ganador,
        nombre_ganador=nombre_ganador,
        creado_en=desafio.creado_en,
    )


# --- Foro ----------------------------------------------------------------

@router_foro.get("/temas", response_model=PaginaTemas, summary="Listar temas del foro")
def listar_temas(
    categoria: str | None = Query(None, description=f"Una de: {', '.join(CATEGORIAS_FORO)}"),
    q: str | None = Query(None, max_length=80),
    limite: int = Query(20, ge=1, le=100),
    desplazamiento: int = Query(0, ge=0),
    sesion: Session = Depends(get_db),
) -> PaginaTemas:
    total, filas = servicio.listar_temas(
        sesion,
        categoria=categoria,
        busqueda=q,
        limite=limite,
        desplazamiento=desplazamiento,
    )
    return PaginaTemas(
        total=total,
        limite=limite,
        desplazamiento=desplazamiento,
        elementos=[_tema(t, n, c) for t, n, c in filas],
    )


@router_foro.get(
    "/temas/{id_tema}", response_model=TemaDetalle, summary="Detalle de un tema y sus respuestas"
)
def detalle_tema(id_tema: uuid.UUID, sesion: Session = Depends(get_db)) -> TemaDetalle:
    try:
        tema, nombre, total = servicio.obtener_tema(sesion, id_tema)
    except servicio.TemaNoEncontrado:
        raise HTTPException(404, "tema no encontrado")
    respuestas = servicio.listar_respuestas(sesion, id_tema)
    return TemaDetalle(
        **_tema(tema, nombre, total).model_dump(),
        respuestas=[_respuesta(r, n) for r, n in respuestas],
    )


@router_foro.post(
    "/temas",
    response_model=TemaPublico,
    status_code=status.HTTP_201_CREATED,
    summary="Abrir un tema nuevo",
)
def abrir_tema(
    datos: TemaEntrada,
    usuario: Usuario = Depends(get_usuario_actual),
    sesion: Session = Depends(get_db),
) -> TemaPublico:
    fila = servicio.crear_tema(sesion, datos, usuario)
    return _tema(*fila)


@router_foro.post(
    "/temas/{id_tema}/respuestas",
    response_model=RespuestaPublica,
    status_code=status.HTTP_201_CREATED,
    summary="Responder un tema",
)
def responder_tema(
    id_tema: uuid.UUID,
    datos: RespuestaEntrada,
    usuario: Usuario = Depends(get_usuario_actual),
    sesion: Session = Depends(get_db),
) -> RespuestaPublica:
    try:
        fila = servicio.responder(sesion, id_tema, datos, usuario)
    except servicio.TemaNoEncontrado:
        raise HTTPException(404, "tema no encontrado")
    except servicio.TemaCerrado:
        raise HTTPException(409, "el tema está cerrado y no admite respuestas")
    return _respuesta(*fila)


@router_foro.post(
    "/temas/{id_tema}/cerrar", response_model=TemaPublico, summary="Cerrar un tema"
)
def cerrar_tema(
    id_tema: uuid.UUID,
    usuario: Usuario = Depends(get_usuario_actual),
    sesion: Session = Depends(get_db),
) -> TemaPublico:
    try:
        fila = servicio.cerrar_tema(sesion, id_tema, usuario)
    except servicio.TemaNoEncontrado:
        raise HTTPException(404, "tema no encontrado")
    except servicio.SinPermisos:
        raise HTTPException(403, "solo el autor o un administrador pueden cerrar el tema")
    return _tema(*fila)


# --- Desafíos ------------------------------------------------------------

@router_desafios.get("", response_model=PaginaDesafios, summary="Historial de desafíos")
def listar_desafios(sesion: Session = Depends(get_db)) -> PaginaDesafios:
    filas = servicio.listar_desafios(sesion)
    return PaginaDesafios(
        total=len(filas),
        elementos=[_desafio(d, n) for d, n in filas],
    )


@router_desafios.get(
    "/vigente", response_model=DesafioPublico | None, summary="Desafío del mes en curso"
)
def desafio_vigente(sesion: Session = Depends(get_db)) -> DesafioPublico | None:
    fila = servicio.desafio_vigente(sesion)
    return None if fila is None else _desafio(*fila)


@router_desafios.post(
    "",
    response_model=DesafioPublico,
    status_code=status.HTTP_201_CREATED,
    summary="Crear un desafío mensual (solo administrador)",
    dependencies=[Depends(requiere_admin)],
)
def crear_desafio(datos: DesafioEntrada, sesion: Session = Depends(get_db)) -> DesafioPublico:
    try:
        fila = servicio.crear_desafio(sesion, datos)
    except servicio.MesDuplicado as error:
        raise HTTPException(409, f"ya existe un desafío para {error.mes}")
    return _desafio(*fila)


@router_desafios.post(
    "/{id_desafio}/ganador",
    response_model=DesafioPublico,
    summary="Elegir el ganador de un desafío (solo administrador)",
    dependencies=[Depends(requiere_admin)],
)
def elegir_ganador(
    id_desafio: uuid.UUID,
    datos: GanadorEntrada,
    sesion: Session = Depends(get_db),
) -> DesafioPublico:
    try:
        fila = servicio.elegir_ganador(sesion, id_desafio, datos.id_usuario)
    except servicio.DesafioNoEncontrado:
        raise HTTPException(404, "desafío no encontrado")
    except servicio.UsuarioNoEncontrado:
        raise HTTPException(404, "usuario no encontrado")
    return _desafio(*fila)
