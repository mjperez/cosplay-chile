# Correcciones del prototipo (criterio 3.1.5)

Este documento registra los hallazgos aparecidos al ejecutar el prototipo integrado y las correcciones aplicadas. Sigue el formato **hallazgo → corrección → evidencia**. El prototipo toma como base el diseño y el backend del ZIP recibido, y añade la capa de calidad de la entrega anterior (CI, cobertura, trazabilidad y recorridos reales).

**Estado final:** 96 pruebas de backend en verde, **97% de cobertura**, 59 pruebas de interfaz en verde y compilación de producción correcta.

---

## 1. Las pruebas de interfaz no arrancaban con Node 22.13

**Hallazgo.** `npm test` terminaba con 8 errores antes de ejecutar ninguna prueba:

```text
TypeError: Cannot read properties of undefined (reading 'bind')
  node_modules/undici/lib/interceptor/decompress.js:78
```

**Diagnóstico.** `jsdom@31` instala `undici@8.12.4`, cuyo `engines` exige `node >= 22.19.0`. El entorno disponible era Node 22.13.1, por lo que `createZstdDecompress` no existía y fallaba el arranque de los workers de Vitest.

**Corrección.** Se fijó una versión compatible mediante `overrides` en `frontend/package.json` y se regeneró `package-lock.json`:

```json
"overrides": { "undici": "^7.16.0" }
```

**Evidencia.** `npm ci && npm test` → **8 archivos, 59 pruebas en verde**. El build sigue correcto (`npm run build`).

---

## 2. La cobertura medía mal el código asíncrono

**Hallazgo.** Con la configuración inicial, el servicio de contenidos marcaba como *no ejecutadas* las líneas posteriores a `await` de `publicar_tutorial`, aunque la petición `POST /api/contenidos` devolvía 201. Lo mismo ocurría en `auth_service`, `moderacion_service` y `contenido_service`: la cobertura global era **83–85%** y no reflejaba lo que realmente se ejecutaba.

**Diagnóstico.** El trazador C de coverage 7.17 pierde la continuación de las corrutinas cuando el event loop las reanuda. Se comprobó con una inyección temporal de `RuntimeError` dentro de `publicar_tutorial`: la excepción se lanzaba, pero coverage seguía marcando esa línea como no cubierta.

**Corrección.** Se activó el núcleo `sysmon` (disponible desde Python 3.12) en `backend/pyproject.toml`:

```toml
[tool.coverage.run]
core = "sysmon"
```

**Evidencia.** La misma suite pasó de **85% a 97%** (2895 sentencias, 98 sin cubrir) y el número de líneas ejecutadas en `publicar_tutorial` pasó de `[23,24,25,26]` a `[23,24,25,26,31,32,34,39]`. Es un hallazgo de *medición*, no de código: sin corregirlo el umbral del pipeline habría rechazado un prototipo correcto.

---

## 3. El prototipo recibido no tenía pipeline de calidad

**Hallazgo.** El ZIP incluía 84 pruebas de backend y 59 de interfaz, pero **no tenía `.github/workflows`**, no medía cobertura y no declaraba dependencias de test reproducibles más allá de `pytest`/`httpx`.

**Corrección.** Se portó el pipeline de la entrega anterior y se adaptó al stack async/PostgreSQL:

- servicio `postgres:16` con `unaccent` y `pg_trgm` (creados por la migración 0001),
- matriz Python 3.12 y 3.13,
- `pytest --cov=app --cov-fail-under=90`,
- `npm ci && npm test && npm run build`,
- `requirements-dev.txt` con `pytest-cov>=6.0`,
- puerta de calidad que bloquea el despliegue si falla algo.

**Evidencia.** El comando exacto del pipeline pasa en local: `96 passed`, `Required test coverage of 90% reached. Total coverage: 96.61%`. El YAML se validó con `yaml.safe_load`.

---

## 4. El entrypoint del seed cerraba el Singleton compartido

**Hallazgo.** Al probar `python -m app.seed` desde pytest, `DatabaseSessionManager.close()` dejaba `_sessionmaker = None` y las fixtures siguientes fallaban con `RuntimeError: DatabaseSessionManager no inicializado`.

**Corrección.** En la prueba se sustituye `close` por una versión inofensiva con `monkeypatch`, porque el Singleton debe sobrevivir a lo largo de toda la sesión de pruebas. El comportamiento de producción no se cambió.

**Evidencia.** `test_entrypoint_semilla_carga_todo_desde_cero` ejecuta el entrypoint dos veces y comprueba que no duplica cuentas. Las 96 pruebas posteriores siguen encontrando el pool inicializado.

