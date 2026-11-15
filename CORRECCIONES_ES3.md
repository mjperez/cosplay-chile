# Evidencia de correcciones a partir de testing e ISO/IEC 27000 — ES3

Documento de apoyo al **criterio 3.1.5** de la rúbrica del prototipo funcional
(35%): *correcciones del código a partir de pruebas de testing e ISO 27000*.
Registra defectos encontrados **mientras se construía** el prototipo, la
decisión técnica que los resolvió y la prueba que demuestra que no reaparecen.

No es un informe de la Unidad 4: es la bitácora de calidad del código que se
presenta junto al prototipo en la Actividad 1, pasos 1 a 3.

| # | Hallazgo | Origen | Corrección | Prueba que lo fija |
|---|---|---|---|---|
| 1 | La semilla demo no renombraba cuentas ya existentes | Prueba de regresión sobre BD previa | Sincronizar el nombre por rol sin tocar clave, rol ni consentimientos | `test_semilla_demo.py` |
| 2 | `nivel: "principiante"` producía 422 en el editor | Prueba nueva del Observer | Alinear el fixture con el contrato `basico \| intermedio \| avanzado` | `test_observer.py::test_enviar_un_tutorial_dispara_los_tres_observadores` |
| 3 | `BackgroundTasks` bloqueaba SQLite (`database is locked`) | Prueba de integración del Observer | Misma sesión y misma transacción para los observadores | `test_observer.py` (13 pruebas) |
| 4 | `FormData` se enviaba con `Content-Type: application/json` | Prueba de subida por HTTP | No forzar la cabecera cuando el cuerpo es `FormData` | `test_adapter.py::test_subir_una_imagen_por_http_y_servirla` |
| 5 | El `DELETE /archivos/{id}` permitía `../` | Revisión OWASP A01 / A03 | `Path.is_relative_to()` sobre el directorio raíz | `test_adapter.py::test_el_adaptador_rechaza_salir_del_directorio` |
| 6 | El enlace devuelto era relativo y `imagenes` exige `HttpUrl` | Prueba de contrato con `ContenidoEntrada` | Convertir a URL absoluta con `Request.base_url` en el endpoint | `test_adapter.py::test_subir_una_imagen_por_http_y_servirla` |
| 7 | Un observador caído podía tumbar el `POST` completo | Diseño del patrón Observer | Aislar excepciones por observador con `logging.exception` | `test_observer.py::test_un_observador_caido_no_impide_a_los_demas` |
| 8 | La bitácora se perdía al borrar la cuenta del actor | ISO 27002 A.8.15 / Ley 19.223 | Sin FK a `usuario`; se guarda `correo_actor` como texto | `test_observer.py::test_la_bitacora_no_tiene_clave_foranea_hacia_usuario` |
| 9 | Un Content-Type falso permitía subir un SVG como PNG | OWASP A03 (validación de entrada) | Lista blanca + verificación de *magic bytes* | `test_adapter.py::test_el_servicio_no_confia_en_el_content_type_declarado` |

**Resultado de la última corrida:** 169 pruebas en verde, cobertura **96%**
(2550 sentencias, 100 sin cubrir), lint del frontend con 0 errores y 0
advertencias, compilación de producción correcta. El umbral del pipeline es
`--cov-fail-under=90`, por debajo de la cobertura real para dejar margen a
cambios futuros sin que el CI se vuelva frágil.

---

## 1. Semilla demo y cuentas existentes

**Hallazgo.** `app.seed.demo` creaba las tres cuentas de demostración con
`Usuario Administrador`, `Usuario Cosplayer` y `Usuario Organizador`, pero si la
base ya tenía esos correos de una corrida anterior conservaba el nombre
anterior. En la presentación no se distinguía el rol de un vistazo.

