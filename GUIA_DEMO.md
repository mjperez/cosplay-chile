# Guía de la demo del lunes

Todo lo que necesitas para mostrar un software funcionando en clases, sin
haber tocado tu PC. Esta guía asume que ya fusionaste el pull request.

## Qué quedó listo

| Verificación | Resultado |
|---|---|
| Pruebas de backend (`pytest`) | **136 en verde** |
| Lint del frontend (`npm run lint`) | **0 errores, 0 advertencias** |
| Compilación (`npm run build`) | **correcta**, genera `dist/` |
| Recorrido HTTP real con datos | **26/26 comprobaciones en verde** |
| Módulos con pantalla y API | **6** + **panel de administración** (directorio, contenidos, eventos, foro, desafíos, comunidad, perfil y `/admin`) |
| Cuentas y contenido de ejemplo | listos con una sola orden |

---

## Opción A · Demo local (la más confiable, ~10 minutos)

Solo necesitas **cualquier computador** con Python y Node, internet para
instalar dependencias y este repositorio. No hace falta Supabase ni Render:
la demo corre sobre un archivo SQLite local. Es la opción recomendada si en la
sala hay un PC disponible.

```bash
git clone https://github.com/mjperez/cosplay-chile.git
cd cosplay-chile
git checkout main          # o la rama que hayas fusionado

# --- Backend ---
cd backend
python -m venv .venv
source .venv/bin/activate                  # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt

cat > .env <<'ENV'
DATABASE_URL=sqlite+pysqlite:///./cosplay_demo.db
JWT_SECRET=clave-local-para-la-demo-2026
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60
BCRYPT_ROUNDS=4
ENVIRONMENT=local
CORS_ORIGINS=http://localhost:5173
ENV

alembic upgrade head
python -m app.seed.datos_base
python -m app.seed.demo
uvicorn app.main:app --reload --port 8000
```

En otra terminal:

```bash
cd cosplay-chile/frontend
npm ci
npm run dev
```

Abre **http://localhost:5173**. Comprueba primero **http://localhost:8000/health**
y **http://localhost:8000/docs**.

> Si el PC es Windows, `source` se cambia por `.venv\Scripts\activate` y el
> `cat > .env` por crear el archivo con el bloc de notas con ese mismo
> contenido. Todo lo demás es igual.

## Opción B · Demo en Render (se puede abrir desde el móvil)

Útil si no consigues un PC: la URL pública se abre en cualquier navegador.
Necesitas la cadena `DATABASE_URL` de Supabase en el panel de Render.

Comprobado tras la fusión: **https://cosplay-chile-web.onrender.com** y
**https://cosplay-chile-api.onrender.com/health** responden 200 con la versión
nueva, y el bundle del frontend ya incluye el panel de administración.

1. Los cambios ya están en `main`. Render despliega **solo desde `main`**;
   si te quedas en `dev` o en una rama de trabajo, no verás los cambios en la
   URL. Si el despliegue no se disparó, usa **Manual Deploy → Deploy latest
   commit** en cada servicio.
2. Espera a que los dos servicios estén en **Live** (`cosplay-chile-api` y
   `cosplay-chile-web`). El plan gratuito tarda unos minutos en el primer
   despliegue y ~30-50 s en despertar tras estar inactivo: ábrelo **antes** de
   entrar a clases.
3. Variables en el panel (sin barra final en las URLs):

   | Servicio | Variable | Valor |
   |---|---|---|
   | API | `DATABASE_URL` | pooler de Supabase con `sslmode=require` |
   | API | `JWT_SECRET` | la genera Render |
   | API | `CORS_ORIGINS` | URL pública del **frontend** |
   | API | `DEMO_SEED` | `1` (ya viene por defecto en `render.yaml`) |
   | Web | `VITE_API_URL` | URL pública del **backend** |

   Orden importante: crea primero el backend para obtener su URL, ponla en
   `VITE_API_URL`, crea el frontend y copia su URL en `CORS_ORIGINS`. Sin
   `CORS_ORIGINS` el navegador bloquea todas las peticiones.
4. **Si el login `demo@cosplay.cl` da 401**, el servicio se creó antes del
   cambio de `render.yaml` y sigue usando su `startCommand` anterior: Render
   no vuelve a leer el blueprint al hacer `git push`. Haz una de estas dos
   cosas, cualquiera sirve:
   - **Environment** del servicio `cosplay-chile-api` → añadir `DEMO_SEED=1`
     → **Manual Deploy → Deploy latest commit**.
   - O, en el Blueprint, **Sync / Apply** para que tome el `render.yaml` nuevo,
     que ya trae `DEMO_SEED=1` por defecto.

   En un despliegue **nuevo** no hay que hacer nada: la semilla demo corre
   sola. Compruébalo entrando con `demo@cosplay.cl` / `Demo2026!`.
