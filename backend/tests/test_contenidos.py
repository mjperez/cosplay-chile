"""Flujo «Publicar tutorial» (UC6, Tabla 6, Figs. 13 y 15) y módulo de contenidos."""
from sqlalchemy import select

from app.models import Contenido, Notificacion, RegistroAuditoria
from app.models.enums import EstadoPublicacion
from app.services.correo import BANDEJA_SIMULADA
from tests.conftest import crear_categoria, uid

GUIA = {
    "tipo": "GUIA",
    "titulo": "Cómo hacer una corona de goma EVA",
    "descripcion": "Paso a paso para tu primera corona, con materiales que encuentras en Chile.",
    "cuerpo": "La goma EVA es barata y fácil de trabajar.\n\nUsa siempre mascarilla al calentarla.",
    "nivel": "PRINCIPIANTE",
    "pasos": ["Dibuja el patrón", "Corta la EVA", "Sella con cola fría", "Pinta"],
    "materiales": ["Goma EVA 5 mm", "Cúter", "Pistola de calor"],
    "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
}


async def _publicar(client, headers, categoria, **extra):
    return await client.post("/api/contenidos", headers=headers, json={**GUIA, "categoria_id": str(categoria.id), **extra})


async def test_flujo_completo_publicar_tutorial(client, db, usuario, admin, auth_usuario, auth_admin):
    categoria = await crear_categoria(db)
    BANDEJA_SIMULADA.clear()

    # Pasos 1-5: envío, validación de categoría, Factory y estado PENDIENTE
    r = await _publicar(client, auth_usuario, categoria)
    assert r.status_code == 201, r.text
    cuerpo = r.json()
    assert "revisión" in cuerpo["mensaje"]  # paso 7: confirmación
    contenido = cuerpo["contenido"]
    assert contenido["estado"] == "PENDIENTE"
    assert contenido["video_embed"] == "https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ"

    # Paso 6: Observer -> notificación «En revisión» al usuario y aviso a moderación
    notifs = {n.usuario_id: n for n in (await db.execute(select(Notificacion))).scalars()}
    assert "en revisión" in notifs[usuario.id].mensaje
    assert "pendiente de revisión" in notifs[admin.id].mensaje
    assert any("Nuevo tutorial" in c["asunto"] for c in BANDEJA_SIMULADA)  # correo a moderación
    assert "NUEVO_TUTORIAL" in (await db.execute(select(RegistroAuditoria.evento))).scalars().all()

    # Mientras está pendiente no es público
    assert (await client.get(f"/api/contenidos/{contenido['id']}")).status_code == 404
    assert (await client.get("/api/contenidos")).json()["total"] == 0
    # pero su autor sí lo ve en «Mis envíos»
    mios = (await client.get("/api/contenidos/mios", headers=auth_usuario)).json()
    assert mios[0]["estado"] == "PENDIENTE"

    # Cola de revisión del moderador
    cola = (await client.get("/api/moderacion/contenidos", headers=auth_admin)).json()
    assert [c["id"] for c in cola] == [contenido["id"]]

    r = await client.post(f"/api/moderacion/contenidos/{contenido['id']}/publicar", headers=auth_admin)
    assert r.status_code == 200 and r.json()["estado"] == "PUBLICADO"
    publico = await client.get(f"/api/contenidos/{contenido['id']}")
    assert publico.status_code == 200 and publico.json()["pasos"][0] == "Dibuja el patrón"
    mensajes = (await db.execute(select(Notificacion.mensaje).where(Notificacion.usuario_id == usuario.id))).scalars().all()
    assert any("fue publicado" in m for m in mensajes)

    # No se puede revisar dos veces
    r = await client.post(f"/api/moderacion/contenidos/{contenido['id']}/publicar", headers=auth_admin)
    assert r.status_code == 409


async def test_categoria_inexistente_muestra_categoria_no_encontrada(client, db, auth_usuario):
    """Flujo alterno 4a."""
    r = await client.post("/api/contenidos", headers=auth_usuario, json={**GUIA, "categoria_id": uid()})
    assert r.status_code == 422
    assert r.json()["detail"] == "Categoría no encontrada"
    assert (await db.execute(select(Contenido))).first() is None


async def test_publicar_requiere_sesion(client, db):
    categoria = await crear_categoria(db)
    assert (await _publicar(client, {}, categoria)).status_code == 401


async def test_validaciones_propias_del_tipo_llegan_como_422(client, db, auth_usuario):
    categoria = await crear_categoria(db)
    r = await _publicar(client, auth_usuario, categoria, pasos=[])
    assert r.status_code == 422 and "paso" in r.json()["detail"]
    r = await _publicar(client, auth_usuario, categoria, video_url="https://videos.example/x")
    assert r.status_code == 422


async def test_rechazo_con_motivo_notifica_al_autor(client, db, usuario, auth_usuario, auth_admin):
    categoria = await crear_categoria(db)
    cid = (await _publicar(client, auth_usuario, categoria)).json()["contenido"]["id"]
    r = await client.post(f"/api/moderacion/contenidos/{cid}/rechazar", headers=auth_admin,
                          json={"motivo": "Faltan fotos de los pasos"})
    assert r.json()["estado"] == "RECHAZADO"
    mensajes = (await db.execute(select(Notificacion.mensaje).where(Notificacion.usuario_id == usuario.id))).scalars().all()
    assert any("Faltan fotos" in m for m in mensajes)


