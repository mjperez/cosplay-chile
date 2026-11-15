# Cosplay Chile

Plataforma web de contenidos, directorio y comunidad para el cosplay chileno.
Proyecto de TI3043, Ingeniería de Software, INACAP. Un repositorio con dos
servicios: API FastAPI en `backend/` y cliente React + Tailwind en `frontend/`.

**Estado:** plataforma completa y funcional. Los seis módulos y el panel de
administración tienen pantalla, endpoints, reglas de negocio y datos de ejemplo.
**169 pruebas de backend en verde con 96% de cobertura**, lint del frontend con
**0 errores y 0 advertencias**, compilación de producción correcta y pipeline de
CI/CD activo en GitHub Actions + Render.

| Módulo | Qué ofrece |
|---|---|
| Directorio | 20 fichas reales con filtros por región, tipo y búsqueda |
| Contenidos | guías, entrevistas y artículos; editor de borradores, **subida de imágenes** y publicación |
| Eventos | calendario con filtros, detalle, inscripción con personaje y participantes |
| Foro | temas por categoría, búsqueda, respuestas y cierre por autor o administrador |
| Desafíos | desafío del mes vigente, historial y elección de ganador |
| Comunidad | dónde comprar, grupos regionales y perfil público de cosplayer |
| Avisos | notificaciones internas con contador de no leídas, generadas por el Observer |
| Administración | panel visual con métricas, bandeja editorial, eventos, foro, desafíos, cuentas, comunidad y **bitácora de auditoría** |

---

## Requisitos

- Python 3.13 (desarrollado y verificado también con 3.11)
- Node.js 22 y npm
- PostgreSQL 17 (Supabase en la nube) o SQLite para una demo local
- Git

## Puesta en marcha

```bash
git clone https://github.com/mjperez/cosplay-chile.git
cd cosplay-chile/backend

python -m venv .venv
source .venv/Scripts/activate      # Windows (Git Bash)
# source .venv/bin/activate       # Linux y macOS

pip install -r requirements-dev.txt
cp .env.example .env
# completar DATABASE_URL y JWT_SECRET
```

Generar el secreto de JWT:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Para una demo sin PostgreSQL, basta con poner en `.env`:

```
DATABASE_URL=sqlite+pysqlite:///./cosplay_demo.db
JWT_SECRET=una-clave-local-de-mas-de-16-caracteres
BCRYPT_ROUNDS=4
ENVIRONMENT=local
```

## Base de datos y datos semilla

```bash
alembic upgrade head
python -m app.seed.datos_base     # datos reales: 5 categorías + 20 fichas
python -m app.seed.demo           # datos de demostración (ver abajo)
```

`app.seed.datos_base` es el que corre en producción: carga las categorías del
editor y las fichas del directorio levantadas en la investigación. Es
idempotente, así que puede ejecutarse en cada arranque sin duplicar.

`app.seed.demo` crea cuentas, eventos, temas del foro, desafíos, tiendas,
grupos, un perfil y tres contenidos publicados. **Se niega a correr si
`ENVIRONMENT=production`** salvo que se fuerce con `DEMO_SEED=1`. También es
idempotente. Las cuentas que crea, todas con contraseña `Demo2026!`:

| Correo | Nombre visible | Rol | Para mostrar |
|---|---|---|---|
| `demo@cosplay.cl` | Usuario Administrador | administrador | entrar a `/admin`, publicar contenido, crear eventos y desafíos, elegir ganador |
| `cosplayer@cosplay.cl` | Usuario Cosplayer | cosplayer | inscribirse en eventos, responder el foro, editar su perfil |
| `organizador@cosplay.cl` | Usuario Organizador | organizador | otro participante con inscripciones previas |

Los nombres dicen el rol a propósito: al exponer la plataforma se ve de
inmediato con qué permisos se está entrando, sin recordar un nombre de persona
inventado. La semilla también **sincroniza el nombre de cuentas ya creadas**,
así que recargarla en una base anterior adopta las etiquetas nuevas sin
duplicar usuarios ni tocar contraseñas, roles o consentimientos.

> **Seguridad:** las cuentas demo son públicas y conocidas. Úsalas solo en un
> entorno de clase. En producción deja `DEMO_SEED` sin definir y cambia o borra
> esas cuentas si alguna vez se cargaron.

