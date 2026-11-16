"""Comunidad (RF-22, 23, 27, 29, 36) y moderación (RF-38, 40; Bloquear/Sancionar Usuario)."""
from datetime import date

from sqlalchemy import select

from app.models import Contacto, DesafioMensual, Foro, Notificacion, RegistroAuditoria, Usuario
from app.models.enums import EstadoUsuario
from app.services.correo import BANDEJA_SIMULADA
from tests.conftest import PASSWORD, crear_usuario, token_de

FOTO = {"imagen_url": "/media/subidas/foto.png", "imagen_alt": "Cosplayer con armadura dorada en la playa",
        "credito_fotografo": "Ignacia Pérez", "credito_cosplayer": "Camila Rojas"}


async def _foros(db):
    foros = [Foro(titulo="Confección y patronaje", slug="confeccion", categoria="Dudas de costura", orden=1),
             Foro(titulo="Historias de cosplayers", slug="historias", categoria="Cómo llegaste al cosplay", orden=2)]
    db.add_all(foros)
    await db.commit()
    return foros


async def test_crear_tema_responder_y_notificar_al_autor(client, db, usuario, auth_usuario):
    await _foros(db)
    foros = (await client.get("/api/foros")).json()
    assert [f["slug"] for f in foros] == ["confeccion", "historias"]

    assert (await client.post("/api/foros/confeccion/temas", json={"titulo": "Duda", "contenido": "x" * 20})).status_code == 401
    r = await client.post("/api/foros/historias/temas", headers=auth_usuario, json={
        "titulo": "Cómo llegué al cosplay", "contenido": "Todo partió en una convención en Concepción...", **FOTO})
    assert r.status_code == 201, r.text
    tema = r.json()
    assert tema["credito_fotografo"] == "Ignacia Pérez" and tema["foro"]["slug"] == "historias"

    otra = await crear_usuario(db, "otra@test.cl", nombre="Rocío")
    r = await client.post(f"/api/temas/{tema['id']}/respuestas", headers=await token_de(client, otra.email),
                          json={"contenido": "¡Qué linda historia!"})
    assert r.status_code == 201
    detalle = (await client.get(f"/api/temas/{tema['id']}")).json()
    assert [x["contenido"] for x in detalle["respuestas"]] == ["¡Qué linda historia!"]
    lista = (await client.get("/api/foros/historias/temas")).json()
    assert lista["items"][0]["respuestas"] == 1 and lista["items"][0]["tiene_imagen"] is True
    mensajes = (await db.execute(select(Notificacion.mensaje).where(Notificacion.usuario_id == usuario.id))).scalars().all()
    assert any("Respondieron tu tema" in m for m in mensajes)


async def test_foto_sin_creditos_se_rechaza(client, db, auth_usuario):
    """RF-27: créditos obligatorios al fotógrafo y al cosplayer."""
    await _foros(db)
    sin_creditos = {**FOTO, "credito_fotografo": None}
    r = await client.post("/api/foros/confeccion/temas", headers=auth_usuario,
                          json={"titulo": "Mi armadura", "contenido": "Les muestro mi armadura", **sin_creditos})
    assert r.status_code == 422 and "fotógrafo" in r.text


async def _desafio(db, mes=None, anio=None):
    hoy = date.today()
    d = DesafioMensual(titulo="Cosplay reciclado", descripcion="Usa materiales reciclados",
                       mes=mes or hoy.month, anio=anio or hoy.year)
    db.add(d)
    await db.commit()
    return d


