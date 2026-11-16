"""Directorio (RF-11 a 14, 19, 32 a 34) y calendario (RF-15 a 17)."""
from datetime import date, timedelta

from sqlalchemy import select

from app.models import ComunidadGrupo, Evento, Notificacion, ProveedorServicio, Reporte, Tienda
from app.models.enums import EstadoPublicacion
from tests.conftest import token_de


async def _directorio(db):
    items = [
        ProveedorServicio(nombre="Sastrería Sur", region="BI", comuna="Concepción", especialidades=["SASTRERIA"],
                          servicios=["Patronaje"], precio_desde=20000, precio_hasta=90000, lat=-36.8, lng=-73.0),
        ProveedorServicio(nombre="Fotos Norte", region="AN", comuna="Antofagasta", especialidades=["FOTOGRAFIA"],
                          lat=-23.6, lng=-70.4),
        Tienda(nombre="EVA Store", region="RM", comuna="Maipú", tipos_producto=["TERMOPLASTICOS", "PINTURAS"],
               alcance="NACIONAL", tienda_fisica=True, envia_a_chile=True, lat=-33.5, lng=-70.7),
        Tienda(nombre="Wig World", region=None, tipos_producto=["PELUCAS"], alcance="INTERNACIONAL",
               tienda_fisica=False, envia_a_chile=True),
        ComunidadGrupo(nombre="Cosplay Biobío", region="BI", plataforma="Discord", lat=-36.82, lng=-73.04),
        ProveedorServicio(nombre="Inactivo", region="BI", especialidades=["SASTRERIA"], activo=False),
    ]
    db.add_all(items)
    await db.commit()
    return {i.nombre: i for i in items}


def _nombres(r):
    return sorted(i["nombre"] for i in r.json()["items"])


async def test_filtros_del_directorio(client, db):
    await _directorio(db)
    assert _nombres(await client.get("/api/directorio?region=BI")) == ["Cosplay Biobío", "Sastrería Sur"]
    assert _nombres(await client.get("/api/directorio?tipo=PROVEEDOR&especialidad=FOTOGRAFIA")) == ["Fotos Norte"]
    assert _nombres(await client.get("/api/directorio?tipo=TIENDA&tipo_producto=PINTURAS")) == ["EVA Store"]
    assert _nombres(await client.get("/api/directorio?tipo=TIENDA&alcance=INTERNACIONAL")) == ["Wig World"]
    assert _nombres(await client.get("/api/directorio?q=concepcion")) == ["Sastrería Sur"]
    assert "Inactivo" not in _nombres(await client.get("/api/directorio?por_pagina=50"))
    assert (await client.get("/api/directorio?region=XX")).status_code == 422


async def test_mapa_solo_incluye_fichas_con_coordenadas(client, db):
    await _directorio(db)
    puntos = (await client.get("/api/directorio/mapa")).json()
    assert {p["nombre"] for p in puntos} == {"Sastrería Sur", "Fotos Norte", "EVA Store", "Cosplay Biobío"}
    assert all(p["lat"] and p["lng"] for p in puntos)


async def test_ficha_publica_con_servicios_precios_y_region(client, db):
    items = await _directorio(db)
    r = await client.get(f"/api/directorio/{items['Sastrería Sur'].id}")
    ficha = r.json()
    assert ficha["servicios"] == ["Patronaje"] and ficha["precio_desde"] == 20000 and ficha["region"] == "BI"
    assert ficha["puede_resenar"] is False  # sin sesión
    assert (await client.get(f"/api/directorio/{items['Inactivo'].id}")).status_code == 404


async def test_resenas_solo_con_sesion_una_por_persona(client, db, usuario, auth_usuario, admin):
    items = await _directorio(db)
    ruta = f"/api/directorio/{items['Sastrería Sur'].id}/resenas"
    assert (await client.post(ruta, json={"calificacion": 5})).status_code == 401
    assert (await client.post(ruta, headers=auth_usuario, json={"calificacion": 6})).status_code == 422
    r = await client.post(ruta, headers=auth_usuario, json={"calificacion": 5, "comentario": "Excelente patronaje"})
    assert r.status_code == 201 and r.json()["autor"]["nombre"] == "Camila"
    assert (await client.post(ruta, headers=auth_usuario, json={"calificacion": 1})).status_code == 409
    await client.post(ruta, headers=await token_de(client, admin.email), json={"calificacion": 4})
    ficha = (await client.get(f"/api/directorio/{items['Sastrería Sur'].id}", headers=auth_usuario)).json()
    assert ficha["promedio"] == 4.5 and ficha["total_resenas"] == 2 and ficha["ya_resenado"] is True
    lista = (await client.get("/api/directorio?region=BI&tipo=PROVEEDOR")).json()["items"]
    assert lista[0]["promedio"] == 4.5
    # Las comunidades no se califican
    r = await client.post(f"/api/directorio/{items['Cosplay Biobío'].id}/resenas", headers=auth_usuario,
                          json={"calificacion": 5})
    assert r.status_code == 400