---

## 5. La campana de avisos dependía de quién fuera el autor del tema

**Hallazgo.** Un primer intento comprobaba las notificaciones respondiendo un tema del seed; el aviso llegaba a la cuenta demo autora, no a la cuenta autenticada de la prueba, y la aserción `no_leidas >= 1` fallaba.

**Corrección.** La prueba crea el tema con la cuenta autenticada y responde con una segunda cuenta. Así se verifica de verdad el `NotificacionInternaObserver`.

**Evidencia.** `test_avisos_internos_se_marcan_como_leidos` comprueba bandeja, `POST /leer`, `POST /leer-todas`, `no_leidas == 0` y 401 sin sesión.

---

## 6. La supresión de cuenta no revela el estado de la cuenta

**Hallazgo.** Después de `DELETE /api/perfil`, iniciar sesión con el correo anterior devuelve **401**, no 403. La primera versión de la prueba esperaba 403.

**Corrección.** Se ajustó la expectativa a 401 y se documentó el motivo: la cuenta se anonimiza, no se elimina físicamente, y responder «cuenta eliminada» permitiría enumerar correos registrados.

**Evidencia.** `test_perfil_actualizar_publico_y_suprimir_cuenta`. Conducta coherente con OWASP A01 (control de acceso) y con el derecho a supresión de la Ley 21.719.

---

## 7. Dependencias de desarrollo incompletas

**Hallazgo.** `requirements-dev.txt` no incluía `pytest-cov`, así que el comando del pipeline no era reproducible desde un entorno limpio.

**Corrección.** Se añadió `pytest-cov>=6.0` y se conservaron `package-lock.json` y `pyproject.toml` como fuentes de verdad de las versiones.

**Evidencia.** Instalación limpia con `uv pip install -r requirements-dev.txt` y ejecución del comando completo del CI.

---

## 8. Faltaba trazabilidad RF ↔ prueba en el prototipo recibido

**Hallazgo.** El ZIP traía `docs/TRAZABILIDAD.md` (37 RF implementados, 3 parciales) pero no una matriz que vinculara cada requerimiento con una prueba ejecutable, requisito del criterio 3.1.5.

**Corrección.** Se incorporó `backend/tests/casos_por_rf.md` con las 96 pruebas, su archivo, el requerimiento cubierto y el resultado observado, más la procedencia de las 12 pruebas nuevas.

**Evidencia.** La matriz está alineada con `docs/TRAZABILIDAD.md` y con `docs/BRECHAS_DISENO.md` (el documento del diseño que explica qué se adaptó y qué quedó como texto editorial).

---

## 9. Brechas heredadas del diseño que se conservan documentadas

**Hallazgo.** El diseño muestra elementos que la API no entrega: minutos de lectura, precios por servicio, avatar, reporte anónimo, región en el formulario de contacto y FAQ autoadministrable. El frontend del ZIP ya los había resuelto sin inventar datos.

**Corrección.** No se modificó el diseño: se conservaron `design/Cosplay Chile — Frontend.html`, los componentes de `frontend/src/components/diseno/`, las ilustraciones y `docs/BRECHAS_DISENO.md`, que lista cada brecha con su estado (Adaptado / Omitido / Placeholder / Estático).

**Evidencia.** 59 pruebas de interfaz recorren todas las pantallas y comprueban que los datos mostrados vienen de la API.

---

## 10. Las ilustraciones del seed desaparecían tras un reinicio en Render

**Hallazgo.** En el prototipo desplegado, las tarjetas de guías, directorio, eventos y comunidad mostraban imágenes rotas: `GET /media/seed/evento.svg` devolvía **404** `{"detail":"Not Found"}`. Se detectó con Chromium en viewport móvil (390×844) recorriendo la página completa.

**Diagnóstico.** `backend/app/seed/__main__.py` llamaba a `generar_todas(settings.media_path)` **después** de la comprobación de idempotencia: si la base ya tenía usuarios, `main()` hacía `return` y no escribía los SVG. Como el plan free de Render tiene disco efímero (`MEDIA_DIR=/tmp/cosplay-media`), cada reinicio de la instancia perdía los archivos sin que el seed los regenerara. No era un defecto exclusivo de móvil: allí se percibía más porque esas ilustraciones se cargan con `loading="lazy"` al hacer scroll.

**Corrección.** Se movió la generación de ilustraciones **antes de cualquier salida temprana** en `app/seed/__main__.py`, y se añadió al `startCommand` de Render una llamada explícita a `generar_todas(get_settings().media_path)` antes de `alembic upgrade head && python -m app.seed`. La generación es idempotente (sobrescribe los 12 SVG) y no toca la base de datos.

