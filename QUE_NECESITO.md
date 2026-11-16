# ✅ Arreglo completado — ya no necesito nada

Con la API key de Render y la contraseña de Supabase que me pasaste, el deploy quedó **`live`** el 16-11-2026.

## Resultado final

| Comprobación | Antes | Ahora |
|---|---|---|
| `GET /api/salud` | 404 `Not Found` | **200** `{"estado":"ok"}` |
| `GET /api/inicio` | 404 | **200** con estadísticas reales |
| Rutas OpenAPI | 49 (stack viejo) | **60** |
| Personas registradas | `—` | **11** |
| Guías publicadas | `—` | **17** |
| Profesionales y tiendas | `—` | **23** |
| Eventos próximos | `—` | **12** |
| Login `admin@cosplaychile.cl` | — | **200** con JWT |
| CORS desde la web | — | **correcto** |
| `scripts/verificar_render.sh` | 3 fallos | **4 OK** |

**Tú solo tienes que recargar la web con Ctrl+F5** en https://cosplay-chile-web.onrender.com.

## Qué se hizo

1. Se detectó que el deploy anterior terminó en `update_failed` porque el servicio seguía con el `startCommand` del stack viejo (`python -m app.seed.datos_base` / `app.seed.demo`, módulos inexistentes en el backend nuevo) y con `healthCheckPath: /health`.
2. Se corrigió vía API de Render: `alembic upgrade head && python -m app.seed && uvicorn …` y `/api/salud`.
3. Se verificó que `main` (`b1f5625`) tiene el código nuevo con `asyncpg`, `alembic` y `app/seed/__main__.py`.
4. La `DATABASE_URL` anterior apuntaba a un proyecto Supabase **ya eliminado**. Se validó la nueva conexión con `psql` y con `asyncpg` + SQLAlchemy (PostgreSQL 17, base vacía, SSL), se codificaron los caracteres especiales de la contraseña y se precrearon `unaccent` y `pg_trgm` en `public`.
5. Se escribieron las 15 variables de entorno (conservando las 11 existentes), se disparó el deploy con caché limpia y se esperó hasta `live` (~2 min).
6. Se verificó de punta a punta: salud, portada, 60 rutas, login, CORS y rutas de contenidos/directorio/eventos/categorías.

La automatización idempotente quedó en `scripts/arreglar_render.py`; el diagnóstico con evidencia en `DIAGNOSTICO_RENDER.md` y el estado de la demo en `GUIA_DEMO.md`.

## Seguridad — hazlo después de clase

- **Rota la API key de Render** (`rnd_…`): está en el historial del chat.
- **Resetea la contraseña de Supabase** y actualiza `DATABASE_URL` en Render si la cambias.
- **Revoca el token de GitHub** que se pegó antes.
- Desactiva el seed (`DEMO_SEED=0`) y borra o cambia la clave de las cuentas demo.

Los secretos se usaron solo en memoria: no se imprimieron en claro, no están en el repositorio ni en el ZIP (verificado).
