# Guía de la demo

Todo lo necesario para mostrar el prototipo en clases, con el diseño integrado y la API real.

## Qué quedó verificado

| Verificación | Resultado |
|---|---|
| Pruebas de backend (`pytest` sobre PostgreSQL) | **96 en verde**, cobertura **97%** |
| Pruebas de interfaz (`npm test`) | **59 en verde** |
| Compilación (`npm run build`) | correcta, genera `dist/` |
| Recorrido HTTP real (`scripts/recorrido_http.py`) | **40/40 comprobaciones** |
| API documentada | **60 rutas** en `/docs` |
| Patrones del informe ES2 | Singleton, Factory Method, Observer y Adapter |
| Cuentas y contenido de ejemplo | se cargan con una sola orden |

## Arranque

### Con Docker (el más simple)

```bash
docker compose up --build
```

- Web: http://localhost:8080
- API: http://localhost:8000/docs
- PostgreSQL: `localhost:5433`, usuario y clave `cosplay`

### Sin Docker

```bash
# PostgreSQL local con rol cosplay y bases cosplay / cosplay_test
powershell -ExecutionPolicy Bypass -File scripts\dev.ps1
```

- API: http://localhost:8000/docs
- Web: http://localhost:5173

El seed es idempotente: si la base ya tiene usuarios, no vuelve a cargar. Para recargarlo: `python -m app.seed --reset` desde `backend/`.

## Cuentas

| Rol | Correo | Contraseña |
|---|---|---|
| Administrador/Moderador | `admin@cosplaychile.cl` | `Admin2026!` |
| Cosplayer | `camila@demo.cl` | `Cosplay2026!` |
| Cosmaker con ficha pública | `joaquin@demo.cl` | `Cosplay2026!` |
| Tienda | `tienda@demo.cl` | `Cosplay2026!` |
| Cuenta suspendida | `suspendido@demo.cl` | `Cosplay2026!` |

> Estas cuentas son inseguras por diseño y solo sirven para la demo. Después de clase: borrarlas o cambiar las claves y desactivar el seed.

> **Ojo con el login (OWASP A07):** tras **5 intentos fallidos consecutivos** la cuenta se bloquea **15 minutos**
> y la API responde `429` con «Demasiados intentos fallidos». Un inicio de sesión correcto reinicia el contador.
> Si vas a mostrar «clave incorrecta» en el guion, haz **un solo intento** y luego entra con la clave buena;
> no martillees 5 veces con `camila@demo.cl` o te quedarás sin cuenta para el paso 5. Los umbrales se ajustan
> con `LOGIN_MAX_INTENTOS` y `LOGIN_BLOQUEO_MINUTOS`.

## Guion de 12 minutos

1. **Portada (1 min).** Estadísticas reales, buscador con autocompletado («EVA»), filtros rápidos por región y categoría. Mostrar que las cifras vienen de `/api/inicio`.
2. **Directorio y mapa (1.5 min).** `/directorio` → tocar una región del mapa de Chile → ver ficha con precios, servicios y reseñas. «Ver mapa detallado» abre Leaflet.
3. **Guías (1 min).** `/guias` → filtrar por nivel → abrir una guía → compartir en redes. Destacar video embebido y descarga HTML.
4. **Identificarse (1 min).** Probar clave incorrecta → «Datos incorrectos». Probar `suspendido@demo.cl` → aviso de suspensión y enlace a contacto.
5. **Publicar tutorial (1.5 min).** Entrar como `camila@demo.cl` → `/guias/publicar` → enviar con una imagen. Ver el estado *Pendiente* en `/perfil` y el aviso en la campana 🔔.
6. **Moderación (2 min).** Entrar como `admin@cosplaychile.cl` → `/moderacion` → aprobar el tutorial (se avisa a toda la comunidad), resolver un reporte con «Ocultar y suspender», publicar el evento sugerido y abrir la **Bitácora**.
7. **Comunidad y desafíos (1.5 min).** `/comunidad` → responder un tema → ver el aviso al autor. `/desafios` → participar con foto y créditos.
8. **Perfil y seguridad (1 min).** `/perfil` → editar biografía y región → activar perfil público. `/seguridad` → consejos y formulario de contacto.
9. **Calidad (1.5 min).** Mostrar `/docs` (60 rutas), `.github/workflows/ci.yml` (99 pruebas, 97% cobertura, 59 pruebas de interfaz) y `CORRECCIONES_ES3.md` (13 hallazgos con evidencia, incluido el bloqueo OWASP A07).
10. **Cierre (30 s).** Mencionar los cuatro patrones del ES2 y el recorrido HTTP de 40/40.

## Endpoints útiles para la demo

| Acción | Ruta |
|---|---|
| Login | `POST /api/auth/login` con `{"email", "password"}` |
| Portada | `GET /api/inicio` |
| Búsqueda global | `GET /api/busqueda?q=EVA` y `/api/busqueda/sugerencias?q=EVA` |
| Mapa del directorio | `GET /api/directorio/mapa` |
| Enviar tutorial | `POST /api/contenidos` |
| Aprobar tutorial | `POST /api/moderacion/contenidos/{id}/publicar` |
| Sugerir evento | `POST /api/eventos/sugerir` |
| Reportar contenido | `POST /api/reportes` |
| Avisos | `GET /api/notificaciones`, `POST /api/notificaciones/leer-todas` |
| Auditoría (admin) | `GET /api/moderacion/auditoria` |
| Subir imagen | `POST /api/archivos` (multipart, campo `archivo`) |

