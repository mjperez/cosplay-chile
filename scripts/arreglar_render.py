#!/usr/bin/env python3
"""Arregla el despliegue de Cosplay Chile en Render, de punta a punta.

Hace, en orden:
  1. Localiza el servicio `cosplay-chile-api` por nombre.
  2. Lee TODAS sus variables actuales (el PUT de Render reemplaza, no fusiona).
  3. Escribe las variables del stack nuevo conservando las demás.
  4. Dispara un deploy con caché limpia y espera a que quede `live`.
  5. Verifica /api/salud, /api/inicio y el número de rutas; imprime las 4 cifras.

Uso:
    export RENDER_API_KEY='rnd_...'
    export DATABASE_URL='postgresql+asyncpg://...'
    python3 scripts/arreglar_render.py

    # sin tocar nada, solo diagnosticar:
    python3 scripts/arreglar_render.py --solo-verificar
    # ver qué cambiaría, sin aplicar:
    python3 scripts/arreglar_render.py --dry-run
    # leer credenciales de un archivo KEY=VALUE:
    python3 scripts/arreglar_render.py --env-file /ruta/a/render.env

Los secretos nunca se imprimen ni se escriben en el repositorio.

Este script solo configura `cosplay-chile-api`. El sitio estático
`cosplay-chile-web` (buildCommand / publishPath) se administra por separado.
"""
from __future__ import annotations

import argparse
import json
import os
import secrets
import sys
import time
from pathlib import Path

import requests

API = "https://api.render.com/v1"
WEB = "https://cosplay-chile-web.onrender.com"
NOMBRE_SERVICIO = "cosplay-chile-api"

VARIABLES_NUEVAS = {
    "FRONTEND_URL": WEB,
    "CORS_ORIGENES_EXTRA": WEB,
    "PYTHON_VERSION": "3.13.14",
    "JWT_EXPIRA_MINUTOS": "60",
    "STORAGE_BACKEND": "local",
    "MEDIA_DIR": "/tmp/cosplay-media",
}

# El prefijo regenera los 12 SVG del seed ANTES de migrar: con MEDIA_DIR en
# disco efímero, un reinicio borra /media/seed/*.svg y el seed idempotente ya
# no los volvía a escribir (CORRECCIONES_ES3.md §10).
START_COMMAND = (
    'python -c "from app.core.config import get_settings; from app.seed.imagenes import generar_todas; '
    'generar_todas(get_settings().media_path)" && '
    "alembic upgrade head && python -m app.seed && "
    "uvicorn app.main:app --host 0.0.0.0 --port $PORT"
)

ESTADOS_FINALES = {"live", "build_failed", "update_failed", "canceled", "deactivated"}


def enmascarar(valor: str) -> str:
    if not valor:
        return "(vacío)"
    if len(valor) <= 8:
        return "***"
    return f"{valor[:3]}…{valor[-4:]} ({len(valor)} chars)"


def cargar_env_file(ruta: str) -> None:
    for linea in Path(ruta).read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if not linea or linea.startswith("#") or "=" not in linea:
            continue
        k, v = linea.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip("'\""))


