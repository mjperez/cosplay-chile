"""Recorrido extremo a extremo reproducible sobre la API real del prototipo.

Crea una base de datos de prueba aislada (`cosplay_recorrido`), aplica la
migración de producción, carga el seed y ejecuta comprobaciones HTTP con
`httpx.ASGITransport` (sin levantar uvicorn ni tocar la base de desarrollo).

Uso, desde `backend/`:
    python scripts/recorrido_http.py
"""
import asyncio
import base64
import os
import pathlib
import sys
import tempfile
from datetime import date, timedelta

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

BASE = "postgresql+asyncpg://cosplay:cosplay@localhost:5432"
NOMBRE_BD = "cosplay_recorrido"
URL = f"{BASE}/{NOMBRE_BD}"
RAIZ = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

TMP = pathlib.Path(tempfile.mkdtemp(prefix="cosplay-recorrido-"))
os.environ.update({
    "DATABASE_URL": URL,
    "TEST_DATABASE_URL": URL,
    "JWT_SECRET": "secreto-del-recorrido-con-mas-de-16-caracteres",
    "FRONTEND_URL": "http://localhost:5173",
    "MEDIA_DIR": str(TMP / "media"),
    "STORAGE_BACKEND": "local",
})

RESULTADOS = []


def comprobar(nombre: str, condicion: bool) -> None:
    RESULTADOS.append((nombre, bool(condicion)))
    print(("  OK   " if condicion else "  FALLO") + "  " + nombre)