**Corrección.** La semilla pasó a ser idempotente en dos niveles: sigue sin
duplicar filas y además **sincroniza el nombre visible** de las cuentas
existentes. No modifica la contraseña, el rol, el estado activo ni los
consentimientos, para no alterar datos que un alumno pudo haber cambiado.

**Evidencia.** `backend/tests/test_semilla_demo.py` y el commit `1e17741`.
`GUIA_DEMO.md` incorporó la verificación del nombre por rol en el checklist
(`3c76c06`) porque el defecto se detectó al preparar la demo, no al leer el
código.

---

## 2. Contrato de `nivel` y el error 422

**Hallazgo.** El primer fixture del Observer creaba un tutorial con
`{"nivel": "principiante"}`. El endpoint respondía **422 Unprocessable
Entity**: `ContenidoBase.nivel` es un `Literal["basico", "intermedio",
"avanzado"]`. La prueba fallaba antes siquiera de ejercitar el patrón.

**Corrección.** Se alineó el fixture con el contrato publicado en
`app/schemas/contenido.py` y con el `<select>` del editor, que ya ofrecía esos
tres valores. No se relajó el schema: el 422 es el comportamiento correcto y
es una defensa de entrada, no un bug.

**Evidencia.** `test_enviar_un_tutorial_dispara_los_tres_observadores` y
`test_crear_desafio_dispara_notificacion_y_bitacora` crean contenido con
`nivel="basico"`. Lección registrada: los datos de prueba deben construirse
contra el mismo contrato que el cliente real.

---

## 3. De `BackgroundTasks` a una sola transacción (adaptación documentada del ES2)

**Hallazgo.** El informe ES2 comprometió que los avisos del Observer se
emitieran *"de forma asíncrona en segundo plano"*. La primera implementación
usó `fastapi.BackgroundTasks`. Al ejecutar las pruebas de integración apareció:

```text
sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) database is locked
[SQL: INSERT INTO bitacora_auditoria ...]
```

Causa diagnosticada: `BackgroundTasks` se ejecuta **antes** de que se cierre la
dependencia `get_db`. La tarea abría una segunda conexión mientras la primera
mantenía la transacción abierta; en SQLite eso bloquea, y en PostgreSQL habría
producido lecturas sucias o notificaciones huérfanas si el `commit` posterior
fallaba.

**Corrección.** Los tres observadores reciben la **misma `Session`** y escriben
en la **misma transacción** que el caso de uso. `GestorEventos.notificar()` ya
no depende de `BackgroundTasks`; las rutas y servicios quedaron sin los
parámetros `publicador` / `en_segundo_plano`. El helper `_con_sesion()` abre
sesión propia sólo cuando se invoca a un observador sin sesión (scripts,
workers, pruebas unitarias). El único efecto realmente diferido es el **correo
a moderación**, que se encola en `bitacora_auditoria` con
`categoria="correo_moderacion"` y `estado="pendiente_de_envio"`, a la espera de
un worker de salida.

Esta es una **adaptación deliberada y justificada** del ES2, no un incumplimiento
silenciado: se conserva la semántica (el usuario no espera por el correo), los
avisos internos y el log quedan atómicos con la operación de negocio, y se evita
que un `commit` fallido deje notificaciones de un tutorial que nunca existió.

**Evidencia.** `backend/app/events/gestor.py`, `backend/app/events/observadores.py`,
las 13 pruebas de `test_observer.py` y el endpoint `GET /api/v1/admin/auditoria`
que permite verificar en vivo la bandeja de salida.

---

## 4. `FormData` y la cabecera forzada

**Hallazgo.** `peticionModulo` añadía `Content-Type: application/json` a toda
petición con cuerpo. Al subir una imagen con `FormData`, el navegador no podía
insertar el *boundary* del multipart y el servidor rechazaba el archivo.

**Corrección.** La cabecera sólo se fija cuando el cuerpo **no** es
`FormData`:

```ts
!(opciones.body instanceof FormData) &&
!cabeceras.has('Content-Type')
```

