# Guía de la demo del lunes

Todo lo que necesitas para mostrar un software funcionando en clases, sin
haber tocado tu PC. Esta guía asume que ya fusionaste el pull request.

## Qué quedó listo

| Verificación | Resultado |
|---|---|
| Pruebas de backend (`pytest`) | **169 en verde**, cobertura **96%** |
| Lint del frontend (`npm run lint`) | **0 errores, 0 advertencias** |
| Compilación (`npm run build`) | **correcta**, genera `dist/` |
| Pipeline de CI/CD | **verde** en `.github/workflows/ci.yml` + `autoDeploy` en Render |
| Recorrido HTTP real con datos | **51/51 comprobaciones en verde** (`backend/scripts/recorrido_http.py`) |
| Rutas en OpenAPI | **49** (antes 43) |
| Módulos con pantalla y API | **7** + **panel de administración**: directorio, contenidos, eventos, foro, desafíos, comunidad, perfil, **avisos** y `/admin` con **Auditoría** |
| Los cuatro patrones del ES2 | Singleton, Factory Method, **Observer** y **Adapter** implementados y probados |
| Cuentas y contenido de ejemplo | listos con una sola orden |

La evidencia de las correcciones hechas a partir de testing e ISO 27000 está en
[`CORRECCIONES_ES3.md`](CORRECCIONES_ES3.md); el mapa de los tres servicios
(entrada → proceso → resultado) y las decisiones técnicas, en `README.md`.

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
STORAGE_BACKEND=local
STORAGE_DIRECTORIO=./archivos-demo
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
   | API | `STORAGE_BACKEND` | `local` (viene en `render.yaml`) |
   | API | `STORAGE_DIRECTORIO` | `/tmp/cosplay-archivos` (disco efímero del plan free) |
   | Web | `VITE_API_URL` | URL pública del **backend** |

   Las imágenes que subas en la demo se sirven desde `/archivos`. En Render el
   disco es efímero, así que desaparecen al reiniciar el servicio: para la clase
   no importa, y está documentado como *trade-off* en `README.md`.

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

| Correo | Se ve como | Rol | Sirve para |
|---|---|---|---|
| `demo@cosplay.cl` | **Usuario Administrador** | administrador | abrir `/admin`, crear eventos/desafíos, elegir ganador, publicar borradores, moderar el foro |
| `cosplayer@cosplay.cl` | **Usuario Cosplayer** | cosplayer | inscribirse, responder el foro, editar perfil |
| `organizador@cosplay.cl` | **Usuario Organizador** | organizador | mostrar que ya tiene inscripciones previas |

El nombre visible dice el rol: al proyectar la pantalla, quien mira sabe al
instante con qué permisos se entró, sin tener que acordarse de un nombre de
persona. Si tu base ya tenía las cuentas de una versión anterior, basta con
volver a ejecutar la semilla: **sincroniza los nombres** sin duplicar cuentas
ni cambiar contraseñas, roles o consentimientos.

Datos precargados: **6 eventos** (con 3 inscripciones de ejemplo), **5 temas
del foro** con respuestas, **2 desafíos** (el vigente y el anterior con
ganador), **6 tiendas**, **5 grupos**, **20 fichas** del directorio, **5
categorías** y **3 contenidos publicados**.

---

## Guion de 12 minutos

1. **Inicio (30 s).** Mostrar las tarjetas de módulos, todas con enlace activo.
   Enseñar que el encabezado ya no tiene etiquetas «pronto» y que ahora
   aparece **Avisos** con un contador de no leídas.
2. **Directorio (1 min).** `/directorio` → filtrar por región «Metropolitana»
   y por tipo, buscar por texto. Destacar que son 20 fichas reales del
   levantamiento y que no se publican datos de personas naturales.
3. **Contenidos con imagen (2 min).** `/contenido` → abrir una guía, mostrar
   niveles, materiales y pasos. Luego `/contenido/nuevo` con la cuenta
   cosplayer: elegir «Guía», **adjuntar un PNG** (se ve la miniatura), guardar
   como borrador. La pantalla de confirmación explica que el envío generó
   avisos, correo a moderación y un registro de auditoría. Aquí se ven juntos
   el **Adapter** (validación con magic bytes y URL pública), el **Factory
   Method** (el formulario cambia por tipo) y el **Observer**.
4. **Avisos (1 min).** Sin cambiar de cuenta, mirar el badge **Avisos** del
   encabezado → `/notificaciones` → marcar uno como leído. Es el servicio 2
   del mapa entrada → proceso → resultado.
