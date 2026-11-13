# Guía de la demo del lunes

Todo lo que necesitas para mostrar un software funcionando en clases, sin
haber tocado tu PC. Esta guía asume que ya fusionaste el pull request.

## Qué quedó listo

| Verificación | Resultado |
|---|---|
| Pruebas de backend (`pytest`) | **121 en verde** |
| Lint del frontend (`npm run lint`) | **0 errores, 0 advertencias** |
| Compilación (`npm run build`) | **correcta**, genera `dist/` |
| Recorrido HTTP real con datos | **15/15 comprobaciones en verde** |
| Módulos con pantalla y API | **6** (directorio, contenidos, eventos, foro, desafíos, comunidad y perfil) |
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

1. Fusiona el PR en `dev` y luego `dev` → `main`. Render despliega **solo
   desde `main`**; si te quedas en `dev`, no verás los cambios en la URL.
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
   | API | `DEMO_SEED` | `1` para que carguen las cuentas de ejemplo |
   | Web | `VITE_API_URL` | URL pública del **backend** |

   Orden importante: crea primero el backend para obtener su URL, ponla en
   `VITE_API_URL`, crea el frontend y copia su URL en `CORS_ORIGINS`. Sin
   `CORS_ORIGINS` el navegador bloquea todas las peticiones.
4. Tras la demo, **quita `DEMO_SEED`** y vuelve a desplegar. Las filas ya
   creadas no se borran solas: elimina las tres cuentas demo desde la base o
   cambia sus contraseñas.

---

## Cuentas de la demo

Todas con contraseña **`Demo2026!`**:

| Correo | Rol | Sirve para |
|---|---|---|
| `demo@cosplay.cl` | administrador | crear eventos/desafíos, elegir ganador, publicar borradores |
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
8. **Cierre (30 s).** Abrir `/docs` y mostrar las 29 rutas; mencionar 121
   pruebas, lint limpio y los dos servicios de Render.

### Si quieres mostrar permisos de administrador

Entra como `demo@cosplay.cl` y usa `/docs` (botón **Authorize** con el token
del login) para estos endpoints; la interfaz no trae un panel de administración:

| Acción | Endpoint |
|---|---|
| Crear evento | `POST /api/v1/eventos` |
| Crear desafío | `POST /api/v1/desafios` (mes `YYYY-MM`) |
| Elegir ganador | `POST /api/v1/desafios/{id}/ganador` |
| Publicar un borrador | `POST /api/v1/contenido/{id}/publicar` |

Ejemplo rápido de crear un evento desde la terminal:

```bash
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"correo":"demo@cosplay.cl","password":"Demo2026!"}' \
  | python -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

curl -X POST http://localhost:8000/api/v1/eventos \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"nombre":"Convención de demostración","tipo":"convencion","fecha_inicio":"2026-12-05T10:00:00Z","lugar":"Sala de clases","region":"Metropolitana"}'
```

---

## Lista de verificación antes de clase

- [ ] `http://localhost:8000/health` responde 200 (o el health check de Render está en verde).
- [ ] La portada carga y las seis tarjetas llevan a páginas reales.
- [ ] Puedes iniciar sesión con `cosplayer@cosplay.cl` / `Demo2026!`.
- [ ] `/eventos` muestra 6 eventos y `/foro` muestra 5 temas.
- [ ] Si usas Render, abriste la URL 5 minutos antes para evitar el arranque en frío.
- [ ] Llevas esta guía abierta en el móvil por si falla la red de la sala (la opción A no depende de internet una vez instaladas las dependencias).

## Si algo falla

| Síntoma | Causa probable | Solución |
|---|---|---|
| La web carga pero todo dice «No pudimos cargar…» | Backend apagado o `VITE_API_URL` mal puesta | Revisa `/health`; quita la barra final de la URL y recompila el frontend |
| Errores de CORS en la consola | `CORS_ORIGINS` no incluye la URL del frontend | Añádela en Render y reinicia el servicio API |
| Directorio o contenidos vacíos | No corrieron las semillas | `python -m app.seed.datos_base` (y `demo` si quieres las cuentas) |
| Login devuelve 401 con la contraseña correcta | Se cargó `datos_base` pero no `demo` | `python -m app.seed.demo` |
| `alembic` falla con «table already exists» | Base de una ejecución anterior | Borra `cosplay_demo.db` y vuelve a correr migración + semillas |
| 404 al recargar `/eventos` en Render | Falta la regla de rewrite | `render.yaml` ya la trae; verifica que el servicio sea de tipo `static` |

---

## Seguridad: revoca el token de GitHub

El token de acceso personal que usaste para crear el PR debe revocarse en
cuanto termines: https://github.com/settings/personal-access-tokens →
**Revoke**. Tenía caducidad corta y permisos limitados a este repositorio, y
no se guardó en ningún archivo del proyecto.

Las cuentas `demo@cosplay.cl` y compañía son deliberadamente inseguras: no las
dejes activas en un despliegue público después de la clase.