**Evidencia.** `frontend/src/lib/modulos.ts` y el cliente
`frontend/src/lib/archivos.ts`; la prueba HTTP
`test_subir_una_imagen_por_http_y_servirla` confirma el ciclo completo de subida
y posterior `GET` del enlace.

---

## 5. Path traversal en el adaptador local

**Hallazgo.** `DELETE /api/v1/archivos/{identificador:path}` recibe el
identificador desde la URL, controlada por el cliente. Un valor como
`../../app/.env` habría permitido resolver rutas fuera del directorio de
almacenamiento. Es el escenario clásico de **OWASP A01 (control de acceso
roto)** combinado con **A03 (validación de entrada)**.

**Corrección.** `AlmacenamientoLocalAdapter._ruta()` resuelve la ruta y exige
`ruta.is_relative_to(self._directorio)`; si no, lanza `ValueError`, que el
endpoint traduce a **400**. Además el `DELETE` autoriza por el prefijo del
identificador (`{uuid_del_dueño}/...`) o por rol `administrador`: un archivo
ajeno da **403**, no 404 ni 204.

**Evidencia.** `test_el_adaptador_rechaza_salir_del_directorio`,
`test_la_api_rechaza_entradas_peligrosas` y
`test_no_se_puede_borrar_un_archivo_de_otra_cuenta`.

---

## 6. Enlace relativo frente a `HttpUrl`

**Hallazgo.** El adaptador local devuelve `/archivos/{id}`, pero
`ContenidoEntrada.imagenes` es `list[HttpUrl]`. Guardar un borrador con ese
enlace devolvía 422: la URL relativa no tiene esquema ni host.

**Corrección.** El endpoint `POST /api/v1/archivos` inyecta `Request` y convierte
el enlace a absoluto con `peticion.base_url`. El adaptador sigue siendo puro y
devolviendo rutas relativas (útil en pruebas y detrás de un proxy); la
composición con el host ocurre en la capa HTTP, que es quien lo conoce.

**Evidencia.** `backend/app/api/routes/archivos.py` y la aserción
`datos["enlace"].startswith("http")` en
`test_subir_una_imagen_por_http_y_servirla`.

---

## 7. Aislamiento de fallos entre observadores

**Hallazgo.** Si el envío de correo o la escritura del log lanzaba una
excepción, el `POST` original devolvía 500 aunque el tutorial sí se hubiera
guardado. Un canal de notificación caído no debe tumbar el caso de uso.

**Corrección.** `GestorEventos.notificar()` envuelve cada `actualizar()` en su
propio `try/except` y registra `logging.exception` con el nombre del
observador. Los demás canales continúan.

**Evidencia.** `test_un_observador_caido_no_impide_a_los_demas` sustituye un
observador por un doble que lanza y comprueba que los otros dos siguen
produciendo efectos.

---

## 8. Bitácora sin dependencia de la cuenta del actor

**Hallazgo.** Una FK de `bitacora_auditoria` hacia `usuario` con `ON DELETE
CASCADE` habría borrado el historial al dar de baja una cuenta. Eso contradice
el control **A.8.15 (registro de eventos / logging)** de ISO/IEC 27002 y la
exigencia de trazabilidad de la **Ley 19.223** de delitos informáticos: el
registro debe sobrevivir al actor.

**Corrección.** La migración `0005` crea `bitacora_auditoria` **sin FK a
usuario**, con `correo_actor` como texto inmutable, `id_actor` como UUID
informativo, `tipo_evento`, `id_recurso`, `detalle` (JSON) y `ocurrido_en`.
`notificacion` sí mantiene FK con `ON DELETE CASCADE`, porque un aviso personal
debe desaparecer con su dueño (minimización de datos, **Ley 21.719**).