## Render: **arreglado y verificado** (16-11-2026)

El deploy `dep-dbtio1utlv9c73acbbb0` quedó **`live`** con el stack integrado. Resultado real:

| Comprobación | Antes | Ahora |
|---|---|---|
| `GET /api/salud` | 404 | **200** `{"estado":"ok"}` |
| `GET /api/inicio` | 404 `Not Found` | **200** con estadísticas reales |
| Rutas en `/openapi.json` | 49 (backend viejo) | **60** |
| Personas registradas | `—` | **11** |
| Guías publicadas | `—` | **17** |
| Profesionales y tiendas | `—` | **23** |
| Eventos próximos | `—` | **12** |
| Login `admin@cosplaychile.cl` | — | **200** con JWT |
| CORS desde `cosplay-chile-web` | — | **`access-control-allow-origin` correcto** |

`bash scripts/verificar_render.sh` → **4 OK**. No hubo que redesplegar la web: su `VITE_API_URL` ya apuntaba bien.

> **Si el navegador sigue mostrando cifras vacías o imágenes viejas**: es caché del
> navegador (capa 8), no del servidor. Abrir en **ventana de incógnito** o añadir `?v=2`
> a la URL. Verificado con Chromium limpio: 11/17/23/12 y 0 imágenes rotas.
>
> **Imágenes**: las ilustraciones del seed se regeneran en cada arranque, así que
> sobreviven a los reinicios del plan free (detalle en `DIAGNOSTICO_RENDER.md`).

**Qué se corrigió** (detalle en [`DIAGNOSTICO_RENDER.md`](DIAGNOSTICO_RENDER.md)):

1. El servicio arrastraba el `startCommand` del stack anterior (`python -m app.seed.datos_base` / `app.seed.demo`) y `healthCheckPath: /health`; por eso el deploy anterior terminó en `update_failed`. Se cambió a `alembic upgrade head && python -m app.seed && uvicorn …` y `/api/salud`.
2. La `DATABASE_URL` apuntaba a un proyecto Supabase que **ya no existe** (`tenant/user not found`). Se sustituyó por el PostgreSQL del equipo en `postgresql+asyncpg://…:5432/postgres?ssl=require`, con las extensiones `unaccent` y `pg_trgm` precreadas en `public`.
3. Se añadieron `FRONTEND_URL`, `CORS_ORIGENES_EXTRA`, `JWT_EXPIRA_MINUTOS` y `MEDIA_DIR`, conservando el resto de variables.

La automatización completa está en `scripts/arreglar_render.py` (idempotente; usa `RENDER_API_KEY` y `DATABASE_URL`). **Después de clase**: rotar la API key de Render, la contraseña de Supabase y el token de GitHub; desactivar el seed y borrar las cuentas demo.

Como respaldo, la demo local sigue disponible con `docker compose up --build`.

## Ajuste de imágenes en móvil

En pantallas de hasta **640 px** el collage de la portada se reduce de `110vw` a `74vw` y las ilustraciones del seed se muestran completas (`object-fit: contain` con fondo del panel) en vez de recortadas. **Escritorio no cambia**: las reglas están confinadas a `@media (max-width: 640px)` al final de `frontend/src/index.css`.

Para verlo en Render sin caché del CDN, abrir en **incógnito** o añadir `?v=2` a la URL (el mismo truco de la sección anterior). Evidencia: `evidencia/portada_movil_ajuste_final.png`; detalle técnico en `CORRECCIONES_ES3.md` §12.

## Checklist antes de entrar a clase

- [ ] `docker compose up --build` levanta web y API sin errores.
- [ ] `http://localhost:8000/docs` muestra 60 rutas.
- [ ] Login de `admin@cosplaychile.cl` y de `camila@demo.cl` responde 200; `suspendido@demo.cl` responde 403.
- [ ] La campana de `camila@demo.cl` muestra avisos después de responder un tema.
- [ ] `/moderacion` abre con la cuenta admin y muestra la bitácora.
- [ ] En Render, abrir las URLs con 5 minutos de anticipación por el arranque en frío del plan free.

## Rollback

El prototipo integrado usa **PostgreSQL y un esquema propio** (`alembic/versions/0001`), distinto del SQLite con migraciones `0001…0005` de la entrega anterior. Por eso:

1. Para volver al código anterior, hacer `git revert` del commit de integración y redesplegar.
2. **No reutilizar la misma base**: restaurar el respaldo de la base anterior o crear una instancia nueva. Apuntar el código nuevo a la base vieja (o al revés) fallará porque las tablas`usuario`, `contenido` y `notificacion` tienen columnas distintas.
3. Si solo quieres ocultar la demo, basta con desactivar el seed y borrar las cuentas listadas arriba; no hace falta revertir código.

Evita `reset --hard` + push forzado si alguien más usa el repositorio: reescribe el historial compartido.
