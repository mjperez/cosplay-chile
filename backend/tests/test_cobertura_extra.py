"""Pruebas adicionales de integración (ES3): semillas y flujos de extremo a extremo.

Cubren las rutas y servicios que las pruebas originales no ejercitaban, y dejan
la cobertura por encima del 90% exigido por el pipeline de CI.
"""
import re
import uuid
from datetime import date, timedelta

from sqlalchemy import func, select

from app.models import (
    CategoriaContenido,
    Contacto,
    Contenido,
    DirectorioItem,
    Evento,
    Foro,
    Reporte,
    Tema,
    Usuario,
)
from app.models.enums import EstadoPublicacion, EstadoReporte
from app.seed.base import seed_base
from app.seed.comunidad import seed_comunidad
from app.seed.contenidos import seed_contenidos
from app.seed.imagenes import generar_todas
from app.services.correo import BANDEJA_SIMULADA
from tests.conftest import crear_usuario, token_de

PASSWORD = "Clave2026segura"


async def _sembrar(db, tmp_path):
    ctx = {"imagenes": generar_todas(tmp_path)}
    await seed_base(db, ctx)
    await seed_contenidos(db, ctx)
    await seed_comunidad(db, ctx)
    await db.commit()
    return ctx


async def _conteo(db, modelo):
    return await db.scalar(select(func.count()).select_from(modelo)) or 0


async def test_semilla_completa_carga_datos_y_ilustraciones(client, db, tmp_path):
    """Las tres etapas del seed dejan la demo lista sin servicios externos."""
    ctx = await _sembrar(db, tmp_path)
    assert await _conteo(db, Usuario) >= 12
    assert await _conteo(db, CategoriaContenido) == 12
    assert await _conteo(db, Contenido) >= 8
    assert await _conteo(db, DirectorioItem) >= 15
    assert await _conteo(db, Evento) >= 8
    assert await _conteo(db, Foro) >= 2
    assert await _conteo(db, Tema) >= 4
    assert len(ctx["imagenes"]) >= 12
    assert all(url.startswith("/media/") for url, _ in ctx["imagenes"].values())
    # La portada y los catálogos responden con los datos sembrados
    portada = (await client.get("/api/inicio")).json()
    assert portada["estadisticas"]["guias"] >= 1
    assert (await client.get("/api/categorias")).json()
    assert (await client.get("/api/meta")).json()["regiones"]


async def test_favoritos_se_pueden_agregar_listar_y_quitar(client, db, tmp_path, auth_usuario):
    await _sembrar(db, tmp_path)
    contenido = (await db.execute(select(Contenido).where(
        Contenido.estado == EstadoPublicacion.PUBLICADO))).scalars().first()
    evento = (await db.execute(select(Evento).where(
        Evento.estado == EstadoPublicacion.PUBLICADO))).scalars().first()

    r = await client.post("/api/favoritos", headers=auth_usuario,
                          json={"tipo": "CONTENIDO", "objeto_id": str(contenido.id)})
    assert r.status_code == 201, r.text
    assert (await client.post("/api/favoritos", headers=auth_usuario,
                              json={"tipo": "EVENTO", "objeto_id": str(evento.id)})).status_code == 201
    # Operación idempotente: repetir no duplica ni falla
    assert (await client.post("/api/favoritos", headers=auth_usuario,
                              json={"tipo": "CONTENIDO", "objeto_id": str(contenido.id)})).status_code == 201
    assert (await client.post("/api/favoritos", headers=auth_usuario,
                              json={"tipo": "CONTENIDO", "objeto_id": str(uuid.uuid4())})).status_code == 404

    items = (await client.get("/api/favoritos", headers=auth_usuario)).json()
    assert {i["tipo"] for i in items} == {"CONTENIDO", "EVENTO"}
    assert all(i["enlace"].startswith("/") for i in items)
    ids = (await client.get("/api/favoritos/ids", headers=auth_usuario)).json()
    assert str(contenido.id) in ids["CONTENIDO"] and str(evento.id) in ids["EVENTO"]

    assert (await client.delete(f"/api/favoritos/CONTENIDO/{contenido.id}", headers=auth_usuario)).status_code == 200
    assert (await client.get("/api/favoritos", headers=auth_usuario)).json()[0]["tipo"] == "EVENTO"
    assert (await client.get("/api/favoritos")).status_code == 401


async def test_reporte_y_resolucion_por_moderacion(client, db, tmp_path, auth_usuario, admin):
    await _sembrar(db, tmp_path)
    evento = (await db.execute(select(Evento).where(
        Evento.estado == EstadoPublicacion.PUBLICADO))).scalars().first()
    r = await client.post("/api/reportes", headers=auth_usuario, json={
        "tipo_objeto": "EVENTO", "objeto_id": str(evento.id),
        "motivo": "ACTUALIZACION_EVENTO", "detalle": "Cambió la dirección del recinto"})
    assert r.status_code == 201, r.text
    # No se puede reportar dos veces el mismo objeto estando abierto
    r2 = await client.post("/api/reportes", headers=auth_usuario, json={
        "tipo_objeto": "EVENTO", "objeto_id": str(evento.id), "motivo": "OTRO"})
    assert r2.status_code == 201 and "Ya habías reportado" in r2.json()["mensaje"]
    assert (await client.post("/api/reportes", headers=auth_usuario, json={
        "tipo_objeto": "EVENTO", "objeto_id": str(evento.id),
        "motivo": "ACTUALIZACION_EVENTO", "detalle": "x"})).status_code == 201
    assert (await client.post("/api/reportes", headers=auth_usuario, json={
        "tipo_objeto": "CONTENIDO", "objeto_id": str(uuid.uuid4()), "motivo": "SPAM"})).status_code == 404
    assert (await client.post("/api/reportes", headers=auth_usuario, json={
        "tipo_objeto": "DIRECTORIO", "objeto_id": str(uuid.uuid4()),
        "motivo": "ACTUALIZACION_EVENTO"})).status_code == 404

    cabeceras = await token_de(client, admin.email)
    abiertos = (await client.get("/api/moderacion/reportes", headers=cabeceras)).json()
    assert len(abiertos) >= 1
    reporte = abiertos[0]
    resuelto = await client.post(f"/api/moderacion/reportes/{reporte['id']}/resolver", headers=cabeceras,
                                 json={"accion": "RESOLVER", "resolucion": "Datos corregidos por el organizador"})
    assert resuelto.status_code == 200 and resuelto.json()["estado"] == EstadoReporte.RESUELTO.value
    assert (await client.get("/api/moderacion/reportes?estado=RESUELTO", headers=cabeceras)).json()