**Evidencia.** `test_la_bitacora_no_tiene_clave_foranea_hacia_usuario` inspecciona
las claves foráneas reales de la tabla; `test_la_bitacora_registra_actor_recurso_y_detalle`
comprueba el contenido; `GET /api/v1/admin/auditoria` está protegido por
`Depends(requiere_admin)` y `test_la_bitacora_solo_la_lee_un_administrador`
verifica 401 sin token y 403 con rol `cosplayer`.

---

## 9. Validación real del contenido de las imágenes

**Hallazgo.** Confiar en el `Content-Type` declarado por el cliente permite
subir un SVG con payload de script diciendo `image/png`. Es **OWASP A03**.

**Corrección.** `app/services/archivos.py` aplica una **lista blanca**
(`image/png`, `image/jpeg`, `image/webp`), verifica los *magic bytes* reales,
rechaza archivos vacíos y limita el tamaño a 5 MB. El nombre original se
descarta: el identificador es `{uuid_dueño}/{uuid4}.{extension}`, generado por
`nuevo_identificador()`. El `POST` traduce cada error de dominio a 415, 400 o
413.

**Evidencia.** `test_el_servicio_acepta_solo_los_tres_formatos_de_la_lista_blanca`,
`test_el_servicio_rechaza_un_tipo_fuera_de_la_lista`,
`test_el_servicio_no_confia_en_el_content_type_declarado`,
`test_el_servicio_rechaza_vacios_y_demasiado_grandes` y
`test_sin_token_no_se_puede_subir`.

---

## Marco normativo aplicado

| Norma / control | Dónde se materializa |
|---|---|
| **ISO/IEC 27002 A.8.15** (logging) | `RegistroAuditoriaObserver`, tabla `bitacora_auditoria`, endpoint admin de solo lectura |
| **ISO/IEC 27002 A.8.12** (prevención de fuga de datos) | El log no expone contraseñas ni tokens; guarda correo y UUID |
| **ISO/IEC 27002 A.5.15 / A.8.3** (control de acceso) | Prefijo por dueño en el borrado de archivos; `requiere_admin` en el router completo |
| **OWASP A01** | Autorización por dueño en `DELETE /archivos`, 404 en lugar de 403 para no revelar UUID ajenos, defensa anti-`../` |
| **OWASP A02** | Secretos sólo en variables de entorno; el `api_secret` de Cloudinary se usa para firmar y **nunca** se envía en el body |
| **OWASP A03** | Whitelist de MIME + magic bytes, límite de tamaño, `Literal` en `nivel`, `HttpUrl` en `imagenes`, sanitización del cuerpo HTML |
| **Ley 19.223** (delitos informáticos) | Trazabilidad de accesos y acciones relevantes con actor, recurso y fecha |
| **Ley 21.719** (protección de datos personales) | Minimización: la notificación se borra con la cuenta; el log conserva sólo el correo del actor, no el perfil completo |

## Pipeline que sostiene estas correcciones

`.github/workflows/ci.yml` ejecuta, en cada push y en cada PR:

1. **Backend** en Python 3.11 y 3.13: `pip install -r requirements-dev.txt` y
   `pytest --cov=app --cov-fail-under=90`. El esquema lo crea
   `alembic upgrade head` en `conftest.py`, el mismo comando de producción.
2. **Frontend** en Node 22: `npm ci`, `npm run lint`, `npm run build`.
3. **Puerta de calidad** que falla si cualquiera de los dos anteriores falla.

La CD la completa `render.yaml` con `autoDeploy: true` sobre `main`: migraciones,
semillas idempotentes y `uvicorn`. Si el CI está en rojo no se mergea a `main`,
por lo que producción no cambia.

Entornos: `ENVIRONMENT=local` (desarrollo, SQLite y adaptador de disco),
`ENVIRONMENT=test` (CI y pytest) y `ENVIRONMENT=production` (Render, Supabase,
`DEMO_SEED` apagado tras la clase, `STORAGE_BACKEND=cloudinary` si se requiere
persistencia).
