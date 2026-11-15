#!/usr/bin/env python3
"""Recorrido extremo a extremo real sobre HTTP (sin TestClient).

Prepara una base SQLite temporal, aplica `alembic upgrade head`, carga las dos
semillas, levanta `uvicorn` en un puerto libre y ejecuta peticiones HTTP reales
con `httpx`. Es la verificación que se cita en `GUIA_DEMO.md` y en
`tests/casos_por_rf.md`; no forma parte de `pytest` porque necesita un proceso
servidor y un esquema propio.

Uso:

    cd backend && .venv/bin/python scripts/recorrido_http.py

Sale con 0 si todas las comprobaciones pasan y con 1 en caso contrario.
"""

from __future__ import annotations

import base64
import os
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import httpx

RAIZ = Path(__file__).resolve().parents[1]
PUERTO = 8791
BASE = f"http://127.0.0.1:{PUERTO}"
API = f"{BASE}/api/v1"

# PNG 1x1 válido: empieza con la firma \x89PNG\r\n\x1a\n.
PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8"
    "z8DwHwAFAAH/q842iQAAAABJRU5ErkJggg=="
)

resultados: list[tuple[bool, str, str]] = []


def check(nombre: str, condicion: bool, detalle: str = "") -> None:
    resultados.append((bool(condicion), nombre, detalle))
    marca = "OK  " if condicion else "FAIL"
    print(f"[{marca}] {nombre}" + (f" · {detalle}" if detalle else ""))


def entorno(directorio: Path) -> dict[str, str]:
    env = os.environ.copy()
    env.update(
        {
            "DATABASE_URL": f"sqlite+pysqlite:///{(directorio / 'demo.db').as_posix()}",
            "JWT_SECRET": "clave-de-recorrido-con-mas-de-16-caracteres",
            "ENVIRONMENT": "local",
            "BCRYPT_ROUNDS": "4",
            "DEMO_SEED": "1",
            "STORAGE_BACKEND": "local",
            "STORAGE_DIRECTORIO": str(directorio / "archivos"),
            "CORS_ORIGINS": "http://localhost:5173",
        }
    )
    return env


