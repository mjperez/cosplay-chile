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

## Guion de 12 minutos

1. **Portada (1 min).** Estadísticas reales, buscador con autocompletado («EVA»), filtros rápidos por región y categoría. Mostrar que las cifras vienen de `/api/inicio`.
2. **Directorio y mapa (1.5 min).** `/directorio` → tocar una región del mapa de Chile → ver ficha con precios, servicios y reseñas. «Ver mapa detallado» abre Leaflet.
3. **Guías (1 min).** `/guias` → filtrar por nivel → abrir una guía → compartir en redes. Destacar video embebido y descarga HTML.
4. **Identificarse (1 min).** Probar clave incorrecta → «Datos incorrectos». Probar `suspendido@demo.cl` → aviso de suspensión y enlace a contacto.
5. **Publicar tutorial (1.5 min).** Entrar como `camila@demo.cl` → `/guias/publicar` → enviar con una imagen. Ver el estado *Pendiente* en `/perfil` y el aviso en la campana 🔔.
6. **Moderación (2 min).** Entrar como `admin@cosplaychile.cl` → `/moderacion` → aprobar el tutorial (se avisa a toda la comunidad), resolver un reporte con «Ocultar y suspender», publicar el evento sugerido y abrir la **Bitácora**.
7. **Comunidad y desafíos (1.5 min).** `/comunidad` → responder un tema → ver el aviso al autor. `/desafios` → participar con foto y créditos.
8. **Perfil y seguridad (1 min).** `/perfil` → editar biografía y región → activar perfil público. `/seguridad` → consejos y formulario de contacto.
9. **Calidad (1.5 min).** Mostrar `/docs` (60 rutas), `.github/workflows/ci.yml` (96 pruebas, 97% cobertura, 59 pruebas de interfaz) y `CORRECCIONES_ES3.md` (9 hallazgos con evidencia).
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
