"""Búsqueda global (RF-31) y portada (RF-01)."""
from datetime import date, timedelta

import pytest

from app.models import (
    ComunidadGrupo,
    DesafioMensual,
    Evento,
    Foro,
    GuiaTutorial,
    ProveedorServicio,
    Respuesta,
    Tema,
    Tienda,
)
from tests.conftest import crear_categoria


@pytest.fixture
async def datos(db, usuario):
    cat = await crear_categoria(db, "Props y armaduras", "props")
    foro = Foro(titulo="Props", slug="props", categoria="Props")
    hoy = date.today()
    db.add_all([
        foro,
        GuiaTutorial(titulo="Tu primera armadura de goma EVA", descripcion="Paso a paso", nivel="PRINCIPIANTE",
                     categoria_id=cat.id, autor_id=usuario.id, estado="PUBLICADO", pasos=["a"], materiales=["b"]),
        GuiaTutorial(titulo="EVA avanzada pendiente", descripcion="No visible", nivel="AVANZADO",
                     categoria_id=cat.id, autor_id=usuario.id, estado="PENDIENTE", pasos=["a"], materiales=["b"]),
        Tienda(nombre="Insumos Centro", region="RM", comuna="Santiago", tipos_producto=["TERMOPLASTICOS"], alcance="NACIONAL"),
        Tienda(nombre="Telas Sur", region="BI", comuna="Concepción", tipos_producto=["TELAS"], alcance="NACIONAL"),
        ProveedorServicio(nombre="Maquillaje Andes", region="RM", comuna="Providencia", especialidades=["MAQUILLAJE"]),
        ProveedorServicio(nombre="Sastrería Penquista", region="BI", comuna="Concepción", especialidades=["SASTRERIA"]),
        ComunidadGrupo(nombre="Cosplay Santiago Centro", region="RM", plataforma="Discord"),
        Evento(nombre="Meetup en Santiago", tipo="MEETUP", region="RM", lugar="Parque Forestal",
               fecha_inicio=hoy + timedelta(days=5), estado="PUBLICADO"),
        Evento(nombre="Convención Biobío", tipo="CONVENCION", region="BI", lugar="Teatro",
               fecha_inicio=hoy + timedelta(days=9), estado="PUBLICADO"),
        DesafioMensual(titulo="Reciclaje", descripcion="Materiales reciclados", mes=hoy.month, anio=hoy.year),
    ])
    await db.flush()
    tema = Tema(foro_id=foro.id, autor_id=usuario.id, titulo="La EVA se me cuartea", contenido="¿Qué hago?")
    db.add(tema)
    await db.flush()
    db.add(Respuesta(tema_id=tema.id, autor_id=usuario.id, contenido="Séllala primero"))
    await db.commit()


def _titulos(r, grupo):
    return sorted(i["titulo"] for i in r.json()["grupos"][grupo])


async def test_busqueda_eva_cruza_guias_tiendas_y_foro(client, datos):
    r = await client.get("/api/busqueda?q=EVA")
    assert r.status_code == 200
    assert _titulos(r, "guia") == ["Tu primera armadura de goma EVA"]  # la pendiente no aparece
    assert _titulos(r, "tienda") == ["Insumos Centro"]  # EVA -> termoplásticos
    assert _titulos(r, "tema") == ["La EVA se me cuartea"]
    assert r.json()["grupos"]["guia"][0]["enlace"].startswith("/guias/")


async def test_busqueda_por_ciudad_reconoce_la_region(client, datos):
    r = await client.get("/api/busqueda?q=Santiago")
    assert _titulos(r, "proveedor") == ["Maquillaje Andes"]  # está en Providencia, RM
    assert _titulos(r, "evento") == ["Meetup en Santiago"]
    assert _titulos(r, "comunidad") == ["Cosplay Santiago Centro"]
    r = await client.get("/api/busqueda?q=concepcion")  # sin tilde
    assert _titulos(r, "proveedor") == ["Sastrería Penquista"]
    assert _titulos(r, "evento") == ["Convención Biobío"]


async def test_busqueda_por_especialidad_y_varias_palabras(client, datos):
    assert _titulos(await client.get("/api/busqueda?q=maquillaje"), "proveedor") == ["Maquillaje Andes"]
    r = await client.get("/api/busqueda?q=telas en Concepción")
    assert _titulos(r, "tienda") == ["Telas Sur"]
    assert _titulos(r, "proveedor") == []


async def test_filtros_de_la_busqueda(client, datos):
    r = await client.get("/api/busqueda?q=santiago&tipos=evento")
    assert set(k for k, v in r.json()["grupos"].items() if v) == {"evento"}
    r = await client.get("/api/busqueda?q=concepcion&region=RM")
    assert r.json()["grupos"]["proveedor"] == [] and r.json()["grupos"]["evento"] == []
    r = await client.get("/api/busqueda?q=EVA&tipos=guia&nivel=AVANZADO")
    assert r.json()["total"] == 0
    assert (await client.get("/api/busqueda?q=a")).status_code == 422


async def test_autocompletado_mezcla_tipos_y_limita(client, datos):
    r = await client.get("/api/busqueda/sugerencias?q=eva")
    sugerencias = r.json()
    assert 0 < len(sugerencias) <= 8
    assert {"guia", "tienda", "tema"} <= {s["tipo"] for s in sugerencias}


async def test_portada_con_novedades_y_estadisticas(client, datos):
    r = await client.get("/api/inicio")
    assert r.status_code == 200
    p = r.json()
    est = p["estadisticas"]
    assert est["guias"] == 1 and est["tiendas"] == 2 and est["proveedores"] == 2 and est["comunidades"] == 1
    assert est["eventos_proximos"] == 2 and est["regiones_con_presencia"] == 2
    assert [g["titulo"] for g in p["ultimas_guias"]] == ["Tu primera armadura de goma EVA"]
    assert [e["nombre"] for e in p["proximos_eventos"]] == ["Meetup en Santiago", "Convención Biobío"]
    assert p["temas_destacados"][0]["respuestas"] == 1
    assert p["desafio_actual"]["titulo"] == "Reciclaje"