**Evidencia.** Deploy `dep-dbtjcoifngtc73cquvdg` → `live`. Los **12 SVG referenciados por la API** responden **200 `image/svg+xml`**. Chromium móvil con scroll completo: **0 imágenes rotas** (antes 3 en la portada y 33 en cinco páginas). `scripts/verificar_render.sh` sigue en **4 OK**. Capturas en `evidencia/`.

---

## 11. El despliegue en Render conservaba la configuración del stack anterior

**Hallazgo.** Tras integrar el ZIP, la portada mostraba «Not Found» y las cuatro cifras quedaban en `—`; `/openapi.json` seguía con 49 rutas.

**Diagnóstico.** Dos causas encadenadas: (a) el servicio `cosplay-chile-api` mantenía el `startCommand` del stack viejo (`python -m app.seed.datos_base` / `app.seed.demo`) y `healthCheckPath: /health`, por lo que el deploy terminaba en `update_failed` y Render seguía sirviendo la versión anterior; (b) su `DATABASE_URL` apuntaba a un proyecto Supabase ya eliminado (`tenant/user not found`).

**Corrección.** Se actualizó el servicio por API: `startCommand` con migración, seed y uvicorn, `healthCheckPath: /api/salud`, y variables `DATABASE_URL` (`postgresql+asyncpg://…:5432/postgres?ssl=require`), `FRONTEND_URL`, `CORS_ORIGENES_EXTRA`, `JWT_EXPIRA_MINUTOS` y `MEDIA_DIR`, conservando las 11 variables existentes. Se precrearon `unaccent` y `pg_trgm` en `public` y se desplegó con caché limpia. La automatización idempotente quedó en `scripts/arreglar_render.py`.

**Evidencia.** Deploy `dep-dbtio1utlv9c73acbbb0` → `live`; `/api/salud` 200, `/api/inicio` 200 con 11/17/23/12, **60 rutas**, login 200 y CORS correcto. Ver `DIAGNOSTICO_RENDER.md`.

---

## 12. Ajuste mínimo de imágenes en móvil (≤ 640px)

**Hallazgo.** En 390×844 las fotos del collage de la portada sufrían un recorte lateral excesivo y las ilustraciones del seed (SVG apaisados de **240×150**) aparecían cortadas dentro de tarjetas verticales. No eran imágenes rotas: respondían 200, pero `object-cover` sobre contenedores de proporción fija descartaba la mayor parte de la escena. Era un problema de presentación heredado del diseño, no del despliegue.

**Alcance.** Se autorizó un ajuste **mínimo y exclusivo de móvil**. El diseño de escritorio queda intacto: las tres reglas viven dentro de `@media (max-width: 640px)` al final de `frontend/src/index.css`.

**Corrección.**

| Selector | Antes | Después |
|---|---|---|
| `div[aria-hidden='true']:has(> img + img)` | `height: min(560px, 110vw)` | `min(560px, 74vw) !important` |
| `div[aria-hidden='true']:has(> img + img) > img` | `object-position: 50% 50%` | `50% 30% !important` |
| `img[src*='/media/seed/']` | `object-fit: cover` | `contain !important` + fondo `#160c34` |

En 390 px el collage pasa de ~217×429 (ratio 0,51) a **~217×289** (ratio 0,75). El comentario `ajuste-movil-es3` sirve de marcador para que el build sea idempotente.

**Despliegue.** En un primer momento no había credenciales de Git para llevar el cambio a `main`, y Render construye desde el repositorio. Se actualizó el `buildCommand` de `cosplay-chile-web` por la API de Render para que añada el bloque (codificado en base64, sólo si el marcador no existe) antes de `npm ci && npm run build`, y se disparó un deploy con caché limpia. Detalle del contrato de la API en `DIAGNOSTICO_RENDER.md` §7.

**Cierre (16-11, más tarde).** Ya se pudo pushear a `main`: el bloque móvil quedó versionado en `frontend/src/index.css`, el `buildCommand` volvió a `npm ci && npm run build` y el parche temporal se retiró. El marcador `ajuste-movil-es3` se conserva igualmente porque hace idempotente cualquier rebuild.

