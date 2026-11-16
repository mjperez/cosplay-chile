"""Motor de búsqueda unificado (RF-31): guías, proveedores, tiendas, comunidades, hilos y eventos.

Cada palabra de la consulta debe coincidir (AND) con algún campo de texto (sin tildes ni
mayúsculas, índices trigram) o con el vocabulario del dominio: «Santiago» -> Región
Metropolitana; «EVA» -> tiendas de termoplásticos; «maquillaje» -> especialidad maquillaje.
"""
from datetime import date

from sqlalchemy import and_, false, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.comunidad import Tema
from app.models.contenido import CategoriaContenido, Contenido
from app.models.directorio import DirectorioItem
from app.models.enums import REGIONES, EstadoPublicacion, Nivel, Region, TipoDirectorio, normalizar, regiones_que_coinciden
from app.models.etiquetas import ETIQUETAS
from app.models.evento import Evento
from app.services.busqueda_util import coincide

TIPOS = ("guia", "proveedor", "tienda", "comunidad", "tema", "evento")

# Sinónimos frecuentes de la comunidad -> palabra que aparece en las etiquetas
SINONIMOS = {"goma": "eva", "foam": "eva", "worbla": "termoplasticos", "fotos": "fotografia", "fotografo": "fotografia",
             "sastre": "sastreria", "peluca": "pelucas", "lentillas": "lentes"}

PALABRAS_VACIAS = {"de", "la", "el", "en", "y", "a", "o", "los", "las", "del", "al", "un", "una", "para", "con", "por", "mi"}


def palabras(q: str) -> list[str]:
    todas = [p for p in (normalizar(x) for x in q.split()) if len(p) >= 2]
    utiles = [p for p in todas if p not in PALABRAS_VACIAS]
    return (utiles or todas)[:6]


def _vocabulario(palabra: str, grupo: str) -> list[str]:
    p = SINONIMOS.get(palabra, palabra)
    return [codigo for codigo, texto in ETIQUETAS[grupo].items() if p in normalizar(texto) or p in codigo.lower()]


def _cond_directorio(p: str):
    conds = [coincide(DirectorioItem.nombre, p), coincide(DirectorioItem.descripcion, p), coincide(DirectorioItem.comuna, p)]
    regiones = regiones_que_coinciden(p)
    if regiones:
        conds.append(DirectorioItem.region.in_(regiones))
    conds += [DirectorioItem.especialidades.contains([e]) for e in _vocabulario(p, "especialidades")]
    conds += [DirectorioItem.tipos_producto.contains([t]) for t in _vocabulario(p, "tipos_producto")]
    return or_(*conds)


def _cond_guia(p: str):
    categorias = select(CategoriaContenido.id).where(coincide(CategoriaContenido.nombre, p))
    return or_(coincide(Contenido.titulo, p), coincide(Contenido.descripcion, p), Contenido.categoria_id.in_(categorias))


def _cond_evento(p: str):
    conds = [coincide(Evento.nombre, p), coincide(Evento.lugar, p), coincide(Evento.comuna, p), coincide(Evento.descripcion, p)]
    regiones = regiones_que_coinciden(p)
    if regiones:
        conds.append(Evento.region.in_(regiones))
    tipos = _vocabulario(p, "tipos_evento")
    if tipos:
        conds.append(Evento.tipo.in_(tipos))
    return or_(*conds)


def _todas(fn, ps: list[str]):
    return and_(*(fn(p) for p in ps)) if ps else false()


def _item(tipo, id_, titulo, subtitulo, enlace) -> dict:
    return {"tipo": tipo, "id": str(id_), "titulo": titulo, "subtitulo": subtitulo, "enlace": enlace}


async def buscar(
    db: AsyncSession, q: str, *, tipos: set[str], region: Region | None, categoria: str | None,
    nivel: Nivel | None, limite: int,
) -> dict[str, list[dict]]:
    ps = palabras(q)
    r: dict[str, list[dict]] = {t: [] for t in TIPOS}
    if not ps:
        return r

    if "guia" in tipos:
        filtros = [Contenido.estado == EstadoPublicacion.PUBLICADO, _todas(_cond_guia, ps)]
        if categoria:
            filtros.append(Contenido.categoria_id.in_(select(CategoriaContenido.id).where(CategoriaContenido.slug == categoria)))
        if nivel:
            filtros.append(Contenido.nivel == nivel)
        filas = (await db.execute(select(Contenido).where(*filtros)
                                  .order_by(Contenido.publicado_at.desc().nulls_last()).limit(limite))).scalars().unique()
        r["guia"] = [_item("guia", c.id, c.titulo, f"{c.categoria.nombre} · {ETIQUETAS['niveles'][c.nivel.value]}",
                           f"/guias/{c.id}") for c in filas]

    for clave, tipo_dir in (("proveedor", TipoDirectorio.PROVEEDOR), ("tienda", TipoDirectorio.TIENDA),
                            ("comunidad", TipoDirectorio.COMUNIDAD)):
        if clave not in tipos:
            continue
        filtros = [DirectorioItem.activo.is_(True), DirectorioItem.tipo == tipo_dir, _todas(_cond_directorio, ps)]
        if region:
            filtros.append(DirectorioItem.region == region)
        filas = (await db.execute(select(DirectorioItem).where(*filtros).order_by(DirectorioItem.nombre).limit(limite))).scalars().unique()
        r[clave] = [_item(clave, i.id, i.nombre,
                          ", ".join(x for x in (i.comuna, REGIONES[Region(i.region)] if i.region else "Internacional") if x),
                          f"/directorio/{i.id}") for i in filas]

    if "tema" in tipos:
        filtros = [Tema.oculto.is_(False), and_(*(or_(coincide(Tema.titulo, p), coincide(Tema.contenido, p)) for p in ps))]
        filas = (await db.execute(select(Tema).where(*filtros).order_by(Tema.created_at.desc()).limit(limite))).scalars().unique()
        r["tema"] = [_item("tema", t.id, t.titulo, f"Foro {t.foro.titulo}", f"/comunidad/temas/{t.id}") for t in filas]

    if "evento" in tipos:
        filtros = [Evento.estado == EstadoPublicacion.PUBLICADO, Evento.fecha_inicio >= date.today(), _todas(_cond_evento, ps)]
        if region:
            filtros.append(Evento.region == region)
        filas = (await db.execute(select(Evento).where(*filtros).order_by(Evento.fecha_inicio).limit(limite))).scalars().unique()
        r["evento"] = [_item("evento", e.id, e.nombre, f"{e.fecha_inicio:%d-%m-%Y} · {e.comuna or e.lugar}",
                             f"/calendario/{e.id}") for e in filas]
    return r
