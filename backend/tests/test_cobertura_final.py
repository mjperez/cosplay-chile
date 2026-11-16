"""Cobertura restante: arranque del seed, cola editorial, moderación, avisos y búsqueda."""
import asyncio
import uuid
from datetime import date
from types import SimpleNamespace

from sqlalchemy import func, select

from app.models import CategoriaContenido, Contenido, DesafioMensual, Evento, Notificacion, Tema, Usuario
from app.models.enums import EstadoPublicacion
from app.seed.base import seed_base
from app.seed.comunidad import seed_comunidad
from app.seed.contenidos import seed_contenidos
from app.seed.imagenes import generar_todas
from tests.conftest import TEST_URL, crear_usuario, token_de

FOTO = {"imagen_url": "/media/subidas/prueba.png", "imagen_alt": "Cosplayer con armadura dorada en la playa",
        "credito_fotografo": "Ignacia Pérez", "credito_cosplayer": "Camila Rojas"}


async def _sembrar(db, tmp_path):
    ctx = {"imagenes": generar_todas(tmp_path)}
    await seed_base(db, ctx)
    await seed_contenidos(db, ctx)
    await seed_comunidad(db, ctx)
    await db.commit()
    return ctx


async def test_entrypoint_semilla_carga_todo_desde_cero(db, tmp_path, monkeypatch):
    """El comando `python -m app.seed` también queda cubierto."""
    from app.db.session_manager import DatabaseSessionManager
    from app.seed.__main__ import main as sembrar

    # El entrypoint cierra el Singleton al terminar; en pruebas debe seguir
    # disponible para las fixtures compartidas.
    async def _no_cerrar(self):
        return None

    monkeypatch.setattr(DatabaseSessionManager, "close", _no_cerrar)
    monkeypatch.setattr("app.seed.__main__.get_settings",
                        lambda: SimpleNamespace(database_url=TEST_URL, media_path=tmp_path))
    await sembrar(False)
    assert await db.scalar(select(func.count()).select_from(Usuario)) >= 12
    # Segunda llamada: no duplica datos
    await sembrar(False)
    assert await db.scalar(select(func.count()).select_from(Usuario)) >= 12


async def test_publicar_tutorial_y_cola_editorial(client, db, tmp_path, auth_usuario, admin):
    await _sembrar(db, tmp_path)
    categorias = (await client.get("/api/categorias")).json()
    categoria = next(c for c in categorias if c["slug"] == "confeccion")
    r = await client.post("/api/contenidos", headers=auth_usuario, json={
        "tipo": "GUIA", "titulo": "Guía de prueba ES3", "descripcion": "Aprende a hacer una armadura",
        "nivel": "PRINCIPIANTE", "categoria_id": categoria["id"],
        "pasos": ["Medir", "Cortar", "Pintar"], "materiales": ["Goma EVA", "Pintura"]})
    assert r.status_code == 201, r.text
    contenido = r.json()["contenido"]
    assert contenido["estado"] == "PENDIENTE" and contenido["pasos"] == ["Medir", "Cortar", "Pintar"]
    assert any(c["id"] == contenido["id"] for c in (await client.get("/api/contenidos/mios", headers=auth_usuario)).json())
    assert (await client.get(f"/api/contenidos/{contenido['id']}", headers=auth_usuario)).json()["es_favorito"] is False
    descarga = await client.get(f"/api/contenidos/{contenido['id']}/descargar", headers=auth_usuario)
    assert descarga.status_code == 200 and "attachment" in descarga.headers["content-disposition"]
    assert (await client.get(f"/api/contenidos/{uuid.uuid4()}")).status_code == 404

    cabeceras = await token_de(client, admin.email)
    cola = (await client.get("/api/moderacion/contenidos", headers=cabeceras)).json()
    assert any(c["id"] == contenido["id"] for c in cola)
    assert (await client.post(f"/api/moderacion/contenidos/{contenido['id']}/publicar",
                              headers=cabeceras)).status_code == 200
    assert any(c["id"] == contenido["id"] for c in (await client.get("/api/contenidos")).json()["items"])