async def test_prestador_completa_su_ficha_y_no_puede_autocalificarse(client, db):
    r = await client.post("/api/auth/registro", json={
        "nombre": "Maquillaje Ñuble", "email": "maq@test.cl", "password": "Clave2026segura",
        "tipo_perfil": "MAQUILLADOR", "region": "NB", "perfil_publico": True, "acepta_privacidad": True})
    headers = {"Authorization": f"Bearer {r.json()['access_token']}"}
    r = await client.put("/api/directorio/mi-ficha", headers=headers, json={
        "servicios": ["Maquillaje FX", "Body paint"], "precio_desde": 15000, "precio_hasta": 60000,
        "comuna": "Chillán", "contacto": "+56 9 1111 2222", "region": "NB",
        "tipos_producto": ["TELAS"]})  # campo de tienda: se ignora para un proveedor
    assert r.status_code == 200, r.text
    ficha = r.json()
    assert ficha["servicios"] == ["Maquillaje FX", "Body paint"] and ficha["lat"] is not None
    assert ficha["tipos_producto"] is None
    r = await client.put("/api/directorio/mi-ficha", headers=headers, json={"precio_desde": 9, "precio_hasta": 1})
    assert r.status_code == 422
    r = await client.post(f"/api/directorio/{ficha['id']}/resenas", headers=headers, json={"calificacion": 5})
    assert r.status_code == 400


async def test_mi_ficha_sin_perfil_publico(client, auth_usuario):
    assert (await client.get("/api/directorio/mi-ficha", headers=auth_usuario)).status_code == 404


# ---------------------------------------------------------------- calendario
async def _eventos(db, admin):
    hoy = date.today()
    evs = [
        Evento(nombre="Convención Sur", tipo="CONVENCION", region="BI", lugar="Teatro", fecha_inicio=hoy + timedelta(days=10),
               fecha_fin=hoy + timedelta(days=11), enlace_oficial="https://conv.example", estado="PUBLICADO"),
        Evento(nombre="Meetup Valpo", tipo="MEETUP", region="VA", lugar="Parque Italia",
               fecha_inicio=hoy + timedelta(days=3), estado="PUBLICADO"),
        Evento(nombre="Evento pasado", tipo="MEETUP", region="RM", lugar="Plaza", fecha_inicio=hoy - timedelta(days=5),
               estado="PUBLICADO"),
        Evento(nombre="En curso", tipo="CONVENCION", region="RM", lugar="Centro", fecha_inicio=hoy - timedelta(days=1),
               fecha_fin=hoy + timedelta(days=1), estado="PUBLICADO"),
        Evento(nombre="Pendiente", tipo="TALLER", region="RM", lugar="Biblioteca", fecha_inicio=hoy + timedelta(days=4),
               estado="PENDIENTE"),
    ]
    db.add_all(evs)
    await db.commit()
    return {e.nombre: e for e in evs}


async def test_calendario_muestra_proximos_publicados_con_datos_de_rf16(client, db, admin):
    await _eventos(db, admin)
    r = (await client.get("/api/eventos")).json()
    assert [e["nombre"] for e in r["items"]] == ["En curso", "Meetup Valpo", "Convención Sur"]
    conv = r["items"][2]
    assert {"nombre", "fecha_inicio", "lugar", "tipo", "enlace_oficial"} <= conv.keys()
    assert [e["nombre"] for e in (await client.get("/api/eventos?region=VA")).json()["items"]] == ["Meetup Valpo"]
    assert [e["nombre"] for e in (await client.get("/api/eventos?tipo=CONVENCION")).json()["items"]] == ["En curso", "Convención Sur"]
    hasta = (date.today() + timedelta(days=5)).isoformat()
    assert len((await client.get(f"/api/eventos?hasta={hasta}")).json()["items"]) == 2


