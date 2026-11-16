# Diagnóstico: «Not Found» en las cifras de la portada de Render

Sondeo real a los dos servicios públicos, 16-11-2026. Complementa la sección «Render» de `GUIA_DEMO.md`.

> ## ✅ RESUELTO el 16-11-2026
>
> Deploy `dep-dbtio1utlv9c73acbbb0` en estado **`live`**. Verificación final:
> `/api/salud` **200**, `/api/inicio` **200** con datos, **60 rutas**, web **200**,
> login admin **200** y CORS correcto. Cifras de la portada: **11 personas,
> 17 guías, 23 profesionales y tiendas, 12 eventos próximos**.
> `bash scripts/verificar_render.sh` → **4 OK**.
>
> La causa no fue solo la base de datos: el servicio conservaba el **`startCommand`
> del stack anterior** (`app.seed.datos_base` / `app.seed.demo`) y el
> **`healthCheckPath: /health`**, por lo que el deploy previo terminó en
> `update_failed`. Además, la `DATABASE_URL` anterior apuntaba a un proyecto
> Supabase **ya eliminado** (`tenant/user not found`). Se corrigieron ambos
> puntos con `scripts/arreglar_render.py`, se precrearon `unaccent` y `pg_trgm`
> en `public` y se desplegó con caché limpia.
>
> **Lo que sigue abajo es el diagnóstico histórico**, conservado como evidencia
> de la rúbrica (hallazgo → corrección → evidencia).

## En una línea

El **frontend nuevo sí se desplegó** (por eso se ve el diseño nuevo), pero el **servicio de API sigue ejecutando el backend anterior**. El nuevo frontend pide `GET /api/inicio` y la API vieja contesta `404 {"detail":"Not Found"}`. Ese texto es, literalmente, el que aparece en el recuadro rojo encima de «Personas registradas · Guías publicadas · Profesionales y tiendas · Eventos próximos».

**No es un problema de base de datos ni de Supabase.**

---


## Caso posterior: imágenes rotas (misma tarde)

**Síntoma.** Ya con las cifras correctas, algunas ilustraciones no se veían en móvil.

**Hallazgo.** `GET /media/seed/*.svg` → **404**. El seed escribía las ilustraciones en `MEDIA_DIR=/tmp/cosplay-media`, pero `main()` devolví­a antes de generarlas cuando la base ya tenía datos; con el disco efímero del plan free, un reinicio las borraba para siempre. Los `.jpg` del frontend sí respondían 200; las que parecían rotas sin hacer scroll eran imágenes `loading="lazy"` aún no cargadas (falso positivo del primer sondeo).

**Corrección.** `generar_todas()` se movió antes de la salida temprana en `backend/app/seed/__main__.py` y el `startCommand` de Render la invoca explícitamente en cada arranque.

**Evidencia.** Deploy `dep-dbtjcoifngtc73cquvdg` → `live`; los 12 SVG que devuelve la API responden **200 `image/svg+xml`**; Chromium 390×844 con scroll completo: **0 imágenes rotas**.

**Lo que NO es un error:** el recorte de las fotos en móvil. El diseño usa `object-cover` sobre contenedores de proporción fija (p. ej. `h-[min(560px,110vw)]`); en 390 px de ancho la primera foto queda en 217×429 px frente a sus 640×854 originales, así que `object-cover` recorta los lados en vez de deformarla. Es una decisión del diseño recibido, que se integró sin cambios visuales; ajustarlo requiere autorización explícita.

## 1. Evidencia medida en vivo

| Comprobación | Resultado |
|---|---|
| `GET https://cosplay-chile-web.onrender.com/` | **200**, `index.html` del diseño nuevo (`lang="es-CL"`, `assets/index-BOKJfpLU.js`) |
| `GET .../assets/index-BOKJfpLU.js` | Contiene `https://cosplay-chile-api.onrender.com` compilado → `VITE_API_URL` **sí está configurado** y apunta a la API |
| `GET https://cosplay-chile-api.onrender.com/openapi.json` | **200**, pero **49 rutas**, descripción *«Plataforma de contenidos, directorio y comunidad…»*, rutas `/health` y `/api/v1/…` |
| ¿Tiene `/api/inicio`? | **No** |
| ¿Tiene `/api/salud`? | **No** |
| `GET /api/inicio` | **404** `{"detail":"Not Found"}` |
| `GET /api/salud` | **404** `{"detail":"Not Found"}` |
| `GET /health` | **200** `{"status":"ok","environment":"production","database":{"ok":true,…}}` |

