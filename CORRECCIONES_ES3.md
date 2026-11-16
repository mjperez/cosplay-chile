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

## Marco normativo aplicado

| Norma / estándar | Aplicación en el prototipo |
|---|---|
| **ISO/IEC 27002 A.8.15** | `RegistroAuditoria` escrito por el `RegistroAuditoriaObserver` ante cada evento de dominio; consultable por administración en `/api/moderacion/auditoria` |
| **ISO/IEC 27002 A.8.3** | Control de acceso por rol (`RequiereAdmin`, `UsuarioActual`), borrado de favoritos y archivos solo por su dueño |
| **OWASP A01** | Rutas protegidas, 401 genérico, redirección `siguiente` limitada a rutas internas, supresión sin enumeración de cuentas |
| **OWASP A02** | JWT con secreto por entorno, contraseñas argon2id, tokens de recuperación guardados como hash, secretos fuera del repositorio |
| **OWASP A03** | Validación Pydantic, URLs restringidas a http(s), tipo de imagen por firma binaria, escape en la descarga HTML, parámetros SQL ORM |
| **Ley 19.223** de delitos informáticos | Bitácora de auditoría y trazabilidad de acciones de moderación |
| **Ley 21.719** de protección de datos | Consentimiento explícito con fecha, finalidad informada, opt-in al directorio y derecho a supresión |

---

## Pipeline que sostiene estas correcciones

```bash
# Backend (PostgreSQL local o servicio del CI)
cd backend
python -m pytest -q --cov=app --cov-fail-under=90

# Frontend
cd frontend
npm ci && npm test && npm run build
```

Ambos comandos son los que ejecuta `.github/workflows/ci.yml` en cada push.