5. Tras la demo, **pon `DEMO_SEED=0`** y vuelve a desplegar. Las filas ya
   creadas no se borran solas: elimina las tres cuentas demo desde la base o
   cambia sus contraseñas.

---

## Cuentas de la demo

Todas con contraseña **`Demo2026!`**:

| Correo | Rol | Sirve para |
|---|---|---|
| `demo@cosplay.cl` | administrador | abrir `/admin`, crear eventos/desafíos, elegir ganador, publicar borradores, moderar el foro |
| `cosplayer@cosplay.cl` | cosplayer | inscribirse, responder el foro, editar perfil |
| `organizador@cosplay.cl` | organizador | mostrar que ya tiene inscripciones previas |

Datos precargados: **6 eventos** (con 3 inscripciones de ejemplo), **5 temas
del foro** con respuestas, **2 desafíos** (el vigente y el anterior con
ganador), **6 tiendas**, **5 grupos**, **20 fichas** del directorio, **5
categorías** y **3 contenidos publicados**.

---

## Guion de 8 minutos

1. **Inicio (30 s).** Mostrar las seis tarjetas de módulos, todas con enlace
   activo. Enseñar que el encabezado ya no tiene etiquetas «pronto».
2. **Directorio (1 min).** `/directorio` → filtrar por región «Metropolitana»
   y por tipo, buscar por texto. Destacar que son 20 fichas reales del
   levantamiento y que no se publican datos de personas naturales.
3. **Contenidos (1 min).** `/contenido` → abrir una guía, mostrar niveles,
   materiales y pasos. Comentar el flujo borrador → publicación.
4. **Eventos (2 min).** `/eventos` → filtrar por «convencion» → abrir el
   detalle → ver los participantes → **ingresar como `cosplayer@cosplay.cl`** →
   inscribirse con un personaje → ver «mis eventos» y cancelar la inscripción.
   Aquí se ve autenticación, reglas de negocio y persistencia en una sola
   secuencia.
5. **Foro (1.5 min).** `/foro` → filtrar por categoría → abrir un tema →
   responder → como autor, **cerrar el tema** y comprobar que el formulario
   desaparece. Es el mejor momento para hablar de permisos (403).
6. **Desafíos y comunidad (1 min).** `/desafios` → destacado del mes + mes
   anterior con ganador. `/comunidad` → tiendas que envían a Chile y grupos
   por región.
7. **Perfil (1 min).** `/perfil` → editar especialidad, biografía y región
   (incluido «prefiero no indicarla») → guardar y volver a ver.
8. **Panel de administración (2 min).** Cerrar sesión y entrar como
   `demo@cosplay.cl`: aparece **Administración** en el encabezado. Abrir
   `/admin` → **Resumen** (12 contadores) → **Contenido** (crear un borrador
   con la cuenta cosplayer y publicarlo aquí) → **Eventos** (crear uno y
   verlo en `/eventos`) → **Foro** (ocultar un tema y comprobar que sale del
   foro público, luego reabrirlo) → **Usuarios** (la cuenta admin no se puede
   desactivar a sí misma). Cada acción recarga el panel con un aviso verde.
9. **Cierre (30 s).** Abrir `/docs` y mostrar las 43 rutas; mencionar 136
   pruebas, lint limpio y los dos servicios de Render.

### Si quieres mostrar la API por debajo del panel

Entra como `demo@cosplay.cl`, abre `/docs` y usa **Authorize** con el token del
login. El panel no hace nada que no esté en la API: son las mismas operaciones
con una interfaz encima.

| Acción del panel | Endpoint |
|---|---|
| Portada con métricas | `GET /api/v1/admin/resumen` |
| Crear evento | `POST /api/v1/admin/eventos` |
| Crear desafío | `POST /api/v1/admin/desafios` (mes `YYYY-MM`) |
| Elegir ganador | `POST /api/v1/admin/desafios/{id}/ganador` |
| Publicar un borrador | `POST /api/v1/admin/contenido/{id}/publicar` |
| Ocultar un tema | `PATCH /api/v1/admin/foro/temas/{id}` |

Ejemplo rápido de crear un evento desde la terminal:

```bash
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"correo":"demo@cosplay.cl","password":"Demo2026!"}' \
  | python -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

curl -X POST http://localhost:8000/api/v1/admin/eventos \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"nombre":"Convención de demostración","tipo":"convencion","fecha_inicio":"2026-12-05T10:00:00Z","lugar":"Sala de clases","region":"Metropolitana"}'
```