### Nota sobre el proveedor de base de datos

El informe de la asignatura describe el despliegue con **Neon**. La
implementación corre sobre **Supabase**, porque el proyecto de Neon se dio de
baja antes de la puesta en marcha. Ambos son PostgreSQL 17, el esquema no usa
extensiones específicas y la cadena se toma de `DATABASE_URL`: cambiar de
proveedor es cambiar una variable de entorno.

## Ejecutar

```bash
# terminal 1 (backend)
cd backend && uvicorn app.main:app --reload

# terminal 2 (frontend)
cd frontend && npm ci && npm run dev
```

Frontend en http://localhost:5173 y API en http://localhost:8000. El
`vite.config.ts` proxya `/api` y `/health`, así que en desarrollo no hace falta
configurar CORS ni `VITE_API_URL`.

| Ruta | Qué es |
|---|---|
| `GET /health` | estado del servicio y de la base |
| `GET /docs` | documentación interactiva (**49 rutas**) |
| `POST /api/v1/auth/registro` | crear cuenta |
| `POST /api/v1/auth/login` | obtener token |
| `GET /api/v1/auth/me` | datos del usuario del token |
| `GET /api/v1/privacidad` | versión vigente de la política |
| `GET /api/v1/admin/usuarios` | cuentas (solo administrador) |
| `GET /api/v1/admin/contenido` | bandeja editorial |
| `GET /api/v1/proveedores` | directorio con filtros y paginación |
| `GET /api/v1/proveedores/opciones` | regiones y tipos con fichas cargadas |
| `GET /api/v1/contenido` | contenido publicado |
| `GET /api/v1/contenido/{id}` | detalle de un contenido |
| `POST /api/v1/contenido` | crear borrador (requiere sesión) |
| `POST /api/v1/contenido/{id}/publicar` | publicar (solo administrador) |
| `GET /api/v1/eventos` | calendario con `tipo`, `region`, `q`, `limite`, `desplazamiento` |
| `GET /api/v1/eventos/mis` | eventos en los que estoy inscrito |
| `GET /api/v1/eventos/{id}` | detalle con total de participantes |
| `GET /api/v1/eventos/{id}/participaciones` | participantes y personaje |
| `POST /api/v1/eventos` | crear evento (solo administrador) |
| `POST /api/v1/eventos/{id}/participar` | inscribirse con personaje |
| `DELETE /api/v1/eventos/{id}/participar` | cancelar inscripción |
| `GET /api/v1/foro/temas` | temas con `categoria`, `q` y paginación |
| `GET /api/v1/foro/temas/{id}` | tema y sus respuestas |
| `POST /api/v1/foro/temas` | abrir tema (requiere sesión) |
| `POST /api/v1/foro/temas/{id}/respuestas` | responder (tema abierto) |
| `POST /api/v1/foro/temas/{id}/cerrar` | cerrar (autor o administrador) |
| `GET /api/v1/desafios` | historial de desafíos |
| `GET /api/v1/desafios/vigente` | desafío del mes en curso, o `null` |
| `POST /api/v1/desafios` | crear desafío (solo administrador) |
| `POST /api/v1/desafios/{id}/ganador` | elegir ganador (solo administrador) |
| `GET /api/v1/perfiles/mio` | mi perfil |
| `PUT /api/v1/perfiles/mio` | actualizar mi perfil |
| `GET /api/v1/perfiles/{id_usuario}` | perfil público |
| `GET /api/v1/tiendas` | dónde comprar, con filtros y paginación |
| `GET /api/v1/grupos` | grupos y comunidades, con filtros y paginación |
| `POST /api/v1/archivos` | subir imagen (PNG/JPEG/WebP, máx. 5 MB) |
| `DELETE /api/v1/archivos/{id}` | borrar imagen propia o como administrador |
| `GET /api/v1/notificaciones/sin-leer` | contador para el encabezado |
| `GET /api/v1/notificaciones` | bandeja de avisos del usuario |
| `PATCH /api/v1/notificaciones/{id}/leer` | marcar aviso como leído |

### Panel de administración

En `/admin`, visible solo para cuentas con rol `administrador`. El backend
vuelve a validar el rol en **cada** petición: la guarda de la interfaz es solo
comodidad. Todas las rutas cuelgan de `/api/v1/admin` y el router completo
lleva la dependencia `requiere_admin`, de modo que un endpoint nuevo nace
protegido.