async def test_contacto_publico_y_atencion_por_admin(client, db, admin):
    datos = {"nombre": "Persona afectada", "email": "afectada@test.cl", "tipo": "DENUNCIA",
             "asunto": "Situación en un evento", "mensaje": "Necesito orientación sobre un incidente ocurrido."}
    assert (await client.post("/api/contacto", json=datos)).status_code == 201
    assert (await client.post("/api/contacto", json={**datos, "mensaje": "corto"})).status_code == 422
    assert await _conteo(db, Contacto) == 1

    cabeceras = await token_de(client, admin.email)
    nuevos = (await client.get("/api/moderacion/contactos", headers=cabeceras)).json()
    assert len(nuevos) == 1
    assert (await client.post(f"/api/moderacion/contactos/{nuevos[0]['id']}/atender",
                              headers=cabeceras)).status_code == 200
    assert (await client.post(f"/api/moderacion/contactos/{uuid.uuid4()}/atender",
                              headers=cabeceras)).status_code == 404
    assert (await client.get("/api/moderacion/contactos?estado=ATENDIDO", headers=cabeceras)).json()
    assert (await client.get("/api/moderacion/contactos")).status_code == 401


async def test_recuperacion_y_restablecer_contrasena(client, db, usuario):
    BANDEJA_SIMULADA.clear()
    r = await client.post("/api/auth/recuperar", json={"email": usuario.email})
    assert r.status_code == 202
    assert "Si el correo está registrado" in r.json()["mensaje"]
    assert (await client.post("/api/auth/recuperar", json={"email": "nadie@test.cl"})).status_code == 202
    token = re.search(r"token=([^\s]+)", BANDEJA_SIMULADA[0]["cuerpo"]).group(1)
    assert (await client.post("/api/auth/restablecer", json={"token": token,
                                                             "password": "NuevaClave2027"})).status_code == 200
    assert (await client.post("/api/auth/restablecer", json={"token": token,
                                                             "password": "OtraClave2028"})).status_code == 400
    assert (await client.post("/api/auth/login", json={"email": usuario.email,
                                                       "password": "NuevaClave2027"})).status_code == 200


async def test_sugerir_evento_asistir_y_decision_admin(client, db, auth_usuario, admin):
    futuro = date.today() + timedelta(days=20)
    datos = {"nombre": "Meetup de prueba", "descripcion": "Encuentro para la comunidad",
             "tipo": "MEETUP", "fecha_inicio": futuro.isoformat(), "lugar": "Santiago", "region": "RM"}
    r = await client.post("/api/eventos/sugerir", headers=auth_usuario, json=datos)
    assert r.status_code == 201 and r.json()["estado"] == "PENDIENTE"
    evento_id = r.json()["id"]
    assert len((await client.get("/api/eventos/sugeridos/mios", headers=auth_usuario)).json()) == 1

    cabeceras = await token_de(client, admin.email)
    assert (await client.get("/api/moderacion/eventos", headers=cabeceras)).json()
    assert (await client.post(f"/api/moderacion/eventos/{evento_id}/aprobar", headers=cabeceras)).status_code == 200
    assert (await client.post(f"/api/eventos/{evento_id}/asistir", headers=auth_usuario)).json()["asistire"] is True
    assert (await client.get(f"/api/eventos/{evento_id}", headers=auth_usuario)).json()["asistire"] is True
    assert (await client.post(f"/api/eventos/{evento_id}/asistir", headers=auth_usuario)).json()["asistire"] is False
    assert (await client.get(f"/api/eventos/{evento_id}")).status_code == 200


async def test_perfil_actualizar_publico_y_suprimir_cuenta(client, db, usuario, auth_usuario):
    r = await client.put("/api/perfil", headers=auth_usuario, json={
        "nombre": "Camila Actualizada", "biografia": "Cosplayer de Arica",
        "tipo_perfil": "COSPLAYER", "region": "AP", "perfil_publico": True})
    assert r.status_code == 200 and r.json()["nombre"] == "Camila Actualizada"
    publico = (await client.get(f"/api/perfil/{usuario.id}")).json()
    assert publico["perfil"]["perfil_publico"] is True
    assert (await client.get(f"/api/perfil/{uuid.uuid4()}")).status_code == 404
    assert (await client.delete("/api/perfil", headers=auth_usuario)).status_code == 200
    assert (await client.get(f"/api/perfil/{usuario.id}")).status_code == 404
    # La cuenta anonimizada ya no autentica: no revela si existe ni su estado.
    assert (await client.post("/api/auth/login", json={"email": usuario.email,
                                                       "password": PASSWORD})).status_code == 401