async def test_participar_en_desafio_una_vez_y_solo_si_esta_abierto(client, db, auth_usuario):
    d = await _desafio(db)
    datos = {"titulo": "Armadura de cartón", **FOTO}
    assert (await client.post(f"/api/desafios/{d.id}/participar", json=datos)).status_code == 401
    r = await client.post(f"/api/desafios/{d.id}/participar", headers=auth_usuario, json=datos)
    assert r.status_code == 201
    assert (await client.post(f"/api/desafios/{d.id}/participar", headers=auth_usuario, json=datos)).status_code == 409
    r = await client.post(f"/api/desafios/{d.id}/participar", headers=auth_usuario, json={"titulo": "Sin foto"})
    assert r.status_code == 422
    detalle = (await client.get(f"/api/desafios/{d.id}", headers=auth_usuario)).json()
    assert detalle["abierto"] and detalle["participaciones"] == 1 and detalle["ya_participo"]

    pasado = await _desafio(db, mes=1, anio=2025)
    r = await client.post(f"/api/desafios/{pasado.id}/participar", headers=auth_usuario, json=datos)
    assert r.status_code == 400


async def test_moderacion_lanza_desafio_y_elige_ganador(client, db, usuario, auth_usuario, auth_admin):
    hoy = date.today()
    sig_mes, sig_anio = (1, hoy.year + 1) if hoy.month == 12 else (hoy.month + 1, hoy.year)
    datos = {"titulo": "Desafío de pelucas", "descripcion": "Estiliza una peluca imposible", "mes": sig_mes, "anio": sig_anio}
    assert (await client.post("/api/moderacion/desafios", headers=auth_usuario, json=datos)).status_code == 403
    r = await client.post("/api/moderacion/desafios", headers=auth_admin, json=datos)
    assert r.status_code == 201
    did = r.json()["id"]
    assert (await client.post("/api/moderacion/desafios", headers=auth_admin, json=datos)).status_code == 409
    avisos = (await db.execute(select(Notificacion.mensaje).where(Notificacion.usuario_id == usuario.id))).scalars().all()
    assert any("Nuevo desafío mensual" in m for m in avisos)

    p = (await client.post(f"/api/desafios/{did}/participar", headers=auth_usuario, json={"titulo": "Peluca", **FOTO})).json()
    r = await client.post(f"/api/moderacion/desafios/{did}/ganador", headers=auth_admin, json={"participacion_id": p["id"]})
    assert r.json()["ganador"]["nombre"] == "Camila" and r.json()["abierto"] is False


async def test_reporte_ocultar_y_suspender_autor(client, db, usuario, auth_usuario, admin, auth_admin):
    """Reportar contenido (RF-38) -> Gestionar Soporte y Reportes -> Bloquear/Sancionar Usuario."""
    await _foros(db)
    troll = await crear_usuario(db, "troll@test.cl", nombre="Troll")
    h_troll = await token_de(client, troll.email)
    tema = (await client.post("/api/foros/confeccion/temas", headers=auth_usuario,
                              json={"titulo": "Duda de patronaje", "contenido": "¿Cómo ajusto una capa?"})).json()
    resp = (await client.post(f"/api/temas/{tema['id']}/respuestas", headers=h_troll,
                              json={"contenido": "Comentario ofensivo de prueba"})).json()

    BANDEJA_SIMULADA.clear()
    r = await client.post("/api/reportes", headers=auth_usuario, json={
        "tipo_objeto": "RESPUESTA", "objeto_id": resp["id"], "motivo": "ACOSO", "detalle": "Me está acosando"})
    assert r.status_code == 201
    assert any("Nuevo reporte" in c["asunto"] for c in BANDEJA_SIMULADA)  # correo a moderación
    assert (await client.get("/api/moderacion/resumen", headers=auth_admin)).json()["reportes_abiertos"] == 1

    assert (await client.get("/api/moderacion/reportes", headers=auth_usuario)).status_code == 403
    reportes = (await client.get("/api/moderacion/reportes", headers=auth_admin)).json()
    assert reportes[0]["objeto_texto"] == "Comentario ofensivo de prueba"
    assert reportes[0]["autor_objeto"]["nombre"] == "Troll"

    r = await client.post(f"/api/moderacion/reportes/{reportes[0]['id']}/resolver", headers=auth_admin,
                          json={"accion": "OCULTAR_Y_SUSPENDER", "resolucion": "Acoso a otra usuaria"})
    assert r.status_code == 200
    assert r.json()["estado"] == "RESUELTO" and r.json()["objeto_oculto"] is True
    assert r.json()["autor_objeto_estado"] == "SUSPENDIDO"

    # La respuesta ya no se ve y el troll no puede ingresar (UC-01 excepción 2)
    assert (await client.get(f"/api/temas/{tema['id']}")).json()["respuestas"] == []
    r = await client.post("/api/auth/login", json={"email": "troll@test.cl", "password": PASSWORD})
    assert r.status_code == 403
    assert (await client.get("/api/auth/me", headers=h_troll)).status_code == 403
    # No se puede resolver dos veces
    r = await client.post(f"/api/moderacion/reportes/{reportes[0]['id']}/resolver", headers=auth_admin,
                          json={"accion": "DESCARTAR", "resolucion": "Duplicado"})
    assert r.status_code == 409
    eventos = (await db.execute(select(RegistroAuditoria.evento))).scalars().all()
    assert {"NUEVO_REPORTE", "REPORTE_RESUELTO", "USUARIO_SUSPENDIDO"} <= set(eventos)