| Ruta | Qué hace |
|---|---|
| `GET /api/v1/admin/resumen` | contadores de toda la plataforma |
| `GET /api/v1/admin/usuarios` | listado de cuentas |
| `PATCH /api/v1/admin/usuarios/{id}` | activar o desactivar una cuenta |
| `GET /api/v1/admin/contenido` | bandeja editorial con borradores |
| `POST /api/v1/admin/contenido/{id}/publicar` | publicar |
| `POST /api/v1/admin/contenido/{id}/rechazar` | rechazar un borrador |
| `POST /api/v1/admin/contenido/{id}/borrador` | devolver a borrador |
| `GET · POST /api/v1/admin/categorias` | categorías editoriales |
| `GET · POST /api/v1/admin/eventos` | calendario y alta de eventos |
| `DELETE /api/v1/admin/eventos/{id}` | eliminar un evento y sus inscripciones |
| `GET /api/v1/admin/foro/temas` | todos los temas, incluidos los ocultos |
| `PATCH /api/v1/admin/foro/temas/{id}` | abrir, cerrar u ocultar |
| `GET · POST /api/v1/admin/desafios` | historial y alta de desafíos |
| `POST /api/v1/admin/desafios/{id}/ganador` | elegir ganador |
| `POST /api/v1/admin/tiendas` | dar de alta una tienda |
| `POST /api/v1/admin/grupos` | dar de alta un grupo |
| `GET /api/v1/admin/auditoria` | bitácora de eventos de dominio y correos de moderación |

La pestaña **Auditoría** muestra fecha, categoría, evento, actor, recurso y
detalle de cada acción emitida por el Observer. Es de solo lectura y el router
completo exige rol `administrador`.

Las transiciones editoriales están acotadas: `pendiente → publicado | rechazado`,
`publicado → pendiente`, `rechazado → pendiente | publicado`. Un administrador
no puede desactivar su propia cuenta.

## Frontend

| Script | Qué hace |
|---|---|
| `npm run dev` | servidor de desarrollo con recarga en caliente |
| `npm run build` | compila TypeScript y genera `dist/` |
| `npm run lint` | oxlint |
| `npm run preview` | sirve `dist/` para probar la compilación |

**18 páginas**: `/`, `/directorio`, `/contenido`, `/contenido/nuevo`,
`/contenido/:id`, `/eventos`, `/eventos/:id`, `/foro`, `/foro/:id`,
`/desafios`, `/comunidad`, `/perfil`, `/notificaciones`, `/admin`,
`/ingresar`, `/registro`, `/privacidad` y 404. La navegación completa está en el
encabezado y en el pie. **Avisos** lleva un badge con el número de
notificaciones sin leer, que se consulta al iniciar sesión.

`VITE_API_URL` se normaliza en `src/lib/api.ts` y `src/lib/modulos.ts`: se le
quitan las barras finales antes de concatenar, para que un valor como
`https://api.ejemplo.com/` no produzca `//api/v1/...`.

## Pruebas

```bash
cd backend && pip install -r requirements-dev.txt && pytest
cd backend && pytest --cov=app --cov-fail-under=90
cd frontend && npm ci && npm run lint && npm run build
```

**169 pruebas** sobre SQLite en un directorio temporal, con el esquema aplicado
por `alembic upgrade head`, la misma migración de producción. No tocan la base
de desarrollo ni servicios externos. **Cobertura medida: 96%** (2550
sentencias, 100 sin cubrir); el umbral del pipeline es 90%.

| Ámbito | Pruebas | Archivo |
|---|---|---|
| Infraestructura, auth, autorización, seguridad | base histórica | `test_*.py` |
| Seis módulos y panel de administración | base histórica | `test_modulos_nuevos.py`, `test_panel_admin.py` |
| **Observer**: 3 observadores, 4 eventos, bitácora, 401/403 | 13 | `test_observer.py` |
| **Adapter**: interfaz, disco, Cloudinary, whitelist, HTTP, borrado | 18 | `test_adapter.py` |

`test_adapter.py::test_los_cuatro_patrones_del_informe_estan_implementados`
comprueba en una sola aserción por patrón que Singleton, Factory Method,
Observer y Adapter están presentes y son los descritos en el informe ES2.