async def test_solo_moderacion_revisa(client, db, auth_usuario):
    categoria = await crear_categoria(db)
    cid = (await _publicar(client, auth_usuario, categoria)).json()["contenido"]["id"]
    assert (await client.get("/api/moderacion/contenidos", headers=auth_usuario)).status_code == 403
    r = await client.post(f"/api/moderacion/contenidos/{cid}/publicar", headers=auth_usuario)
    assert r.status_code == 403


async def _contenido_publicado(db, usuario, categoria, titulo, nivel):
    from app.models import GuiaTutorial
    c = GuiaTutorial(titulo=titulo, descripcion="desc", nivel=nivel, categoria_id=categoria.id, autor_id=usuario.id,
                     estado=EstadoPublicacion.PUBLICADO, pasos=["a"], materiales=["b"])
    db.add(c)
    await db.commit()
    return c


async def test_filtros_por_nivel_categoria_y_texto(client, db, usuario):
    confeccion = await crear_categoria(db)
    maquillaje = await crear_categoria(db, "Maquillaje", "maquillaje")
    await _contenido_publicado(db, usuario, confeccion, "Patrón de capa", "PRINCIPIANTE")
    await _contenido_publicado(db, usuario, confeccion, "Corsé avanzado", "AVANZADO")
    await _contenido_publicado(db, usuario, maquillaje, "Maquillaje FX básico", "PRINCIPIANTE")

    def titulos(r):
        return sorted(c["titulo"] for c in r.json()["items"])

    assert titulos(await client.get("/api/contenidos?nivel=PRINCIPIANTE")) == ["Maquillaje FX básico", "Patrón de capa"]
    assert titulos(await client.get("/api/contenidos?categoria=confeccion")) == ["Corsé avanzado", "Patrón de capa"]
    assert titulos(await client.get("/api/contenidos?categoria=confeccion&nivel=AVANZADO")) == ["Corsé avanzado"]
    # búsqueda sin tildes ni mayúsculas
    assert titulos(await client.get("/api/contenidos?q=CORSE")) == ["Corsé avanzado"]
    r = await client.get("/api/contenidos?por_pagina=2")
    assert r.json()["paginas"] == 2 and len(r.json()["items"]) == 2


async def test_descarga_solo_con_sesion_y_escapa_html(client, db, usuario, auth_usuario):
    categoria = await crear_categoria(db)
    c = await _contenido_publicado(db, usuario, categoria, "<script>alert(1)</script> Guía", "PRINCIPIANTE")
    assert (await client.get(f"/api/contenidos/{c.id}/descargar")).status_code == 401
    r = await client.get(f"/api/contenidos/{c.id}/descargar", headers=auth_usuario)
    assert r.status_code == 200
    assert "attachment" in r.headers["content-disposition"]
    assert "<script>" not in r.text and "&lt;script&gt;" in r.text


async def test_favoritos_guardar_listar_y_quitar(client, db, usuario, auth_usuario):
    categoria = await crear_categoria(db)
    c = await _contenido_publicado(db, usuario, categoria, "Peluca", "PRINCIPIANTE")
    assert (await client.post("/api/favoritos", json={"tipo": "CONTENIDO", "objeto_id": str(c.id)})).status_code == 401
    for _ in range(2):  # idempotente
        r = await client.post("/api/favoritos", headers=auth_usuario, json={"tipo": "CONTENIDO", "objeto_id": str(c.id)})
        assert r.status_code == 201
    lista = (await client.get("/api/favoritos", headers=auth_usuario)).json()
    assert len(lista) == 1 and lista[0]["enlace"] == f"/guias/{c.id}"
    assert (await client.get(f"/api/contenidos/{c.id}", headers=auth_usuario)).json()["es_favorito"] is True
    await client.delete(f"/api/favoritos/CONTENIDO/{c.id}", headers=auth_usuario)
    assert (await client.get("/api/favoritos/ids", headers=auth_usuario)).json()["CONTENIDO"] == []


async def test_no_se_puede_guardar_contenido_pendiente(client, db, auth_usuario):
    categoria = await crear_categoria(db)
    cid = (await _publicar(client, auth_usuario, categoria)).json()["contenido"]["id"]
    r = await client.post("/api/favoritos", headers=auth_usuario, json={"tipo": "CONTENIDO", "objeto_id": cid})
    assert r.status_code == 404


async def test_bandeja_de_notificaciones(client, db, usuario, auth_usuario, admin):
    categoria = await crear_categoria(db)
    await _publicar(client, auth_usuario, categoria)
    bandeja = (await client.get("/api/notificaciones", headers=auth_usuario)).json()
    assert bandeja["no_leidas"] == 1
    await client.post("/api/notificaciones/leer-todas", headers=auth_usuario)
    assert (await client.get("/api/notificaciones", headers=auth_usuario)).json()["no_leidas"] == 0