class Render:
    def __init__(self, key: str) -> None:
        self.s = requests.Session()
        self.s.headers.update({
            "Authorization": f"Bearer {key}",
            "accept": "application/json",
            "content-type": "application/json",
        })

    def call(self, method: str, path: str, body=None, params=None, timeout=30):
        r = self.s.request(method, API + path, json=body, params=params, timeout=timeout)
        if r.status_code == 401:
            raise SystemExit("API key inválida o sin permisos (401). Revisa RENDER_API_KEY.")
        if r.status_code == 429:
            raise SystemExit("Render devolvió 429 (rate limit). Espera un minuto y reintenta.")
        if not r.ok:
            raise SystemExit(f"{method} {path} → {r.status_code}: {r.text[:400]}")
        return r.json() if r.text.strip() else None

    def servicio(self, nombre: str) -> dict:
        datos = self.call("GET", "/services", params={"name": nombre, "limit": 20, "includePreviews": "false"})
        for fila in datos or []:
            srv = fila.get("service", {})
            if srv.get("name") == nombre:
                return srv
        raise SystemExit(f"No encontré el servicio '{nombre}' en la cuenta. ¿La API key es del workspace correcto?")

    def actualizar_servicio(self, sid: str) -> None:
        """Corrige startCommand y healthCheckPath: el servicio arrastraba los del stack viejo.

        El prefijo que regenera los SVG es obligatorio mientras MEDIA_DIR viva
        en disco efímero; quitarlo devuelve los 404 de /media/seed/*.svg.
        """
        self.call("PATCH", f"/services/{sid}", body={"serviceDetails": {
            "healthCheckPath": "/api/salud",
            "envSpecificDetails": {
                "buildCommand": "pip install -r requirements.txt",
                "startCommand": START_COMMAND,
            },
        }})

    def env_vars(self, sid: str) -> list[dict]:
        datos = self.call("GET", f"/services/{sid}/env-vars", params={"limit": 100})
        return datos or []

    def escribir_env(self, sid: str, lista: list[dict]) -> None:
        self.call("PUT", f"/services/{sid}/env-vars", body=lista)

    def deploy(self, sid: str) -> str:
        d = self.call("POST", f"/services/{sid}/deploys",
                      body={"clearCache": "clear", "deployMode": "build_and_deploy"})
        return d["id"]

    def estado(self, sid: str, did: str) -> str:
        return self.call("GET", f"/services/{sid}/deploys/{did}").get("status", "?")

    def logs(self, sid: str, inicio: str) -> list[str]:
        try:
            d = self.call("GET", "/logs", params={
                "resource": sid, "startTime": inicio, "limit": 100, "direction": "forward",
            })
        except SystemExit:
            return []
        lineas = []
        for fila in d or []:
            txt = fila.get("message") or fila.get("text") or ""
            if txt:
                lineas.append(str(txt))
        return lineas


def validar_url(url: str) -> None:
    if not url.startswith("postgresql+asyncpg://"):
        raise SystemExit("DATABASE_URL debe empezar con postgresql+asyncpg://  (no postgresql:// ni sqlite).")
    if "sqlite" in url.lower():
        raise SystemExit("DATABASE_URL sigue apuntando a SQLite. El backend nuevo necesita PostgreSQL.")
    if "localhost" in url or "127.0.0.1" in url:
        raise SystemExit("Esa URL es local: Render no puede alcanzarla. Usa la URL pública de Supabase/Neon/Render.")
    if ":6543" in url and "prepared_statement_cache_size" not in url:
        print("  AVISO: puerto 6543 (transaction pooler) suele romper asyncpg.")
        print("         Mejor usa el session pooler en 5432, o añade &prepared_statement_cache_size=0")