async def test_suspender_y_reactivar_usuario(client, db, admin, auth_admin):
    u = await crear_usuario(db, "x@test.cl", nombre="Persona X")
    r = await client.post(f"/api/moderacion/usuarios/{u.id}/suspender", headers=auth_admin, json={"motivo": "Spam reiterado"})
    assert r.json()["estado"] == "SUSPENDIDO"
    lista = (await client.get("/api/moderacion/usuarios?estado=SUSPENDIDO", headers=auth_admin)).json()
    assert [x["email"] for x in lista] == ["x@test.cl"]
    r = await client.post(f"/api/moderacion/usuarios/{u.id}/reactivar", headers=auth_admin)
    assert r.json()["estado"] == "ACTIVO"
    # No se puede suspender a moderación ni a sí mismo
    r = await client.post(f"/api/moderacion/usuarios/{admin.id}/suspender", headers=auth_admin, json={"motivo": "Prueba x"})
    assert r.status_code == 400


async def test_contacto_publico_llega_al_panel(client, db, admin, auth_admin):
    """RF-40 y UC-01 exc. 2: una persona suspendida, sin sesión, puede escribir."""
    BANDEJA_SIMULADA.clear()
    r = await client.post("/api/contacto", json={"nombre": "Cuenta suspendida", "email": "s@test.cl", "tipo": "CUENTA",
                                                 "asunto": "Mi cuenta está suspendida", "mensaje": "Creo que es un error, por favor revisen."})
    assert r.status_code == 201
    assert any("contacto" in c["asunto"] for c in BANDEJA_SIMULADA)
    mensajes = (await client.get("/api/moderacion/contactos", headers=auth_admin)).json()
    assert mensajes[0]["tipo"] == "CUENTA"
    await client.post(f"/api/moderacion/contactos/{mensajes[0]['id']}/atender", headers=auth_admin)
    assert (await client.get("/api/moderacion/contactos", headers=auth_admin)).json() == []
    assert (await db.execute(select(Contacto))).scalar_one().estado.value == "ATENDIDO"
    r = await client.post("/api/contacto", json={"nombre": "A", "email": "no-es-correo", "asunto": "x", "mensaje": "corto"})
    assert r.status_code == 422


async def test_bitacora_de_auditoria_visible_para_moderacion(client, db, auth_usuario, auth_admin):
    await client.post("/api/contacto", headers=auth_usuario, json={
        "nombre": "Camila", "email": "camila@test.cl", "asunto": "Sugerencia", "mensaje": "Agreguen más guías de pelucas"})
    bitacora = (await client.get("/api/moderacion/auditoria", headers=auth_admin)).json()
    assert bitacora[0]["evento"] == "CONTACTO_RECIBIDO" and bitacora[0]["actor"]["nombre"] == "Camila"
    usuario = (await db.execute(select(Usuario).where(Usuario.email == "camila@test.cl"))).scalar_one()
    assert usuario.estado == EstadoUsuario.ACTIVO
