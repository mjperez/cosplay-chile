"""Módulo Contenidos Educativos: UC6 «Gestionar Tutoriales» (Tabla 6, Figs. 13 y 15)."""
import html
import uuid
from datetime import datetime, timezone

from fastapi import BackgroundTasks, HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.contenido import CategoriaContenido, Contenido, ContenidoInvalido
from app.models.enums import EstadoPublicacion, Nivel, TipoContenido
from app.models.usuario import Usuario
from app.patterns.contenido_factory import CategoriaNoEncontrada, ContenidoFactory, TipoContenidoDesconocido
from app.patterns.observer import Eventos, GestorEventos
from app.schemas.contenido import ContenidoCrear
from app.services.busqueda_util import coincide


async def publicar_tutorial(
    db: AsyncSession, gestor: GestorEventos, tareas: BackgroundTasks, autor: Usuario, datos: ContenidoCrear
) -> Contenido:
    """Pasos 3-7 del flujo normal de UC6."""
    payload = datos.model_dump(mode="json")
    payload["autor_id"] = autor.id
    try:
        contenido = await ContenidoFactory(db).crear_contenido(datos.tipo, payload)  # pasos 4 y 5
    except CategoriaNoEncontrada as e:  # flujo alterno 4a
        raise HTTPException(422, e.mensaje)
    except (ContenidoInvalido, TipoContenidoDesconocido) as e:
        raise HTTPException(422, str(e))
    contenido.autor = autor
    await db.commit()
    # Paso 6: el Observer avisa al usuario y a moderación, en segundo plano
    gestor.notificar_en_segundo_plano(
        tareas, Eventos.NUEVO_TUTORIAL,
        {"contenido_id": contenido.id, "titulo": contenido.titulo, "autor_id": autor.id, "tipo": contenido.tipo},
        actor_id=autor.id,
    )
    return contenido


async def listar_publicados(
    db: AsyncSession, *, nivel: Nivel | None, categoria: str | None, tipo: TipoContenido | None,
    q: str | None, pagina: int, por_pagina: int,
) -> tuple[list[Contenido], int]:
    filtros = [Contenido.estado == EstadoPublicacion.PUBLICADO]
    if nivel:
        filtros.append(Contenido.nivel == nivel)
    if tipo:
        filtros.append(Contenido.tipo == tipo)
    if categoria:
        filtros.append(Contenido.categoria_id.in_(select(CategoriaContenido.id).where(CategoriaContenido.slug == categoria)))
    if q:
        filtros.append(or_(coincide(Contenido.titulo, q), coincide(Contenido.descripcion, q)))
    total = await db.scalar(select(func.count()).select_from(Contenido).where(*filtros))
    filas = (await db.execute(
        select(Contenido).where(*filtros)
        .order_by(Contenido.publicado_at.desc().nulls_last(), Contenido.created_at.desc())
        .offset((pagina - 1) * por_pagina).limit(por_pagina)
    )).scalars().unique().all()
    return list(filas), total or 0


async def obtener_visible(db: AsyncSession, contenido_id: uuid.UUID, usuario: Usuario | None) -> Contenido:
    """Publicado: visible para todos. Pendiente/rechazado: solo autor y moderación."""
    c = await db.get(Contenido, contenido_id)
    if c is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Contenido no encontrado")
    if c.estado != EstadoPublicacion.PUBLICADO:
        if usuario is None or (usuario.id != c.autor_id and not usuario.es_admin):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Contenido no encontrado")
    return c


async def moderar(
    db: AsyncSession, gestor: GestorEventos, tareas: BackgroundTasks, admin: Usuario,
    contenido_id: uuid.UUID, aprobar: bool, motivo: str | None = None,
) -> Contenido:
    c = await db.get(Contenido, contenido_id)
    if c is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Contenido no encontrado")
    if c.estado != EstadoPublicacion.PENDIENTE:
        raise HTTPException(status.HTTP_409_CONFLICT, "Este contenido ya fue revisado")
    if aprobar:
        c.estado = EstadoPublicacion.PUBLICADO
        c.publicado_at = datetime.now(timezone.utc)
        c.motivo_rechazo = None
        evento = Eventos.CONTENIDO_PUBLICADO
    else:
        c.estado = EstadoPublicacion.RECHAZADO
        c.motivo_rechazo = motivo
        evento = Eventos.CONTENIDO_RECHAZADO
    await db.commit()
    gestor.notificar_en_segundo_plano(
        tareas, evento,
        {"contenido_id": c.id, "titulo": c.titulo, "autor_id": c.autor_id, "motivo": motivo},
        actor_id=admin.id,
    )
    return c


def html_descarga(c: Contenido) -> str:
    """RF-06: versión descargable, autocontenida e imprimible a PDF."""
    e = html.escape

    def lista(items, ordenada=False):
        if not items:
            return ""
        tag = "ol" if ordenada else "ul"
        return f"<{tag}>" + "".join(f"<li>{e(i)}</li>" for i in items) + f"</{tag}>"

    bloques = []
    if c.materiales:
        bloques.append(f"<h2>Materiales</h2>{lista(c.materiales)}")
    if c.pasos:
        bloques.append(f"<h2>Paso a paso</h2>{lista(c.pasos, ordenada=True)}")
    if c.preguntas:
        qa = "".join(
            f"<h3>{e(p)}</h3><p>{e(r)}</p>" for p, r in zip(c.preguntas, c.respuestas or [])
        )
        bloques.append(f"<h2>Entrevista a {e(c.entrevistado or '')}</h2>{qa}")
    if c.enlaces:
        bloques.append("<h2>Referencias</h2><ul>" + "".join(
            f'<li><a href="{e(u)}">{e(u)}</a></li>' for u in c.enlaces) + "</ul>")
    cuerpo = "".join(f"<p>{e(p.strip())}</p>" for p in (c.cuerpo or "").split("\n\n") if p.strip())
    video = f'<p>Video complementario: <a href="{e(c.video_url)}">{e(c.video_url)}</a></p>' if c.video_url else ""
    fecha = (c.publicado_at or c.created_at).strftime("%d-%m-%Y")
    return f"""<!doctype html>
<html lang="es-CL"><head><meta charset="utf-8"><title>{e(c.titulo)} · Cosplay Chile</title>
<style>body{{font-family:system-ui,sans-serif;max-width:46rem;margin:2rem auto;padding:0 1rem;line-height:1.6;color:#111}}
h1{{color:#5b21b6}}.meta{{color:#444}}a{{color:#5b21b6}}@media print{{a{{color:#000}}}}</style></head>
<body><p class="meta">Cosplay Chile · {e(c.categoria.nombre)} · Nivel {e(c.nivel.value.lower())}</p>
<h1>{e(c.titulo)}</h1><p class="meta">Por {e(c.autor.nombre)} · {fecha}</p>
<p><strong>{e(c.descripcion)}</strong></p>{cuerpo}{''.join(bloques)}{video}
<hr><p class="meta">Descargado desde Cosplay Chile. Para imprimir o guardar como PDF usa Ctrl+P.</p></body></html>"""