async def test_moderacion_de_cuentas_desafios_y_auditoria(client, db, admin, auth_usuario, tmp_path):
    await _sembrar(db, tmp_path)
    otra = await crear_usuario(db, "sancionar@test.cl", nombre="Persona a sancionar")
    cabeceras = await token_de(client, admin.email)
    assert (await client.get("/api/moderacion/usuarios?q=sancionar", headers=cabeceras)).json()
    assert (await client.get("/api/moderacion/resumen", headers=cabeceras)).json()["contenidos_pendientes"] >= 0
    r = await client.post(f"/api/moderacion/usuarios/{otra.id}/suspender", headers=cabeceras,
                          json={"motivo": "Incumplimiento reiterado de las normas"})
    assert r.status_code == 200 and r.json()["estado"] == "SUSPENDIDO"
    assert (await client.get("/api/moderacion/usuarios?estado=SUSPENDIDO", headers=cabeceras)).json()
    assert (await client.post(f"/api/moderacion/usuarios/{otra.id}/reactivar",
                              headers=cabeceras)).status_code == 200
    assert (await client.post(f"/api/moderacion/usuarios/{uuid.uuid4()}/suspender", headers=cabeceras,
                              json={"motivo": "Motivo válido de prueba"})).status_code == 404

    mes = date.today().month % 12 + 1
    anio = date.today().year + (1 if mes == 1 else 0)
    r = await client.post("/api/moderacion/desafios", headers=cabeceras, json={
        "titulo": "Desafío de prueba ES3", "descripcion": "Comparte tu mejor propuesta",
        "mes": mes, "anio": anio})
    assert r.status_code == 201 and r.json()["abierto"] is True
    desafio_id = r.json()["id"]
    assert (await client.post("/api/moderacion/desafios", headers=cabeceras, json={
        "titulo": "Duplicado", "descripcion": "No debería crearse dos veces",
        "mes": mes, "anio": anio})).status_code == 409
    assert (await client.get("/api/desafios")).json()
    p = await client.post(f"/api/desafios/{desafio_id}/participar", headers=auth_usuario,
                          json={"titulo": "Mi propuesta", **FOTO})
    assert p.status_code == 201
    ganador = await client.post(f"/api/moderacion/desafios/{desafio_id}/ganador", headers=cabeceras,
                                json={"participacion_id": p.json()["id"]})
    assert ganador.status_code == 200 and ganador.json()["ganador"] is not None
    assert (await client.get("/api/moderacion/auditoria", headers=cabeceras)).json()
    assert (await client.get("/api/moderacion/auditoria")).status_code == 401


async def test_avisos_internos_se_marcan_como_leidos(client, db, tmp_path, auth_usuario, admin):
    await _sembrar(db, tmp_path)
    foros = (await client.get("/api/foros")).json()
    assert (await client.get("/api/temas/recientes")).json()
    tema = await client.post(f"/api/foros/{foros[0]['slug']}/temas", headers=auth_usuario, json={
        "titulo": "Mi tema sobre armaduras", "contenido": "Les cuento cómo hice mi primera armadura"})
    assert tema.status_code == 201
    otro = await crear_usuario(db, "respuesta@test.cl", nombre="Otra persona")
    r = await client.post(f"/api/temas/{tema.json()['id']}/respuestas", headers=await token_de(client, otro.email),
                          json={"contenido": "Gracias por compartir tu experiencia"})
    assert r.status_code == 201
    bandeja = (await client.get("/api/notificaciones", headers=auth_usuario)).json()
    assert bandeja["no_leidas"] >= 1 and bandeja["items"]
    notificacion = bandeja["items"][0]
    assert (await client.post(f"/api/notificaciones/{notificacion['id']}/leer",
                              headers=auth_usuario)).status_code == 200
    assert (await client.post("/api/notificaciones/leer-todas", headers=auth_usuario)).status_code == 200
    assert (await client.get("/api/notificaciones", headers=auth_usuario)).json()["no_leidas"] == 0
    assert (await client.get("/api/notificaciones")).status_code == 401
    assert (await client.get(f"/api/temas/{uuid.uuid4()}")).status_code == 404


async def test_busqueda_global_y_filtros_de_directorio(client, db, tmp_path):
    await _sembrar(db, tmp_path)
    r = await client.get("/api/busqueda?q=EVA&limite=5")
    assert r.status_code == 200 and r.json()["q"] == "EVA"
    assert (await client.get("/api/busqueda/sugerencias?q=cosplay")).status_code == 200
    assert (await client.get("/api/busqueda?q=EVA&tipos=CONTENIDO,EVENTO&region=RM&nivel=PRINCIPIANTE")).status_code == 200
    assert (await client.get("/api/busqueda?q=x")).status_code == 422

    assert (await client.get("/api/directorio?tipo=COMUNIDAD&pagina=1&por_pagina=2")).json()["paginas"] >= 1
    assert (await client.get("/api/directorio?alcance=NACIONAL&q=telas")).status_code == 200
    puntos = (await client.get("/api/directorio/mapa?tipo=TIENDA")).json()
    assert all(p["lat"] and p["lng"] for p in puntos)
    assert (await client.get("/api/directorio/mapa?region=RM")).status_code == 200