Los defectos encontrados durante el desarrollo y sus correcciones están en
[`CORRECCIONES_ES3.md`](CORRECCIONES_ES3.md), con el formato
*hallazgo → corrección → evidencia* que pide el criterio 3.1.5. El recorrido
extremo a extremo se documenta en [`GUIA_DEMO.md`](GUIA_DEMO.md).

## Despliegue en Render

`render.yaml` define **dos servicios** con despliegue automático desde `main`:

| Servicio | Tipo | Publica |
|---|---|---|
| `cosplay-chile-api` | web (Python) | `backend/`, con `/health` como health check |
| `cosplay-chile-web` | static | `frontend/dist`, con rewrite `/* -> /index.html` para React Router |

El `startCommand` del backend aplica migraciones y ejecuta
`app.seed.datos_base` en cada arranque. Después corre `app.seed.demo` **por
defecto** (`DEMO_SEED=1`), de modo que un despliegue nuevo funciona sin
configurar nada en el panel. Si el servicio de Render ya existía, sincroniza el
blueprint o añade `DEMO_SEED=1` a mano y redespliega: Render no relee
`render.yaml` con un `git push`. Al terminar la demo, cambia `DEMO_SEED` a `0`,
redespliega y borra las cuentas de ejemplo: sus contraseñas son públicas.

Variables que se cargan a mano en el panel:

| Variable | Servicio | Valor |
|---|---|---|
| `DATABASE_URL` | API | cadena del pooler de Supabase, con `sslmode=require` |
| `JWT_SECRET` | API | la genera Render (`generateValue: true`) |
| `CORS_ORIGINS` | API | URL pública del frontend, sin barra final |
| `VITE_API_URL` | Web | URL pública del backend, sin barra final |
| `DEMO_SEED` | API | `1` por defecto para la demo; poner `0` después |
| `STORAGE_BACKEND` | API | `local` en la demo; `cloudinary` si se necesita persistencia |
| `STORAGE_DIRECTORIO` | API | `/tmp/cosplay-archivos` (disco efímero del plan free) |

`CORS_ORIGINS` y `VITE_API_URL` se necesitan entre sí: primero crea el backend
para obtener su URL, luego el frontend, y por último vuelve al backend a
poner la URL del frontend en `CORS_ORIGINS`. Si `CORS_ORIGINS` queda con el
valor por defecto (`http://localhost:5173`), el navegador bloquea las
peticiones en producción.

## Pipeline CI/CD y entornos

```
push / PR ──> GitHub Actions (.github/workflows/ci.yml)
                ├─ Backend: Python 3.11 y 3.13 · pytest --cov-fail-under=90
                ├─ Frontend: Node 22 · npm ci · lint · build
                └─ Puerta de calidad (falla si algo anterior falló)
                        │
                        v  merge a main
              Render autoDeploy (render.yaml)
                alembic upgrade head → datos_base → [demo] → uvicorn
                        │
                        v
              /health + smoke de login, avisos, auditoría e imágenes
```

`requirements.txt` es sólo de ejecución; `requirements-dev.txt` añade `pytest`,
`httpx` y `pytest-cov`. `pytest.ini` fija `pythonpath = .` y `testpaths = tests`.
`conftest.py` fija las variables de entorno **antes** de importar la aplicación,
así que el CI no necesita secretos: `DATABASE_URL` apunta a un SQLite temporal,
`JWT_SECRET` es de prueba y `BCRYPT_ROUNDS=4`.

| Entorno | `ENVIRONMENT` | Base | Archivos | Uso |
|---|---|---|---|---|
| Desarrollo | `local` | SQLite o Supabase de pruebas | adaptador local | `npm run dev` + `uvicorn --reload` |
| Testing | `test` | SQLite temporal por sesión | directorio temporal | pytest y GitHub Actions |
| Producción | `production` | Supabase PostgreSQL 17 | `local` en demo / `cloudinary` con credenciales | Render, `main` |

La semilla `demo` se niega a correr en `production` salvo `DEMO_SEED=1`, y las
credenciales de Cloudinary se leen del entorno: el `api_secret` se usa para
firmar la petición SHA-1 y **nunca** se envía en el cuerpo del multipart.

## Flujo de ramas