**Evidencia.** Deploy `dep-dbtjk0u1egvs73b4vmsg` → `live`. Se sirve `index-B7RbawAk.css` (75.429 bytes) e `index-BiZJm7rM.js`, idénticos al build local; `npm test` → **59/59**. Chromium 390×844 con scroll completo: collage **350×289**, 3/3 SVG con `object-fit: contain`, **0 imágenes rotas**, 0 errores JS, cifras 11/17/23/12. Control en 1440×900: collage **560 px**, `object-position: 50% 50%`, SVG con `cover` → **escritorio sin cambios**. Captura en `evidencia/portada_movil_ajuste_final.png`.

**Nota de consistencia.** `scripts/arreglar_render.py` y `render.yaml` conservan el prefijo de regeneración de SVG en `startCommand`, de modo que re-ejecutar el script de rescate ya no pisa la corrección de la §10.

---

## 13. Bloqueo temporal por intentos fallidos de login (OWASP A07)

**Hallazgo.** La «Guía de verificación de seguridad OWASP» pide deshabilitar la cuenta tras un número
establecido de intentos inválidos (ejemplo: cinco). Verificado en vivo contra Render: 8 intentos con clave
errónea devolvían `[401, 401, 401, 401, 401, 401, 401, 401]` — sin `429` ni bloqueo. Era la única brecha
relevante de A01–A03/A07 en el prototipo.

**Corrección.** Se añadieron dos columnas a `usuario` (`intentos_fallidos`, `bloqueado_hasta`) mediante la
migración `0002_rate_limiting_login.py`, y `auth_service.autenticar` ahora:

| Situación | Respuesta |
|---|---|
| Cuenta con `bloqueado_hasta` vigente | `429` + `CUENTA_BLOQUEADA` (sin procesar la clave) |
| Intento fallido | `401` genérico y contador +1 (solo si el correo existe) |
| Contador llega a `login_max_intentos` (5) | `bloqueado_hasta = ahora + login_bloqueo_minutos` (15) |
| Login exitoso | contador a 0 y `bloqueado_hasta = None` |
| Correo no registrado | siempre `401`, sin contador (no enumera cuentas) |

Ambos umbrales son variables de entorno (`LOGIN_MAX_INTENTOS`, `LOGIN_BLOQUEO_MINUTOS`), no constantes en
el código. El router persiste el contador con `commit()` **incluso cuando `autenticar` lanza la excepción**
(`try/except HTTPException`), porque `get_db` no hace commit automático. El cliente ya mostraba los objetos
`detail` con `mensaje`/`codigo` (`ApiError`), así que el `429` se pinta como alerta en español sin tocar la UI.

**Evidencia.** `tests/test_auth.py`: 3 pruebas nuevas (bloqueo tras 5, reinicio tras login exitoso, correo
inexistente nunca se bloquea). Suite completa **99 pruebas en verde, 97% de cobertura** con Python 3.12 +
`sysmon` (umbral de CI: 90%). Migración aplicada en el despliegue con `alembic upgrade head`; es aditiva y
no destruye datos (`server_default='0'`, columna nullable).

---

## Marco normativo aplicado

| Norma / estándar | Aplicación en el prototipo |
|---|---|
| **ISO/IEC 27002 A.8.15** | `RegistroAuditoria` escrito por el `RegistroAuditoriaObserver` ante cada evento de dominio; consultable por administración en `/api/moderacion/auditoria` |
| **ISO/IEC 27002 A.8.3** | Control de acceso por rol (`RequiereAdmin`, `UsuarioActual`), borrado de favoritos y archivos solo por su dueño |
| **OWASP A01** | Rutas protegidas, 401 genérico, redirección `siguiente` limitada a rutas internas, supresión sin enumeración de cuentas |
| **OWASP A02** | JWT con secreto por entorno, contraseñas argon2id, tokens de recuperación guardados como hash, secretos fuera del repositorio |
| **OWASP A03** | Validación Pydantic, URLs restringidas a http(s), tipo de imagen por firma binaria, escape en la descarga HTML, parámetros SQL ORM |
| **OWASP A07** | Bloqueo temporal tras 5 intentos fallidos de login, contador por cuenta, umbrales por entorno (§13) |
| **Ley 19.223** de delitos informáticos | Bitácora de auditoría y trazabilidad de acciones de moderación |
| **Ley 21.719** de protección de datos | Consentimiento explícito con fecha, finalidad informada, opt-in al directorio y derecho a supresión |

---

## Pipeline que sostiene estas correcciones

```bash
# Backend (PostgreSQL local o servicio del CI)
cd backend
python -m pytest -q --cov=app --cov-fail-under=90   # 99 pruebas, 97% de cobertura

# Frontend
cd frontend
npm ci && npm test && npm run build
```

Ambos comandos son los que ejecuta `.github/workflows/ci.yml` en cada push.