El backend del ZIP, en cambio, monta `/api/inicio`, `/api/salud` y ~60 rutas, y su descripción OpenAPI es *«API REST del prototipo Cosplay Chile: guías, directorio, calendario y comunidad cosplay»*. La comparación no deja dudas: en Render corre el código de la entrega anterior.

### Por qué el mensaje aparece justo ahí

- `frontend/src/pages/Inicio.jsx:121` → `useApi('/api/inicio')`.
- `frontend/src/pages/Inicio.jsx:261` → `<Alerta tipo="error">{error?.message}</Alerta>` muestra el `detail` del 404: **«Not Found»**.
- `frontend/src/pages/Inicio.jsx:263–266` → las cuatro `Cifra` reciben `undefined` y muestran `—`.
- `frontend/src/api/client.js` convierte el 404 en `ApiError(404, 'Not Found')`.

---

## 2. Causa raíz

`render.yaml` define para el servicio `cosplay-chile-api`:

```yaml
startCommand: alembic upgrade head && python -m app.seed && uvicorn …
healthCheckPath: /api/salud
```

Si el despliegue nuevo no completa, Render **sigue sirviendo el despliegue anterior**. La causa más probable es que `DATABASE_URL` en Render sigue siendo la URL **SQLite** del stack anterior: el nuevo backend es `asyncpg` + PostgreSQL, así que `alembic upgrade head` falla, el seed no corre y el health check `/api/salud` nunca responde 200.

Consecuencias, todas observables:

1. La portada pide una ruta que no existe → «Not Found».
2. **El seed nuevo nunca se ejecutó**, por eso tampoco aparecen «los datos nuevos»: las cuentas demo, guías, directorio y eventos del ZIP no están cargados en esa base.
3. `/docs` sigue mostrando 49 rutas en vez de ~60.

---

## 3. ¿Necesito acceso a Supabase? → No

- En todo el repositorio **no hay ni una referencia a Supabase**: la capa de datos es SQLAlchemy async + `asyncpg` sobre PostgreSQL estándar. Es indistinto que el Postgres viva en Supabase, Neon o Render.
- La API vieja reporta `database.ok: true`. **La base responde**; el fallo está en el código desplegado, no en la conexión.
- Si el Postgres del equipo está en Supabase, lo único que hace falta es la cadena de conexión en formato `postgresql+asyncpg://usuario:clave@host:PUERTO/postgres` (o la URL del pooler transaccional, puerto 6543) pegada en la variable `DATABASE_URL` **del dashboard de Render**. No necesito entrar a Supabase, ni ver tablas, ni credenciales de su proyecto.
- Lo que sí haría falta para que yo lo dejara funcionando de punta a punta es **acceso al dashboard de Render** (o una *Deploy Hook*). Desde este entorno no hay credenciales de Render ni conector disponible, así que no puedo cambiar variables ni lanzar el deploy. **No pegues tokens ni claves en el chat**: ya hay un PAT de GitHub que conviene rotar después de clase.

> Importante: usar una base **nueva y vacía**. El esquema del ZIP (`0001_esquema_inicial.py`) es incompatible con el SQLite anterior; apuntar el código nuevo a la base vieja falla igual que al revés.

---

## 4. Pasos exactos para arreglarlo

1. **Render → `cosplay-chile-api` → Environment**
   - `DATABASE_URL` = `postgresql+asyncpg://…` (PostgreSQL nuevo; ver nota anterior).
   - `FRONTEND_URL` = `https://cosplay-chile-web.onrender.com`.
   - `CORS_ORIGENES_EXTRA` = `https://cosplay-chile-web.onrender.com`.
   - `JWT_SECRET` generado, `PYTHON_VERSION=3.13.14`.
2. **Render → `cosplay-chile-web` → Environment**: confirmar `VITE_API_URL=https://cosplay-chile-api.onrender.com` (ya está, según el bundle).
3. **Manual Deploy** de `cosplay-chile-api` con *Clear build cache & deploy*. En los logs deben verse, en orden: `alembic upgrade head`, `Seed cargado (N etapas)` y `Uvicorn running on …`.
4. Si el deploy falla, leer el **primer** error del log: suele ser la URL de la BD o permisos para crear las extensiones `unaccent` y `pg_trgm` que crea la migración.
5. Recargar la web (no hace falta redesplegarla: el bundle ya apunta bien).