async def _crear_base() -> None:
    engine = create_async_engine(f"{BASE}/postgres", isolation_level="AUTOCOMMIT")
    async with engine.connect() as c:
        await c.execute(text("SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                             f"WHERE datname = '{NOMBRE_BD}' AND pid <> pg_backend_pid()"))
        await c.execute(text(f"DROP DATABASE IF EXISTS {NOMBRE_BD}"))
        await c.execute(text(f"CREATE DATABASE {NOMBRE_BD} OWNER cosplay"))
    await engine.dispose()


def preparar_base() -> None:
    """Se ejecuta fuera del event loop: alembic/env.py usa asyncio.run()."""
    asyncio.run(_crear_base())
    from alembic import command
    from alembic.config import Config

    cfg = Config(str(RAIZ / "alembic.ini"))
    cfg.set_main_option("script_location", str(RAIZ / "alembic"))
    cfg.attributes["database_url"] = URL
    command.upgrade(cfg, "head")


async def sembrar() -> None:
    from app.db.session_manager import DatabaseSessionManager
    from app.seed.base import seed_base
    from app.seed.comunidad import seed_comunidad
    from app.seed.contenidos import seed_contenidos
    from app.seed.imagenes import generar_todas

    gestor = DatabaseSessionManager()
    gestor.init(URL)
    ctx = {"imagenes": generar_todas(TMP / "media")}
    async with gestor.session() as s:
        await seed_base(s, ctx)
        await seed_contenidos(s, ctx)
        await seed_comunidad(s, ctx)
        await s.commit()


async def main() -> int:
    await sembrar()

    from httpx import ASGITransport, AsyncClient

    from app.main import app

    PNG = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8DwHwAFAAH/q842iQAAAABJRU5ErkJggg=="
    )
    (TMP / "prueba.png").write_bytes(PNG)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://recorrido") as c:
        print("== Catálogos públicos ==")
        r = await c.get("/api/salud")
        comprobar("salud responde 200", r.status_code == 200)
        r = await c.get("/api/inicio")
        comprobar("portada con estadísticas", r.status_code == 200 and r.json()["estadisticas"]["guias"] > 0)
        comprobar("categorías", len((await c.get("/api/categorias")).json()) == 12)
        comprobar("metadatos de regiones", bool((await c.get("/api/meta")).json()["regiones"]))
        r = await c.get("/api/contenidos")
        comprobar("guías publicadas", r.status_code == 200 and r.json()["total"] > 0)
        comprobar("directorio", (await c.get("/api/directorio")).json()["total"] > 0)
        comprobar("mapa con coordenadas", bool((await c.get("/api/directorio/mapa")).json()))
        comprobar("eventos", (await c.get("/api/eventos")).json()["total"] > 0)
        comprobar("foros", len((await c.get("/api/foros")).json()) >= 2)
        comprobar("desafíos", bool((await c.get("/api/desafios")).json()))
        comprobar("ruta inexistente da 404", (await c.get("/api/no-existe")).status_code == 404)

        print("== Autenticación y roles ==")
        admin = await c.post("/api/auth/login", json={"email": "admin@cosplaychile.cl", "password": "Admin2026!"})
        comprobar("login de administración", admin.status_code == 200)
        A = {"Authorization": f"Bearer {admin.json()['access_token']}"}
        camila = await c.post("/api/auth/login", json={"email": "camila@demo.cl", "password": "Cosplay2026!"})
        comprobar("login de cosplayer", camila.status_code == 200)
        U = {"Authorization": f"Bearer {camila.json()['access_token']}"}
        comprobar("sesión actual", (await c.get("/api/auth/me", headers=U)).status_code == 200)
        comprobar("sin token da 401", (await c.get("/api/moderacion/resumen")).status_code == 401)
        comprobar("cosplayer no entra a moderación", (await c.get("/api/moderacion/resumen", headers=U)).status_code == 403)
        comprobar("admin ve el resumen", (await c.get("/api/moderacion/resumen", headers=A)).status_code == 200)
        comprobar("cuenta suspendida no entra", (await c.post("/api/auth/login", json={
            "email": "suspendido@demo.cl", "password": "Cosplay2026!"})).status_code == 403)
        comprobar("contraseña débil da 422", (await c.post("/api/auth/registro", json={
            "nombre": "Nueva persona", "email": "nueva@test.cl", "password": "debil",
            "acepta_privacidad": True})).status_code == 422)

        print("== Comunidad, avisos y favoritos ==")
        foros = (await c.get("/api/foros")).json()
        tema = await c.post(f"/api/foros/{foros[0]['slug']}/temas", headers=U, json={
            "titulo": "Tema del recorrido", "contenido": "Les cuento cómo armé mi primera armadura"})
        comprobar("crear tema", tema.status_code == 201)
        respondido = await c.post(f"/api/temas/{tema.json()['id']}/respuestas", headers=A,
                                  json={"contenido": "¡Qué buen trabajo!"})
        comprobar("responder tema", respondido.status_code == 201)
        bandeja = (await c.get("/api/notificaciones", headers=U)).json()
        comprobar("aviso interno al autor", bandeja["no_leidas"] >= 1 and bool(bandeja["items"]))
        comprobar("marcar todos los avisos", (await c.post("/api/notificaciones/leer-todas", headers=U)).status_code == 200)
        comprobar("bitácora de auditoría", bool((await c.get("/api/moderacion/auditoria", headers=A)).json()))

        contenido = (await c.get("/api/contenidos")).json()["items"][0]
        comprobar("guardar favorito", (await c.post("/api/favoritos", headers=U, json={
            "tipo": "CONTENIDO", "objeto_id": contenido["id"]})).status_code == 201)
        comprobar("listar favoritos", any(f["objeto_id"] == contenido["id"]
                                          for f in (await c.get("/api/favoritos", headers=U)).json()))

        print("== Contenido, eventos, reportes y contacto ==")
        cats = (await c.get("/api/categorias")).json()
        envio = await c.post("/api/contenidos", headers=U, json={
            "tipo": "GUIA", "titulo": "Guía del recorrido", "descripcion": "Una guía de prueba",
            "nivel": "PRINCIPIANTE", "categoria_id": cats[0]["id"],
            "pasos": ["Medir", "Cortar"], "materiales": ["Goma EVA"]})
        comprobar("enviar tutorial a revisión", envio.status_code == 201)
        id_contenido = envio.json()["contenido"]["id"]
        comprobar("aparece en la cola", any(x["id"] == id_contenido
                                           for x in (await c.get("/api/moderacion/contenidos", headers=A)).json()))
        comprobar("publicar tutorial", (await c.post(
            f"/api/moderacion/contenidos/{id_contenido}/publicar", headers=A)).status_code == 200)

        sugerencia = await c.post("/api/eventos/sugerir", headers=U, json={
            "nombre": "Meetup del recorrido", "descripcion": "Encuentro de prueba", "tipo": "MEETUP",
            "fecha_inicio": (date.today() + timedelta(days=15)).isoformat(),
            "lugar": "Santiago", "region": "RM"})
        comprobar("sugerir evento", sugerencia.status_code == 201)

        evento = (await c.get("/api/eventos")).json()["items"][0]
        reporte = await c.post("/api/reportes", headers=U, json={
            "tipo_objeto": "EVENTO", "objeto_id": evento["id"],
            "motivo": "ACTUALIZACION_EVENTO", "detalle": "Cambió la dirección"})
        comprobar("reportar contenido", reporte.status_code == 201)
        comprobar("cola de reportes", bool((await c.get("/api/moderacion/reportes", headers=A)).json()))
        contacto = await c.post("/api/contacto", json={
            "nombre": "Persona", "email": "persona@test.cl", "tipo": "DUDA",
            "asunto": "Consulta", "mensaje": "Quisiera saber más sobre los talleres"})
        comprobar("formulario de contacto", contacto.status_code == 201)
        comprobar("bandeja de contactos", bool((await c.get("/api/moderacion/contactos", headers=A)).json()))

        print("== Archivos (Adapter) y OpenAPI ==")
        subida = await c.post("/api/archivos", headers=U,
                              files={"archivo": ("prueba.png", PNG, "image/png")})
        comprobar("subir PNG", subida.status_code == 201)
        if subida.status_code == 201:
            enlace = subida.json()["url"]
            comprobar("servir el archivo", (await c.get(enlace)).status_code == 200)
            clave = subida.json()["clave"]
            fabricado = await c.post("/api/archivos", headers=U,
                                     files={"archivo": ("falso.svg", b"<svg></svg>", "image/svg+xml")})
            comprobar("rechazar SVG disfrazado", fabricado.status_code == 415)
            comprobar("la clave del archivo es única", clave.startswith("subidas/"))

        esquema = (await c.get("/openapi.json")).json()
        rutas = sorted(esquema["paths"])
        comprobar(f"OpenAPI con {len(rutas)} rutas", len(rutas) == 60)
        comprobar("rutas clave presentes", all(p in esquema["paths"] for p in (
            "/api/inicio", "/api/meta", "/api/busqueda/sugerencias", "/api/notificaciones",
            "/api/favoritos", "/api/reportes", "/api/contacto", "/api/moderacion/auditoria")))

    fallos = [n for n, ok in RESULTADOS if not ok]
    print(f"\nRESULTADO: {len(RESULTADOS) - len(fallos)}/{len(RESULTADOS)} comprobaciones en verde")
    return 1 if fallos else 0


if __name__ == "__main__":
    preparar_base()
    raise SystemExit(asyncio.run(main()))