def esperar_servicio(cliente: httpx.Client, proceso: subprocess.Popen) -> bool:
    for _ in range(60):
        if proceso.poll() is not None:
            return False
        try:
            if cliente.get("/health", timeout=1).status_code == 200:
                return True
        except httpx.HTTPError:
            pass
        time.sleep(0.5)
    return False


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="cosplay-recorrido-") as temporal:
        directorio = Path(temporal)
        env = entorno(directorio)

        for comando in (
            [sys.executable, "-m", "alembic", "upgrade", "head"],
            [sys.executable, "-m", "app.seed.datos_base"],
            [sys.executable, "-m", "app.seed.demo"],
        ):
            paso = subprocess.run(
                comando, cwd=RAIZ, env=env, capture_output=True, text=True
            )
            if paso.returncode != 0:
                print(f"No se pudo preparar la base: {' '.join(comando)}")
                print(paso.stdout[-2000:])
                print(paso.stderr[-2000:])
                return 1

        with socket.socket() as zocalo:
            zocalo.bind(("127.0.0.1", 0))
            puerto_libre = zocalo.getsockname()[1]
        global PUERTO, BASE, API
        PUERTO = puerto_libre
        BASE = f"http://127.0.0.1:{PUERTO}"
        API = f"{BASE}/api/v1"

        proceso = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "app.main:app",
                "--host",
                "127.0.0.1",
                "--port",
                str(PUERTO),
                "--log-level",
                "warning",
            ],
            cwd=RAIZ,
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )

        try:
            with httpx.Client(base_url=BASE, timeout=10) as cliente:
                if not esperar_servicio(cliente, proceso):
                    print("El servidor no levantó a tiempo.")
                    if proceso.stderr:
                        print(proceso.stderr.read().decode(errors="replace")[-2000:])
                    return 1

                # --- 1. Salud y contrato ----------------------------------
                r = cliente.get("/health")
                check("GET /health responde 200 con status ok",
                      r.status_code == 200 and r.json().get("status") == "ok")
                check("GET /health reporta el entorno local",
                      r.json().get("environment") == "local")

                esquema = cliente.get("/openapi.json")
                rutas = esquema.json().get("paths", {}) if esquema.status_code == 200 else {}
                check("OpenAPI expone 49 rutas", len(rutas) == 49, f"{len(rutas)} rutas")
                for nueva in (
                    "/api/v1/notificaciones/sin-leer",
                    "/api/v1/archivos",
                    "/api/v1/admin/auditoria",
                ):
                    check(f"OpenAPI incluye {nueva}", nueva in rutas)

                check("GET /docs responde 200", cliente.get("/docs").status_code == 200)

                # --- 2. Autenticación y autorización -----------------------
                def login(correo: str, password: str = "Demo2026!") -> httpx.Response:
                    return cliente.post(
                        f"{API}/auth/login", json={"correo": correo, "password": password}
                    )

                admin = login("demo@cosplay.cl")
                cosplayer = login("cosplayer@cosplay.cl")
                organizador = login("organizador@cosplay.cl")
                check("Login del administrador demo", admin.status_code == 200)
                check("Login del cosplayer demo", cosplayer.status_code == 200)
                check("Login del organizador demo", organizador.status_code == 200)
                check("Login con contraseña incorrecta da 401",
                      login("demo@cosplay.cl", "incorrecta").status_code == 401)

                t_admin = admin.json()["access_token"]
                t_cos = cosplayer.json()["access_token"]
                H_ADMIN = {"Authorization": f"Bearer {t_admin}"}
                H_COS = {"Authorization": f"Bearer {t_cos}"}

                check("GET /auth/me con token devuelve rol administrador",
                      cliente.get(f"{API}/auth/me", headers=H_ADMIN).json().get("rol")
                      == "administrador")
                check("GET /auth/me sin token da 401",
                      cliente.get(f"{API}/auth/me").status_code == 401)
                check("GET /admin/resumen sin token da 401",
                      cliente.get(f"{API}/admin/resumen").status_code == 401)
                check("GET /admin/resumen con cosplayer da 403",
                      cliente.get(f"{API}/admin/resumen", headers=H_COS).status_code == 403)
                check("GET /admin/resumen con admin da 200",
                      cliente.get(f"{API}/admin/resumen", headers=H_ADMIN).status_code == 200)
                check("GET /admin/auditoria con cosplayer da 403",
                      cliente.get(f"{API}/admin/auditoria", headers=H_COS).status_code == 403)

                # --- 3. Catálogos y módulos --------------------------------
                check("GET /proveedores trae las 20 fichas reales",
                      cliente.get(f"{API}/proveedores").json().get("total") == 20)
                check("GET /contenido lista los publicados",
                      cliente.get(f"{API}/contenido").status_code == 200)
                check("GET /eventos responde 200", cliente.get(f"{API}/eventos").status_code == 200)
                check("GET /foro/temas responde 200", cliente.get(f"{API}/foro/temas").status_code == 200)
                check("GET /desafios/vigente responde 200",
                      cliente.get(f"{API}/desafios/vigente").status_code == 200)
                check("GET /tiendas responde 200", cliente.get(f"{API}/tiendas").status_code == 200)
                check("GET /grupos responde 200", cliente.get(f"{API}/grupos").status_code == 200)
                check("GET /perfiles/mio con sesión responde 200",
                      cliente.get(f"{API}/perfiles/mio", headers=H_COS).status_code == 200)
                check("GET /admin/usuarios con admin responde 200",
                      cliente.get(f"{API}/admin/usuarios", headers=H_ADMIN).status_code == 200)

                # --- 4. Adapter: subida de imágenes ------------------------
                check("POST /archivos sin token da 401",
                      cliente.post(f"{API}/archivos",
                                   files={"archivo": ("f.png", PNG, "image/png")}).status_code == 401)

                subida = cliente.post(
                    f"{API}/archivos",
                    files={"archivo": ("foto.png", PNG, "image/png")},
                    headers=H_COS,
                )
                check("POST /archivos con PNG válido da 201", subida.status_code == 201)
                enlace = subida.json().get("enlace", "") if subida.status_code == 201 else ""
                check("El enlace devuelto es una URL absoluta", enlace.startswith("http"))
                check("POST /archivos con SVG que dice PNG da 415",
                      cliente.post(f"{API}/archivos",
                                   files={"archivo": ("falso.png", b"<svg onload='x'/>", "image/png")},
                                   headers=H_COS).status_code == 415)
                check("POST /archivos con archivo vacío da 400",
                      cliente.post(f"{API}/archivos",
                                   files={"archivo": ("vacio.png", b"", "image/png")},
                                   headers=H_COS).status_code == 400)

                servido = cliente.get(enlace) if enlace else None
                check("GET del enlace sirve la imagen",
                      servido is not None and servido.status_code == 200
                      and servido.content.startswith(b"\x89PNG"))

                # Borrado ajeno y propio.
                subida_admin = cliente.post(
                    f"{API}/archivos",
                    files={"archivo": ("admin.png", PNG, "image/png")},
                    headers=H_ADMIN,
                )
                id_admin = subida_admin.json().get("identificador", "")
                check("Un cosplayer no puede borrar la imagen del admin (403)",
                      cliente.delete(f"{API}/archivos/{id_admin}", headers=H_COS).status_code == 403)

                id_propio = subida.json().get("identificador", "")
                check("El dueño borra su imagen (204)",
                      cliente.delete(f"{API}/archivos/{id_propio}", headers=H_COS).status_code == 204)
                check("Borrar dos veces da 404",
                      cliente.delete(f"{API}/archivos/{id_propio}", headers=H_COS).status_code == 404)

                # --- 5. Factory + Observer: enviar tutorial ----------------
                payload = {
                    "tipo": "guia",
                    "titulo": "Guía de prueba ES3 con imagen",
                    "resumen": "Recorrido HTTP real",
                    "nivel": "basico",
                    "cuerpo": "<p>Contenido de prueba</p>",
                    "imagenes": [enlace],
                    "video_url": None,
                    "id_categoria": None,
                    "personaje": "Personaje de prueba",
                    "pasos": ["Trazo", "Corte"],
                }
                creado = cliente.post(f"{API}/contenido", json=payload, headers=H_COS)
                check("POST /contenido crea el borrador (201)", creado.status_code == 201,
                      str(creado.status_code))
                datos_creados = creado.json() if creado.status_code == 201 else {}
                check("El borrador queda en estado pendiente",
                      datos_creados.get("estado") == "pendiente")
                check("El borrador conserva la imagen subida",
                      enlace in (datos_creados.get("imagenes") or []))
                check("POST /contenido con nivel inválido da 422",
                      cliente.post(f"{API}/contenido",
                                   json={**payload, "nivel": "principiante"},
                                   headers=H_COS).status_code == 422)

                check("GET /notificaciones sin token da 401",
                      cliente.get(f"{API}/notificaciones").status_code == 401)
                check("GET /notificaciones/sin-leer sin token da 401",
                      cliente.get(f"{API}/notificaciones/sin-leer").status_code == 401)

                avisos_cos = cliente.get(f"{API}/notificaciones?limite=100", headers=H_COS)
                check("El autor recibe aviso interno por el envío a revisión",
                      avisos_cos.status_code == 200 and avisos_cos.json().get("total", 0) >= 1)

                bitacora = cliente.get(f"{API}/admin/auditoria?limite=100", headers=H_ADMIN)
                tipos = {fila["tipo_evento"] for fila in bitacora.json().get("elementos", [])} \
                    if bitacora.status_code == 200 else set()
                check("GET /admin/auditoria con admin da 200", bitacora.status_code == 200)
                check("La bitácora registra contenido_enviado_revision",
                      "contenido_enviado_revision" in tipos)
                check("La bitácora registra el correo a moderación",
                      any(fila["categoria"] == "correo_moderacion"
                          for fila in bitacora.json().get("elementos", [])),
                      )

                # --- 6. Observer: crear evento y avisar --------------------
                evento = cliente.post(
                    f"{API}/admin/eventos",
                    json={
                        "nombre": "Convención de prueba ES3",
                        "tipo": "convencion",
                        "fecha_inicio": "2026-12-01T10:00:00Z",
                        "lugar": "Santiago",
                        "region": "Metropolitana",
                    },
                    headers=H_ADMIN,
                )
                check("POST /admin/eventos crea el evento (201)", evento.status_code == 201,
                      str(evento.status_code))

                sin_leer = cliente.get(f"{API}/notificaciones/sin-leer", headers=H_COS)
                check("Crear evento genera avisos a la comunidad",
                      sin_leer.status_code == 200 and sin_leer.json().get("sin_leer", 0) >= 2,
                      f"sin_leer={sin_leer.json().get('sin_leer')}")

                bitacora2 = cliente.get(f"{API}/admin/auditoria?limite=100", headers=H_ADMIN)
                check("La bitácora registra evento_creado",
                      any(fila["tipo_evento"] == "evento_creado"
                          for fila in bitacora2.json().get("elementos", [])))

                pendientes = cliente.get(
                    f"{API}/notificaciones?solo_no_leidas=true&limite=100", headers=H_COS
                )
                primer = pendientes.json().get("elementos", [{}])[0].get("id_notificacion")
                marcada = cliente.patch(
                    f"{API}/notificaciones/{primer}/leer", headers=H_COS
                )
                check("PATCH /notificaciones/{id}/leer marca como leída",
                      marcada.status_code == 200 and marcada.json().get("leida") is True)

                # --- 7. Bandeja editorial ----------------------------------
                id_contenido = creado.json().get("id_contenido") if creado.status_code == 201 else None
                if id_contenido:
                    publicado = cliente.post(
                        f"{API}/admin/contenido/{id_contenido}/publicar", headers=H_ADMIN
                    )
                    check("Publicar el borrador desde el panel da 200",
                          publicado.status_code == 200 and publicado.json().get("estado") == "publicado")
                else:
                    check("Publicar el borrador desde el panel da 200", False)

                tema = cliente.post(
                    f"{API}/foro/temas",
                    json={"titulo": "Tema del recorrido ES3",
                          "categoria": "Eventos y comunidad",
                          "contenido": "Mensaje de prueba del recorrido HTTP."},
                    headers=H_COS,
                )
                check("POST /foro/temas con sesión crea el tema",
                      tema.status_code in (200, 201), str(tema.status_code))
        finally:
            proceso.terminate()
            try:
                proceso.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proceso.kill()

    total = len(resultados)
    fallos = [nombre for ok, nombre, _ in resultados if not ok]
    print("\n" + "=" * 62)
    print(f"RESULTADO: {total - len(fallos)}/{total} comprobaciones en verde")
    if fallos:
        print("Fallos:")
        for nombre in fallos:
            print(f"  - {nombre}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