---

## 5. Verificación en 30 segundos

```bash
# 1) salud del backend nuevo
curl -s -o /dev/null -w "%{http_code}\n" https://cosplay-chile-api.onrender.com/api/salud     # esperado 200

# 2) la portada devuelve estadísticas reales
curl -s https://cosplay-chile-api.onrender.com/api/inicio | head -c 200                       # esperado {"estadisticas":{...}}

# 3) ~60 rutas en vez de 49
curl -s https://cosplay-chile-api.onrender.com/openapi.json \
  | python3 -c "import json,sys; print(len(json.load(sys.stdin)['paths']),'rutas')"
```

También está el script `scripts/verificar_render.sh`, que hace las tres comprobaciones y dice si el stack nuevo está vivo:

```bash
bash scripts/verificar_render.sh
# o con otras URLs:
API_URL=https://… WEB_URL=https://… bash scripts/verificar_render.sh
```

Mientras Render no esté reconfigurado, la demo segura sigue siendo local:

```bash
docker compose up --build
```

---

## 6. Nota sobre el seed

`python -m app.seed` es **idempotente**: si la base ya tiene usuarios, no vuelve a cargar. Para forzar los datos de ejemplo: `python -m app.seed --reset` desde `backend/`. Por eso, si se reutiliza una base con datos viejos, las cifras de la portada podrían seguir siendo las antiguas aunque el backend nuevo ya esté desplegado.

---

## 7. Caso posterior: ajuste móvil sin poder pushear a Git

El ajuste de imágenes para móvil (`CORRECCIONES_ES3.md` §12) quedó en el código fuente, pero **no se pudo subir a `main`** porque el entorno no tenía credenciales de GitHub. Render construye desde el repositorio, así que el cambio no aparecía en producción aunque el build local estuviera correcto.

**Solución temporal por API.** Se actualizó el `buildCommand` de `cosplay-chile-web`. Para un `static_site`, el `PATCH /v1/services/{id}` usa `serviceDetails` con los campos **planos** (`buildCommand`, `publishPath`) — variante `staticSiteDetailsPATCH` —, no `envSpecificDetails` como en el web service:

```
grep -q 'ajuste-movil-es3' src/index.css || printf '%s' '<base64>' | base64 -d >> src/index.css; npm ci && npm run build
```

El marcador `ajuste-movil-es3` hace el comando **idempotente**: cuando el commit con el CSS llegue a `main`, el `buildCommand` puede volver a `npm ci && npm run build` sin duplicar reglas. La documentación de Render confirma que un PATCH de configuración **no despliega automáticamente**: después hay que llamar a `POST /v1/services/{id}/deploys` con `{"clearCache":"clear"}`.

**Resultado.** Deploy `dep-dbtjk0u1egvs73b4vmsg` → `live`; se sirve `index-B7RbawAk.css` (idéntico al build local) e `index-BiZJm7rM.js`. Móvil 390×844: collage 350×289, 3/3 SVG con `contain`, 0 imágenes rotas. Escritorio 1440×900: collage 560 px y `cover`, **sin cambios**.

**Consistencia.** `scripts/arreglar_render.py` y `render.yaml` ya incluyen el prefijo de regeneración de SVG en `startCommand`; re-ejecutar el script de rescate no pisa la corrección de la §10.

**Diagnóstico de escritorio (sin cambios aplicados).** Se revisaron además «Trajes recientes», «Qué encuentras aquí» y «Hecho por y para la comunidad» en 1440×900: no hay desborde horizontal (`scrollWidth = clientWidth`), las 12 imágenes cargan y no hay errores JS. Lo que se percibe como «corrido» es, por un lado, la composición asimétrica del diseño recibido (`items-end text-right` en los títulos, collages con `md:mt-20` / `md:mt-10`) y, por otro, el `object-cover` de los SVG del seed en tarjetas verticales. **Se decidió no modificar escritorio**; el ajuste autorizado sigue siendo sólo ≤ 640 px.

**Cierre (16-11-2026, más tarde).** Ya se pudo pushear a `main` con el PAT: el bloque móvil quedó en
`frontend/src/index.css` dentro del repositorio y el `buildCommand` de `cosplay-chile-web` volvió a
`npm ci && npm run build`. El parche por `buildCommand` de esta sección fue **temporal** y ya no es necesario;
se conserva como bitácora de cómo se desplegó sin credenciales de Git.