---

## Lista de verificación antes de clase

- [ ] `http://localhost:8000/health` responde 200 (o el health check de Render está en verde).
- [ ] La portada carga y las seis tarjetas llevan a páginas reales.
- [ ] Puedes iniciar sesión con `cosplayer@cosplay.cl` / `Demo2026!`.
- [ ] `/eventos` muestra 6 eventos y `/foro` muestra 5 temas.
- [ ] Entrando como `demo@cosplay.cl` se ve **Administración** y `/admin` carga el resumen.
- [ ] En Render, el login `demo@cosplay.cl` / `Demo2026!` responde 200 (si da 401, redesplegar la API).
- [ ] Si usas Render, abriste la URL 5 minutos antes para evitar el arranque en frío.
- [ ] Llevas esta guía abierta en el móvil por si falla la red de la sala (la opción A no depende de internet una vez instaladas las dependencias).

## Si algo falla

| Síntoma | Causa probable | Solución |
|---|---|---|
| La web carga pero todo dice «No pudimos cargar…» | Backend apagado o `VITE_API_URL` mal puesta | Revisa `/health`; quita la barra final de la URL y recompila el frontend |
| Errores de CORS en la consola | `CORS_ORIGINS` no incluye la URL del frontend | Añádela en Render y reinicia el servicio API |
| Directorio o contenidos vacíos | No corrieron las semillas | `python -m app.seed.datos_base` (y `demo` si quieres las cuentas) |
| Login devuelve 401 con la contraseña correcta | Se cargó `datos_base` pero no `demo` | `python -m app.seed.demo` |
| En Render el login demo da 401 | El servicio existente no tomó el `render.yaml` nuevo | Añadir `DEMO_SEED=1` en Environment y **Manual Deploy**, o hacer **Sync** del Blueprint |
| El login demo da 429 | Demasiados intentos fallidos seguidos (bloqueo de 15 min por correo) | Esperar 15 min; el contador se libera solo |
| `alembic` falla con «table already exists» | Base de una ejecución anterior | Borra `cosplay_demo.db` y vuelve a correr migración + semillas |
| 404 al recargar `/eventos` en Render | Falta la regla de rewrite | `render.yaml` ya la trae; verifica que el servicio sea de tipo `static` |

---

## Si quieres volver atrás (rollback)

**Sí se puede**, y no hace falta rehacer nada. Antes de llevar los cambios a
`main` se dejó una rama y una etiqueta de respaldo apuntando al `main`
anterior: `backup/pre-demo-admin` y `backup-pre-demo-admin` (commit `bcef3c4`).

Tres formas, de menos a más drástica:

| Forma | Cuándo usarla | Cómo |
|---|---|---|
| **Rollback en Render** | Solo quieres volver a la versión anterior ya desplegada, sin tocar Git | Panel de Render → servicio → pestaña **Deploys** → elegir el deploy anterior → **Redeploy**. Es instantáneo y no cambia el repo |
| **`git revert`** (recomendado en Git) | Quieres que `main` quede limpio y que Render vuelva a desplegar solo | `git checkout main && git revert -m 1 94f8b2c0 && git push origin main` |
| **Restaurar el respaldo** | Quieres exactamente el estado previo, sin historial del intento | `git checkout main && git reset --hard backup-pre-demo-admin && git push --force-with-lease origin main` |

> Evita `reset --hard` + push forzado si alguien más usa el repo: reescribe el
> historial compartido. Para una demo, `git revert` o el rollback de Render
> alcanzan. Tanto la rama `backup/pre-demo-admin` como la etiqueta
> `backup-pre-demo-admin` **ya están publicadas en GitHub**, así que el respaldo
> sobrevive aunque borres el clon local o trabajes solo desde el móvil.

Recuerda que las **migraciones no se revierten** con `git revert`: este cambio
no agregó ninguna migración, así que la base sigue siendo compatible con ambas
versiones. Si en el futuro revertís un cambio que sí tocó Alembic, revisa ese
punto antes.

---

## Seguridad: revoca el token de GitHub

El token de acceso personal que usaste para crear el PR y llevar los cambios
a `main` debe revocarse en cuanto termines:
https://github.com/settings/personal-access-tokens → **Revoke**. Tenía
caducidad corta y permisos limitados a este repositorio, y no se guardó en
ningún archivo del proyecto.

Las cuentas `demo@cosplay.cl` y compañía son deliberadamente inseguras: no las
dejes activas en un despliegue público después de la clase.