5. **Eventos (2 min).** `/eventos` → filtrar por «convencion» → abrir el
   detalle → ver los participantes → **ingresar como `cosplayer@cosplay.cl`** →
   inscribirse con un personaje → ver «mis eventos» y cancelar la inscripción.
   Aquí se ve autenticación, reglas de negocio y persistencia en una sola
   secuencia.
6. **Foro (1.5 min).** `/foro` → filtrar por categoría → abrir un tema →
   responder → como autor, **cerrar el tema** y comprobar que el formulario
   desaparece. Es el mejor momento para hablar de permisos (403).
7. **Desafíos y comunidad (1 min).** `/desafios` → destacado del mes + mes
   anterior con ganador. `/comunidad` → tiendas que envían a Chile y grupos
   por región.
8. **Perfil (1 min).** `/perfil` → editar especialidad, biografía y región
   (incluido «prefiero no indicarla») → guardar y volver a ver.
9. **Panel de administración (2.5 min).** Cerrar sesión y entrar como
   `demo@cosplay.cl`: aparece **Administración** en el encabezado. Abrir
   `/admin` → **Resumen** (12 contadores) → **Contenido** (publicar el borrador
   con imagen que creó el cosplayer) → **Eventos** (crear uno: eso dispara
   avisos a toda la comunidad menos al actor) → **Foro** (ocultar un tema y
   reabrirlo) → **Usuarios** (la cuenta admin no se puede desactivar a sí
   misma) → **Auditoría** (mostrar las filas recién generadas: fecha,
   categoría, evento, actor, recurso y detalle; explicar que el log sobrevive
   a la baja de la cuenta por ISO 27002 A.8.15 y Ley 19.223).
10. **Cierre (30 s).** Volver a entrar como cosplayer y ver que el badge
    **Avisos** subió con el evento nuevo. Abrir `/docs` y mostrar las **49
    rutas**; mencionar **169 pruebas**, **96% de cobertura**, el pipeline de
    CI/CD y los dos servicios de Render.

### Los tres servicios que pide el paso 3

| Servicio | Entrada | Proceso | Resultado observable |
|---|---|---|---|
| Subir imagen | PNG + token | whitelist + magic bytes + `IAlmacenamientoArchivos` | miniatura y URL absoluta en `imagenes` |
| Enviar tutorial | formulario por tipo | Factory + 3 observadores en la misma transacción | borrador, aviso al autor, correo encolado, fila en bitácora |
| Crear evento | formulario admin | `evento_creado` → avisos masivos + log | evento en `/eventos`, badge con N avisos, fila en **Auditoría** |

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
| **Ver la bitácora** | `GET /api/v1/admin/auditoria?limite=100` |
| **Contador de avisos** | `GET /api/v1/notificaciones/sin-leer` |
| **Bandeja de avisos** | `GET /api/v1/notificaciones` |
| **Marcar como leído** | `PATCH /api/v1/notificaciones/{id}/leer` |
| **Subir una imagen** | `POST /api/v1/archivos` (multipart, campo `archivo`) |

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
- [ ] El encabezado dice **Hola, Usuario Administrador** (o *Usuario Cosplayer*),
      no un nombre de persona: así se ve de inmediato con qué rol entraste.
- [ ] `/eventos` muestra 6 eventos y `/foro` muestra 5 temas.
- [ ] Entrando como `demo@cosplay.cl` se ve **Administración** y `/admin` carga el resumen.
- [ ] El encabezado muestra **Avisos** y `/notificaciones` abre la bandeja.
- [ ] En `/contenido/nuevo` se puede adjuntar un PNG y aparece la miniatura.
- [ ] En `/admin` existe la pestaña **Auditoría** y muestra registros con fecha, actor y detalle.
- [ ] `GET /api/v1/notificaciones/sin-leer` con token responde 200 y el badge coincide.
- [ ] `GET /api/v1/admin/auditoria` con token de cosplayer responde **403** (rol).
- [ ] `POST /api/v1/archivos` con un SVG renombrado a `.png` responde **415** (magic bytes).
- [ ] `GET /docs` muestra **49 rutas**, incluidas `/archivos` y `/admin/auditoria`.
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
| **Restaurar el respaldo** (lo más simple para volver del todo) | Quieres exactamente el estado previo | `git checkout main && git reset --hard backup-pre-demo-admin && git push --force-with-lease origin main` |
| **`git revert`** | Quieres conservar el historial y que Render redespliegue solo | Ver la secuencia de abajo |

