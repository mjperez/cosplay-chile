# Cosplay Chile

Plataforma web de contenidos, directorio y comunidad para el cosplay chileno.
Proyecto de TI3043, Ingeniería de Software, INACAP. Un repositorio con dos
servicios: API FastAPI en `backend/` y cliente React + Tailwind en `frontend/`.

**Estado:** plataforma completa y funcional. Los seis módulos y el panel de
administración tienen pantalla, endpoints, reglas de negocio y datos de ejemplo.
**136 pruebas de backend en verde**, lint del frontend con **0 errores y 0
advertencias**, compilación de producción correcta y recorrido extremo a extremo
verificado sobre el esquema real de migraciones (26/26 comprobaciones).

| Módulo | Qué ofrece |
|---|---|
| Directorio | 20 fichas reales con filtros por región, tipo y búsqueda |
| Contenidos | guías, entrevistas y artículos; editor de borradores y publicación |
| Eventos | calendario con filtros, detalle, inscripción con personaje y participantes |
| Foro | temas por categoría, búsqueda, respuestas y cierre por autor o administrador |
| Desafíos | desafío del mes vigente, historial y elección de ganador |
| Comunidad | dónde comprar, grupos regionales y perfil público de cosplayer |
| Administración | panel visual con métricas, bandeja editorial, eventos, foro, desafíos, cuentas y comunidad |

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

| Correo | Rol | Para mostrar |
|---|---|---|
| `demo@cosplay.cl` | administrador | entrar a `/admin`, publicar contenido, crear eventos y desafíos, elegir ganador |
| `cosplayer@cosplay.cl` | cosplayer | inscribirse en eventos, responder el foro, editar su perfil |
| `organizador@cosplay.cl` | organizador | otro participante con inscripciones previas |

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
| `GET /docs` | documentación interactiva (43 rutas) |
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

Páginas: `/`, `/directorio`, `/contenido`, `/contenido/nuevo`,
`/contenido/:id`, `/eventos`, `/eventos/:id`, `/foro`, `/foro/:id`,
`/desafios`, `/comunidad`, `/perfil`, `/ingresar`, `/registro`,
`/privacidad` y 404. La navegación completa está en el encabezado y en el pie.

`VITE_API_URL` se normaliza en `src/lib/api.ts` y `src/lib/modulos.ts`: se le
quitan las barras finales antes de concatenar, para que un valor como
`https://api.ejemplo.com/` no produzca `//api/v1/...`.

## Pruebas

```bash
cd backend && pytest
```

136 pruebas sobre SQLite en un directorio temporal, con el esquema aplicado por
la misma migración de producción. No tocan la base de desarrollo ni servicios
externos. Cubren infraestructura, autenticación, autorización, directorio,
contenido, los seis módulos nuevos, el panel de administración y las semillas
(incluida su idempotencia).

El recorrido extremo a extremo adicional se documenta en
[`GUIA_DEMO.md`](GUIA_DEMO.md): migración, semillas, arranque y peticiones
reales de login, inscripción, foro y perfil.

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

`CORS_ORIGINS` y `VITE_API_URL` se necesitan entre sí: primero crea el backend
para obtener su URL, luego el frontend, y por último vuelve al backend a
poner la URL del frontend en `CORS_ORIGINS`. Si `CORS_ORIGINS` queda con el
valor por defecto (`http://localhost:5173`), el navegador bloquea las
peticiones en producción.

## Flujo de ramas

| Rama | Uso | Despliegue |
|---|---|---|
| `main` | código desplegable | automático en Render (ambos servicios) |
| `dev` | integración del sprint | manual |

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
- **Sin carga de imágenes.** Los contenidos usan texto y HTML saneado; el
  portafolio del perfil es un enlace externo.
- **Las cuentas demo son inseguras por diseño.** Solo para entornos de clase.