| Rama | Uso | Despliegue |
|---|---|---|
| `main` | código desplegable | automático en Render (ambos servicios) |
| `dev` | integración del sprint | manual |
| `despliegue` | trabajo de la entrega | CI en verde antes de mergear a `main` |

---

## Los cuatro patrones comprometidos en el informe ES2

La sección *"Patrones de diseño de la solución del problema"* del ES2 declaró
cuatro patrones. Al cierre de ES3 **los cuatro están implementados y probados**:
Singleton y Factory Method venían de la primera entrega; Observer y Adapter se
incorporaron en ES3 porque el informe los daba por diseñados pero el código no
los tenía. `test_los_cuatro_patrones_del_informe_estan_implementados` los
verifica juntos para que no vuelvan a desincronizarse documento y código.

| Patrón | Implementación | Papel | Prueba |
|---|---|---|---|
| **Singleton** (creacional) | `app/core/database.py` → `DatabaseSessionManager` | `__new__` con `threading.Lock`: un solo motor y un solo pool por proceso; `get_db()` inyecta la sesión | `test_singleton.py` |
| **Factory Method** (creacional) | `app/factories/contenido_factory.py` → `CreadorContenido` + `CreadorGuia` / `CreadorEntrevista` / `CreadorArticulo` + `ContenidoFactory.para()/crear()` | Crea el subtipo correcto sin que el servicio conozca clases concretas | `test_contenido.py` |
| **Observer** (comportamiento) | `app/events/gestor.py` + `app/events/observadores.py` | `GestorEventos` sujeto; `NotificacionInternaObserver`, `CorreoModeradorObserver`, `RegistroAuditoriaObserver` con `actualizar()`; catálogo cerrado de 4 eventos | `test_observer.py` (13) |
| **Adapter** (estructural) | `app/adapters/almacenamiento.py` | `IAlmacenamientoArchivos` con `guardar_archivo/eliminar_archivo/obtener_enlace`; adaptadores Local y Cloudinary; inversión de dependencias vía `get_almacenamiento()` | `test_adapter.py` (18) |

**Adaptación documentada del Observer.** El ES2 prometía avisos *"asíncronos en
segundo plano"*. La implementación con `BackgroundTasks` produjo
`database is locked` en SQLite porque la tarea abría una segunda conexión antes
de que cerrara `get_db`. Se cambió a **misma sesión, misma transacción** para
los tres observadores, y el único efecto diferido es el correo a moderación,
que queda encolado en la bitácora con `estado="pendiente_de_envio"`. Se
conserva la semántica (el usuario no espera por el correo) y se gana
atomicidad: si el `commit` falla, no quedan avisos de un tutorial inexistente.
El detalle completo está en [`CORRECCIONES_ES3.md`](CORRECCIONES_ES3.md).

## Tres servicios al usuario: entrada → proceso → resultado

Paso 3 de la Actividad 1. Cada servicio se presenta en la demo con su
formulario, su efecto en la interfaz y su registro en la bitácora.

### 1. Subir una imagen al editor de contenidos (RF-18 / RF-27)

| | |
|---|---|
| **Entrada** | `multipart/form-data` con un archivo PNG, JPEG o WebP de hasta 5 MB y el token JWT del autor |
| **Proceso** | `POST /api/v1/archivos` → autenticación → lista blanca de MIME + verificación de *magic bytes* (no confía en el `Content-Type`) + límite de tamaño → `nuevo_identificador()` genera `{uuid_dueño}/{uuid4}.ext` → `IAlmacenamientoArchivos.guardar_archivo()` → el endpoint compone la URL absoluta con `Request.base_url` |
| **Resultado** | `ArchivoPublico {identificador, enlace, tipo_mime, tamano}`; el enlace se adjunta en `imagenes[]` al guardar el borrador y se muestra como miniatura. Errores: 401, 415, 400, 413 |
| **Control** | OWASP A03 (validación de entrada), A01 (borrado autorizado por prefijo de dueño), defensa anti-`../` con `Path.is_relative_to()` |

### 2. Enviar un tutorial a revisión (RF-12 / RF-37)