async def test_sugerir_evento_queda_pendiente_y_moderacion_lo_aprueba(client, db, usuario, auth_usuario, admin, auth_admin):
    datos = {"nombre": "Meetup Chillán", "tipo": "MEETUP", "region": "NB", "lugar": "Plaza de Armas",
             "fecha_inicio": (date.today() + timedelta(days=20)).isoformat(), "enlace_oficial": "https://meetup.example"}
    assert (await client.post("/api/eventos/sugerir", json=datos)).status_code == 401
    r = await client.post("/api/eventos/sugerir", headers=auth_usuario, json=datos)
    assert r.status_code == 201 and r.json()["estado"] == "PENDIENTE"
    evento_id = r.json()["id"]
    assert (await client.get("/api/eventos")).json()["total"] == 0
    assert (await client.get(f"/api/eventos/{evento_id}")).status_code == 404
    avisos = (await db.execute(select(Notificacion.mensaje).where(Notificacion.usuario_id == admin.id))).scalars().all()
    assert any("Meetup Chillán" in m for m in avisos)

    pendientes = (await client.get("/api/moderacion/eventos", headers=auth_admin)).json()
    assert [e["id"] for e in pendientes] == [evento_id]
    assert (await client.post(f"/api/moderacion/eventos/{evento_id}/aprobar", headers=auth_usuario)).status_code == 403
    r = await client.post(f"/api/moderacion/eventos/{evento_id}/aprobar", headers=auth_admin)
    assert r.json()["estado"] == "PUBLICADO"
    assert (await client.get("/api/eventos")).json()["total"] == 1
    mensajes = (await db.execute(select(Notificacion.mensaje).where(Notificacion.usuario_id == usuario.id))).scalars().all()
    assert any("ya está en el calendario" in m for m in mensajes)


async def test_sugerir_evento_valida_fechas(client, auth_usuario):
    base = {"nombre": "X evento", "tipo": "MEETUP", "region": "RM", "lugar": "Plaza"}
    ayer = (date.today() - timedelta(days=1)).isoformat()
    assert (await client.post("/api/eventos/sugerir", headers=auth_usuario, json={**base, "fecha_inicio": ayer})).status_code == 422
    manana = (date.today() + timedelta(days=1)).isoformat()
    r = await client.post("/api/eventos/sugerir", headers=auth_usuario,
                          json={**base, "fecha_inicio": manana, "fecha_fin": date.today().isoformat()})
    assert r.status_code == 422


async def test_reportar_actualizacion_de_evento_y_asistir(client, db, admin, auth_usuario):
    evs = await _eventos(db, admin)
    eid = evs["Meetup Valpo"].id
    r = await client.post("/api/reportes", headers=auth_usuario, json={
        "tipo_objeto": "EVENTO", "objeto_id": str(eid), "motivo": "ACTUALIZACION_EVENTO",
        "detalle": "Se cambió al Parque Alemania"})
    assert r.status_code == 201
    reporte = (await db.execute(select(Reporte))).scalar_one()
    assert reporte.motivo.value == "ACTUALIZACION_EVENTO" and reporte.estado.value == "ABIERTO"
    # repetir no duplica
    await client.post("/api/reportes", headers=auth_usuario, json={
        "tipo_objeto": "EVENTO", "objeto_id": str(eid), "motivo": "ACTUALIZACION_EVENTO"})
    assert len((await db.execute(select(Reporte))).scalars().all()) == 1

    r = await client.post(f"/api/eventos/{eid}/asistir", headers=auth_usuario)
    assert r.json() == {"asistire": True, "asistentes": 1}
    detalle = (await client.get(f"/api/eventos/{eid}", headers=auth_usuario)).json()
    assert detalle["asistire"] is True
    r = await client.post(f"/api/eventos/{eid}/asistir", headers=auth_usuario)
    assert r.json() == {"asistire": False, "asistentes": 0}


async def test_favoritos_de_eventos_y_proveedores(client, db, admin, auth_usuario):
    evs = await _eventos(db, admin)
    items = await _directorio(db)
    await client.post("/api/favoritos", headers=auth_usuario, json={"tipo": "EVENTO", "objeto_id": str(evs["Convención Sur"].id)})
    await client.post("/api/favoritos", headers=auth_usuario, json={"tipo": "DIRECTORIO", "objeto_id": str(items["EVA Store"].id)})
    r = await client.post("/api/favoritos", headers=auth_usuario, json={"tipo": "EVENTO", "objeto_id": str(evs["Pendiente"].id)})
    assert r.status_code == 404
    tipos = sorted(f["tipo"] for f in (await client.get("/api/favoritos", headers=auth_usuario)).json())
    assert tipos == ["DIRECTORIO", "EVENTO"]
    assert evs["Pendiente"].estado == EstadoPublicacion.PENDIENTE