> **Ojo con el `git revert`.** El merge del PR es `94f8b2c`, pero después se
> subieron varios commits directos a `main` (despliegue, nombres de cuentas,
> corrección del rollback y, por último, el cierre de ES3 con Observer,
> Adapter y CI/CD). Hacer solo `git revert -m 1 94f8b2c0` quita la plataforma
> pero **deja todos esos commits**. La secuencia completa, en orden inverso y
> verificada en una rama desechable, deja el árbol idéntico al respaldo
> `bcef3c4`:
>
> ```bash
> git checkout main && git pull --ff-only
> ULTIMO=$(git rev-parse --short HEAD)     # el commit de cierre de ES3
> git revert --no-edit "$ULTIMO"
> git revert --no-edit 3454d91
> git revert --no-edit 3c76c06
> git revert --no-edit 1e17741
> git revert --no-edit 078a7ed
> git revert --no-edit 95fed8a
> git revert -m 1 --no-edit 94f8b2c0
> git push origin main
> ```
>
> Si en el futuro se agregan más commits a `main`, basta con revertirlos
> primero: `git log --oneline bcef3c4..HEAD` los lista de más reciente a más
> antiguo, y se revierten en ese mismo orden. Sólo el merge `94f8b2c0`
> necesita `-m 1`.
>
> Importante: ejecútala con el árbol limpio (`git status` sin cambios). Si hay
> archivos sin commitear, el primer revert se aborta y los siguientes producen
> conflictos `modify/delete`; en ese caso `git revert --abort`, guarda tus
> cambios y vuelve a empezar. Para una demo, el rollback de Render o restaurar
> el respaldo son más rápidos.

> Evita `reset --hard` + push forzado si alguien más usa el repo: reescribe el
> historial compartido. Tanto la rama `backup/pre-demo-admin` como la etiqueta
> `backup-pre-demo-admin` **ya están publicadas en GitHub**, así que el respaldo
> sobrevive aunque borres el clon local o trabajes solo desde el móvil.

> **⚠️ Ahora SÍ hay una migración nueva.** ES3 agregó
> `0005_observer_notificaciones_auditoria.py`, que crea `notificacion` y
> `bitacora_auditoria`. Es puramente **aditiva**: el código anterior a ES3
> simplemente ignora esas dos tablas y puede seguir leyendo la base. Lo que
> **no** es compatible es `alembic_version`, que queda en `0005` mientras el
> código revertido sólo conoce hasta `0004`; el `startCommand` de Render
> ejecuta `alembic upgrade head` y fallaría al no encontrar la revisión.
> Antes de redesplegar código anterior, baja el esquema:
>
> ```bash
> cd backend
> alembic downgrade 0004
> ```
>
> En la base de Render esto se hace con una sesión de shell del servicio o con
> una consulta sobre `alembic_version` si no hay shell disponible. Si decides
> **no** hacer el downgrade porque las tablas nuevas no estorban, deja al menos
> el archivo `0005` en el árbol para que Alembic siga resolviendo `head`.

---

## Después de la clase: cierre obligatorio

**Esto es lo único que falta por hacer.** Mientras la demo esté montada, la
contraseña `Demo2026!` es pública y hay una cuenta `administrador` accesible
desde internet. En cuanto termines:

1. En **Environment** de `cosplay-chile-api`, cambia `DEMO_SEED` a `0` y haz
   **Manual Deploy → Deploy latest commit**. Sin esto, cada arranque vuelve a
   crear las cuentas demo aunque las borres a mano (el `startCommand` tiene
   `export DEMO_SEED="${DEMO_SEED:-1}"`, así que dejar la variable vacía no
   basta).
2. **Borra las tres cuentas demo de la base** o cámbiales la contraseña.
   Borrarlas sin el paso 1 no sirve: se recrean en el próximo despliegue.
3. **Revoca el token de GitHub**: https://github.com/settings/personal-access-tokens
   → **Revoke**. Tenía caducidad corta y permisos limitados a este repositorio,
   y no se guardó en ningún archivo del proyecto.
4. Revisa la base de producción: además de las tres cuentas demo hay una
   cuenta real registrada a mano (`mariajperezc@gmail.com`). Si la creaste tú
   probando el formulario, bórrala si no la vas a usar.
5. Si quieres dejar `render.yaml` seguro para el futuro, cambia el valor de
   `DEMO_SEED` a `"0"` y quita el `export DEMO_SEED="${DEMO_SEED:-1}"` del
   `startCommand`. Hoy está en `1` a propósito para que la entrega en clases
   funcione sin configurar nada.

Las cuentas `demo@cosplay.cl` y compañía son deliberadamente inseguras: no las
dejes activas en un despliegue público después de la clase.