| | |
|---|---|
| **Entrada** | Formulario del editor: `tipo`, `título`, `resumen`, `nivel`, `categoría`, `cuerpo`, `imágenes`, campos propios de guía/entrevista/artículo + token |
| **Proceso** | Unión discriminada de Pydantic por `tipo` → `ContenidoFactory.crear()` → persistencia del borrador → `GestorEventos.notificar(contenido_enviado_revision, sesion=...)` → los tres observadores escriben en la misma transacción |
| **Resultado** | Borrador en estado `pendiente`; aviso interno al autor y a los administradores; correo a `moderacion@cosplay.cl` encolado; fila en `bitacora_auditoria` con actor, recurso y detalle |
| **Control** | ISO/IEC 27002 A.8.15 (trazabilidad), Ley 19.223, atomicidad de la transacción |

### 3. Publicar un evento o desafío y avisar a la comunidad (RF-20 / RF-37)

| | |
|---|---|
| **Entrada** | Formulario del panel admin: título, tipo, fecha (convertida a UTC naive), lugar, región + token de administrador |
| **Proceso** | `Depends(requiere_admin)` → validación → persistencia → emisión de `evento_creado` / `desafio_creado` con `id_actor` → `NotificacionInternaObserver` avisa a **todos los usuarios activos menos el actor**, con deduplicación → `RegistroAuditoriaObserver` escribe el log |
| **Resultado** | Evento visible en `/eventos` (o desafío en `/desafios`), N avisos internos con badge en el encabezado y una fila nueva en la pestaña **Auditoría** |
| **Control** | ISO/IEC 27002 A.8.15 y A.8.3; minimización de datos de la Ley 21.719 |

## Cloud computing, ética y normativa

La solución se apoya en servicios administrados, sin servidores propios:

| Capa | Proveedor | Uso |
|---|---|---|
| **SaaS** | Supabase | PostgreSQL 17 como servicio (sin administrar motor ni respaldos) |
| **SaaS** | Cloudinary (opcional) | Almacenamiento y entrega de imágenes por CDN |
| **SaaS** | GitHub Actions | Integración continua y cobertura |
| **PaaS** | Render | API Python y sitio estático; migraciones y semillas en el `startCommand` |

No se usa **IaaS**: no hay máquinas virtuales ni red que administrar. El
*trade-off* es deliberado — menos control del sistema operativo a cambio de
despliegue reproducible desde `main` y coste cero en la demo — y su límite
conocido es el **disco efímero del plan free**, por eso el adaptador de
almacenamiento es intercambiable.

En lo ético se siguen los lineamientos de responsabilidad, no daño y respeto a
la privacidad del **Código de Ética ACM / IEEE-CS**: no se publican datos de
terceros sin consentimiento (el registro guarda fecha y versión del
consentimiento), el cuerpo HTML se sanitiza antes de mostrarse, ningún secreto
vive en el repositorio, la bitácora no guarda contraseñas ni tokens, y las
cuentas demo se declaran **inseguras a propósito** con instrucciones explícitas
para retirarlas después de la clase.

Normativa aplicada: **ISO/IEC 27002** (A.8.15 registro de eventos, A.5.15 y
A.8.3 control de acceso), **OWASP Top 10** A01/A02/A03, **Ley 19.223** de
delitos informáticos y **Ley 21.719** de protección de datos personales.

---

## Decisiones de implementación

**Arquitectura en capas.** `routes -> services -> repositories -> models`.
Cada módulo nuevo (eventos, foro, desafíos, perfiles, tiendas, grupos) tiene
su esquema Pydantic, su repositorio de consultas, su servicio de reglas y su
router. Ningún endpoint escribe SQL y ningún servicio conoce HTTP.

**Fechas en UTC naive.** `EventoEntrada` convierte cualquier datetime con zona
a UTC sin zona antes de guardarlo. SQLite no conserva el offset y PostgreSQL
interpreta un naive en la zona del servidor; guardar siempre UTC evita que la
misma hora se lea distinta en pruebas y producción. El frontend agrega `Z` a
esos valores y formatea en `America/Santiago`.

**Rutas literales antes que rutas con parámetro.** `/eventos/mis` se registra
antes de `/eventos/{id_evento}` y `/perfiles/mio` antes de
`/perfiles/{id_usuario}`; si se invirtiera, FastAPI intentaría parsear `mis`
como UUID y devolvería 422.

**Singleton con `__new__` y lock.** El gestor de sesiones se construye una sola
vez, con doble verificación para arranques concurrentes.