def verificar() -> bool:
    print("\n=== Verificación en vivo ===")
    ok = True
    try:
        r = requests.get("https://cosplay-chile-api.onrender.com/api/salud", timeout=30)
        print(f"  /api/salud      → {r.status_code} {r.text[:60]}")
        ok &= r.status_code == 200
    except Exception as e:
        print(f"  /api/salud      → error: {e}")
        ok = False
    try:
        r = requests.get("https://cosplay-chile-api.onrender.com/api/inicio", timeout=30)
        if r.status_code == 200 and "estadisticas" in r.text:
            e = r.json()["estadisticas"]
            print("  /api/inicio     → 200 con datos reales:")
            print(f"       Personas registradas : {e.get('personas')}")
            print(f"       Guías publicadas     : {e.get('guias')}")
            print(f"       Profesionales+tiendas: {(e.get('proveedores') or 0) + (e.get('tiendas') or 0)}")
            print(f"       Eventos próximos     : {e.get('eventos_proximos')}")
        else:
            print(f"  /api/inicio     → {r.status_code} {r.text[:100]}")
            ok = False
    except Exception as e:
        print(f"  /api/inicio     → error: {e}")
        ok = False
    try:
        r = requests.get("https://cosplay-chile-api.onrender.com/openapi.json", timeout=30)
        n = len(r.json().get("paths", {}))
        print(f"  /openapi.json   → {n} rutas (esperado ~60, viejo = 49)")
        ok &= n >= 55
    except Exception as e:
        print(f"  /openapi.json   → error: {e}")
        ok = False
    try:
        r = requests.get(WEB + "/", timeout=30)
        print(f"  web             → {r.status_code}")
        ok &= r.status_code == 200
    except Exception as e:
        print(f"  web             → error: {e}")
        ok = False
    print("\n  RESULTADO:", "TODO OK — recarga la web con Ctrl+F5" if ok else "AÚN FALTA ALGO — revisa los logs del deploy")
    return ok


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--env-file", help="archivo con RENDER_API_KEY=... y DATABASE_URL=...")
    ap.add_argument("--dry-run", action="store_true", help="muestra el plan sin aplicar cambios")
    ap.add_argument("--solo-verificar", action="store_true", help="no toca Render, solo sondea la API pública")
    ap.add_argument("--espera", type=int, default=900, help="segundos máximos de espera del deploy")
    args = ap.parse_args()

    if args.env_file:
        cargar_env_file(args.env_file)
    if args.solo_verificar:
        return 0 if verificar() else 1

    key = os.environ.get("RENDER_API_KEY", "").strip()
    url = os.environ.get("DATABASE_URL", "").strip()
    if not key:
        raise SystemExit("Falta RENDER_API_KEY.")
    if not url:
        raise SystemExit("Falta DATABASE_URL (PostgreSQL vacío, formato postgresql+asyncpg://…).")
    validar_url(url)

    print(f"API key      : {enmascarar(key)}")
    print(f"DATABASE_URL : {enmascarar(url)}")
    print(f"Servicio     : {NOMBRE_SERVICIO}\n")

    r = Render(key)
    srv = r.servicio(NOMBRE_SERVICIO)
    sid = srv["id"]
    print(f"Servicio encontrado: id={sid}  branch={srv.get('branch')}  rootDir={srv.get('rootDir')}")
    print(f"Dashboard: {srv.get('dashboardUrl', 'https://dashboard.render.com')}")

    print("0/5 Corrigiendo startCommand y healthCheckPath…")
    if not args.dry_run:
        r.actualizar_servicio(sid)
    print("    OK (startCommand → regenerar SVG + alembic + seed + uvicorn; health → /api/salud)")

    actuales = r.env_vars(sid)
    mapa: dict[str, str] = {}
    generadas: list[str] = []
    for fila in actuales:
        ev = fila.get("envVar", {}) if isinstance(fila, dict) else {}
        k = ev.get("key")
        if not k:
            continue
        if "value" in ev and ev["value"] is not None:
            mapa[k] = str(ev["value"])
        else:
            generadas.append(k)

    print(f"Variables actuales: {len(mapa)} con valor, {len(generadas)} generadas por Render")
    print("  " + ", ".join(sorted(mapa)) or "  (ninguna)")

    cambios = dict(VARIABLES_NUEVAS)
    cambios["DATABASE_URL"] = url
    if "JWT_SECRET" not in mapa:
        cambios["JWT_SECRET"] = secrets.token_urlsafe(48)
        print("  + JWT_SECRET generado (no existía)")

    print("\nCambios a aplicar:")
    for k, v in cambios.items():
        antes = mapa.get(k)
        estado = "sin cambio" if antes == v else ("nueva" if antes is None else "reemplaza")
        muestra = enmascarar(v) if k in ("DATABASE_URL", "JWT_SECRET") else v
        print(f"  {k:24} {estado:12} → {muestra}")

    mapa.update(cambios)
    lista = [{"key": k, "value": v} for k, v in sorted(mapa.items())]
    # Las que Render generaba y no tenían valor explícito se preservan como generadas.
    for k in generadas:
        if k not in mapa:
            lista.append({"key": k, "generateValue": True})

    if args.dry_run:
        print(f"\nDry-run: se enviarían {len(lista)} variables y se dispararía un deploy. No se tocó nada.")
        return 0

    print(f"\n1/5 Escribiendo {len(lista)} variables (PUT reemplaza, se conservaron las demás)…")
    r.escribir_env(sid, lista)
    print("    OK")

    print("2/5 Disparando deploy con caché limpia…")
    inicio = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    did = r.deploy(sid)
    print(f"    deploy id = {did}")

    print(f"3/5 Esperando hasta {args.espera}s (plan free: arranque en frío lento)…")
    estado, muerto = "?", time.time() + args.espera
    while time.time() < muerto:
        estado = r.estado(sid, did)
        print(f"    {time.strftime('%H:%M:%S')} → {estado}", flush=True)
        if estado in ESTADOS_FINALES:
            break
        time.sleep(15)
    if estado != "live":
        print(f"\n    El deploy terminó en '{estado}'. Últimas líneas del log:")
        for linea in r.logs(sid, inicio)[-25:]:
            print("      " + linea[:200])
        print("\n    Lee el PRIMER error del log en el dashboard de Render.")
        return 1
    print("    Deploy live ✅")

    print("4/5 Buscando el seed en los logs…")
    for linea in r.logs(sid, inicio):
        if "Seed" in linea or "alembic" in linea.lower() or "Uvicorn" in linea:
            print("      " + linea[:200])

    return 0 if verificar() else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nInterrumpido.")
        sys.exit(130)