**Tipos portables.** `Uuid`, `JSON` y `Enum` sin tipo nativo compilan a
`UUID`/`JSON`/`VARCHAR` en PostgreSQL y a `CHAR(32)`/`JSON`/`VARCHAR` en
SQLite, lo que permite correr la migración completa en las pruebas.

**`/health` devuelve 503 si la base no responde.** Render usa esa ruta para
decidir si enruta tráfico; en producción el mensaje del driver se reemplaza
por uno genérico para no filtrar host ni usuario.

**Herencia de tabla unida para `Contenido`.** Una tabla base y una por subtipo
que comparte la clave primaria, con la creación a cargo de
`ContenidoFactory`.

**El bloqueo por intentos vive en la base**, no en memoria: sobrevive a
reinicios y es consistente entre workers. El intento fallido se confirma antes
de responder 401 para que el contador avance.

**El rol se lee de la base, no del token**, así revocar un permiso surte efecto
de inmediato.

**Semillas separadas por entorno.** `datos_base` son datos reales y corren
siempre; `demo` crea cuentas conocidas y se bloquea en producción. Ninguna
credencial vive en el repositorio.

**Errores de carga sin render en cascada.** Las páginas nuevas reinician su
estado de carga dentro de una microtarea, no de forma sincrónica en el
`useEffect`, y usan una bandera `vigente` para descartar respuestas tardías.

**FastAPI + React, y por qué.** FastAPI da validación declarativa con Pydantic
(la unión discriminada por `tipo` elimina `if` manuales), OpenAPI generado y
dependencias que permiten poner `requiere_admin` en un router completo. React +
TypeScript + Vite dan tipado del contrato en el cliente y un bundle estático
que Render sirve sin Node en producción. La alternativa era un monolito con
plantillas del servidor: menos piezas, pero habría obligado a reimplementar el
editor dinámico por tipo y el panel de administración con recargas completas.
El coste asumido es mantener dos despliegues y configurar CORS.

**Observer en la misma transacción.** Se descartó `BackgroundTasks` tras medir
`database is locked`. Alternativas evaluadas: una cola externa (Celery/Redis),
desproporcionada para la demo y con otro servicio que fallar; y un worker que
lea una bandeja de salida, que es justo lo que se dejó para el correo. La
solución elegida hace que avisos y auditoría sean **atómicos** con la operación
de negocio, a costa de que el `POST` incluya unas pocas inserciones más.

**Adapter local en demo, Cloudinary en producción.** El plan free de Render
tiene disco efímero: las imágenes subidas desaparecen en cada reinicio. En la
demo eso es aceptable y permite mostrar el flujo sin credenciales externas.
Cambiar a `STORAGE_BACKEND=cloudinary` no toca ningún servicio ni endpoint:
sólo la fábrica `obtener_almacenamiento()`. El `api_secret` se usa para firmar
SHA-1 y jamás viaja en el body del multipart.

**Migraciones aditivas.** `0005_observer_notificaciones_auditoria.py` sólo crea
dos tablas e índices, sin alterar columnas existentes. La bitácora **no** tiene
FK a `usuario` para que el historial sobreviva a la baja de una cuenta
(A.8.15); las notificaciones sí la tienen con `ON DELETE CASCADE` por
minimización de datos.

**Cobertura como contrato, no como meta decorativa.** El umbral del CI es 90%
frente al 96% real: deja margen para refactorizar sin que un cambio inocuo
rompa el pipeline, pero bloquea cualquier entrega que deje código nuevo sin
probar.

---

## Trazabilidad de criterios

### US-01 · Infraestructura

| Criterio | Dónde | Verificación |
|---|---|---|
| `GET /health` responde 200 con estado de la BD | `app/api/routes/health.py` | `tests/test_health.py` |
| `alembic upgrade head` sobre base vacía | `migrations/versions/0001_esquema_inicial.py` | `tests/test_migraciones.py` |
| Dos llamadas al gestor devuelven el mismo objeto | `app/core/database.py` | `tests/test_singleton.py` |
| Configuración desde variables de entorno | `app/core/config.py` | `tests/test_config.py` |
| Ramas `main` y `dev` con despliegue automático | `render.yaml` | panel de Render |

### US-04a · Registro, login, roles, hash y JWT

| Criterio | Dónde | Verificación |
|---|---|---|
| Contraseña con bcrypt; sin texto plano en la BD | `app/core/security.py` | `test_registro.py::test_la_contrasena_se_guarda_hasheada` |
| Credenciales inválidas dan 401 sin revelar si el correo existe | `app/api/routes/auth.py` | `test_login.py::test_correo_inexistente_responde_igual_que_contrasena_incorrecta` |
| Consentimiento con fecha y versión | `app/models/usuario.py` | `test_registro.py::test_el_consentimiento_queda_con_fecha_y_version` |
| Sesión persiste tras recargar; token vencido da 401 | `app/core/security.py` | `tests/test_autorizacion.py` |
| Rol sin permisos recibe 403 en administración | `app/api/deps.py` | `tests/test_autorizacion.py` |
| 5 intentos fallidos en 15 min bloquean el login | `app/services/auth.py` | `test_login.py::test_cinco_fallos_bloquean_el_login` |

### Módulos de comunidad

| Criterio | Dónde | Verificación |
|---|---|---|
| Calendario con filtros, detalle e inscripción única por usuario | `app/services/evento.py` | `tests/test_modulos_nuevos.py` |
| Foro con temas, respuestas y cierre por autor o administrador | `app/services/comunidad.py` | `tests/test_modulos_nuevos.py` |
| Desafío vigente por mes, sin duplicados | `app/services/comunidad.py` | `tests/test_modulos_nuevos.py` |
| Perfil público editable y catálogos de tiendas/grupos | `app/services/perfil.py` | `tests/test_modulos_nuevos.py` |
| Semillas idempotentes y bloqueadas en producción | `app/seed/demo.py` | `tests/test_semilla_demo.py` |

La matriz completa de casos por requerimiento está en
[`backend/tests/casos_por_rf.md`](backend/tests/casos_por_rf.md).

### ES3 · Prototipo funcional

| Criterio de la Unidad 3 | Dónde se evidencia |
|---|---|
| Repositorio Git y ramas con historial | `main`, `dev`, `despliegue`; respaldo `backup/pre-demo-admin` |
| Pipeline de CI/CD | `.github/workflows/ci.yml` + `autoDeploy` en `render.yaml` |
| Entornos desarrollo / testing / producción | `ENVIRONMENT=local\|test\|production`, tabla más arriba |
| Entradas, procesos y resultados en ≥3 servicios | sección «Tres servicios al usuario» |
| Cuatro patrones del informe ES2 | sección «Los cuatro patrones comprometidos» |
| Logs de auditoría y normativa | `bitacora_auditoria`, `GET /admin/auditoria`, `CORRECCIONES_ES3.md` |
| OWASP A01/A02/A03 | whitelist + magic bytes, secretos fuera del repo, control por dueño |
| SOLID / Clean Code / testing desde el inicio / code review | capas, `IAlmacenamientoArchivos`, 169 pruebas, PR #1 |
| Correcciones a partir de testing e ISO 27000 | `CORRECCIONES_ES3.md` (9 hallazgos) |
| Justificación de arquitectura, tecnologías y trade-offs | sección «Decisiones de implementación» |

---

## Limitaciones conocidas

- **El registro revela si un correo existe** (409). Es inevitable si se quiere
  dar un mensaje útil, y no permite probar contraseñas.
- **No hay refresh token.** Al vencer el token (60 min por defecto) hay que
  volver a iniciar sesión.
- **El bloqueo es por correo, no por IP.** Se mitiga con la ventana de 15 min.
- **El panel de administración no cambia roles ni contraseñas.** Se evitó a
  propósito: una escalada de privilegios por descuido es peor que tener que
  usar SQL para promover una cuenta. Tampoco hay edición de contenidos ya
  creados; el flujo es borrador → publicar/rechazar → volver a borrador.
- **Las imágenes de la demo no persisten entre reinicios.** El adaptador
  `local` escribe en `/tmp`, que el plan free de Render limpia. Para
  persistencia real basta configurar `STORAGE_BACKEND=cloudinary` y las tres
  credenciales en el panel; el código no cambia. El portafolio del perfil
  sigue siendo un enlace externo, no una galería propia.
- **El correo a moderación se encola, no se envía.** Queda en la bitácora con
  `estado="pendiente_de_envio"` a la espera de un worker de salida. La demo no
  necesita SMTP y evita depender de un servicio externo más.
- **Las cuentas demo son inseguras por diseño.** Solo para entornos de clase.
