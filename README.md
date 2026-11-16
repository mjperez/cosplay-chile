# Cosplay Chile

Plataforma web gratuita para la comunidad cosplay chilena: guías educativas, directorio de proveedores y tiendas, calendario de eventos, foros, desafíos mensuales y moderación. Prototipo funcional de punta a punta del informe [`docs/informe_requerimientos.pdf`](docs/informe_requerimientos.pdf) (TI3043), construido sobre el diseño exportado de Claude Design ([`design/Cosplay Chile — Frontend.html`](design/Cosplay%20Chile%20—%20Frontend.html)).

- **Backend:** Python 3.12+ · FastAPI async · Pydantic · SQLAlchemy 2 async · Alembic · PostgreSQL · JWT + argon2
- **Frontend:** React 19 · React Router 7 · Tailwind CSS 4 · Leaflet · Vite · Vitest + Testing Library
- **Patrones:** Singleton, Factory Method, Observer y Adapter (ver [Patrones de diseño](#patrones-de-diseño))
- **Calidad:** **99 pruebas de backend**, **97% de cobertura**, **59 pruebas de interfaz**, **40/40 comprobaciones HTTP reales** y pipeline de CI con umbral de 90%.

## Levantar todo con un comando

### Opción A: Docker (recomendada)

```bash
docker compose up --build
```

| Servicio | URL |
|---|---|
| Aplicación | http://localhost:8080 |
| API y documentación OpenAPI | http://localhost:8000/docs |
| PostgreSQL | `localhost:5433` (usuario/clave `cosplay`) |

Al arrancar, el backend aplica las migraciones y carga los datos de demo si la base está vacía.

### Opción B: sin Docker, con PostgreSQL local (Windows/PowerShell)

Requisitos: Python 3.12+, Node 22+ y PostgreSQL 13+ con las extensiones `unaccent` y `pg_trgm`. Crea un rol y dos bases:

```sql
CREATE ROLE cosplay LOGIN PASSWORD 'cosplay';
CREATE DATABASE cosplay OWNER cosplay;
CREATE DATABASE cosplay_test OWNER cosplay;
```

Después, desde la raíz del repositorio:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\dev.ps1
```

El script crea `backend\.env` desde `.env.example`, instala dependencias, migra, carga el seed y levanta la API (http://localhost:8000/docs) y el frontend (http://localhost:5173). Si los puertos están ocupados, usa los siguientes libres y lo indica en consola. Usa `-ResetSeed` para recargar la demo.

## Cuentas de demostración

| Rol | Correo | Contraseña | Para mostrar |
|---|---|---|---|
| Administrador/Moderador | `admin@cosplaychile.cl` | `Admin2026!` | Panel de moderación: tutoriales y eventos pendientes, reportes, usuarios, bitácora |
| Usuaria registrada (cosplayer) | `camila@demo.cl` | `Cosplay2026!` | Publicar tutorial, favoritos, notificaciones, foro, desafío |
| Cosmaker con ficha pública | `joaquin@demo.cl` | `Cosplay2026!` | «Mi ficha» en el perfil (opt-in al directorio, RF-10) |
| Tienda con ficha pública | `tienda@demo.cl` | `Cosplay2026!` | Ficha de tienda (tipos de producto, envíos) |
| Cuenta suspendida | `suspendido@demo.cl` | `Cosplay2026!` | Login → aviso de suspensión + formulario de contacto |

Los negocios, comunidades y eventos del seed son **ficticios** (dominios `.example`). Las ilustraciones son SVG propios con diversidad de cuerpos, géneros y capacidades (RNF-10).

## Guion sugerido para la demo

1. **Visitante.** Portada con estadísticas y novedades; busca «EVA» con autocompletado; filtra el directorio tocando una región del **mapa de Chile**; elige un día en el **calendario**; comparte una guía en redes (RF-05).
2. **Identificarse (UC-01).** Clave incorrecta → «Datos incorrectos»; luego `suspendido@demo.cl` → aviso de suspensión y enlace a «Contacto y denuncias».
3. **Publicar tutorial (UC6)** con `camila@demo.cl`. El tutorial queda *Pendiente*, aparece el aviso en la campana 🔔 y se escribe un correo simulado a moderación en la consola del backend.
4. **Moderación** con `admin@cosplaychile.cl`. Aprueba el tutorial (se avisa a la comunidad), resuelve un reporte con «Ocultar y suspender», publica el evento sugerido y revisa la **Bitácora**.
5. **Recuperar contraseña.** El enlace aparece en la consola del backend como `[CORREO SIMULADO]`.

## Pruebas y calidad

```bash
cd backend
python -m pytest -q --cov=app --cov-report=term-missing --cov-fail-under=90
python scripts/recorrido_http.py        # 40/40 sobre una base aislada

cd ../frontend
npm ci && npm test && npm run build
```

| Verificación | Resultado |
|---|---|
| Pruebas de backend (pytest + PostgreSQL real) | **96 en verde**, **97% de cobertura** (2895 sentencias) |
| Pruebas de interfaz (Vitest + Testing Library) | **59 en verde**, 8 archivos |
| Recorrido HTTP real (`scripts/recorrido_http.py`) | **40/40 comprobaciones** |
| OpenAPI | **60 rutas** documentadas |
| Compilación de producción | correcta (`frontend/dist/`) |

`pytest` recrea el esquema con la migración real de Alembic y vacía las tablas antes de cada prueba; nunca toca la base de desarrollo. La cobertura usa el núcleo `sysmon` porque el trazador C pierde las líneas posteriores a un `await` (ver [`CORRECCIONES_ES3.md`](CORRECCIONES_ES3.md)).

La matriz RF ↔ prueba está en [`backend/tests/casos_por_rf.md`](backend/tests/casos_por_rf.md), los hallazgos corregidos en [`CORRECCIONES_ES3.md`](CORRECCIONES_ES3.md), las decisiones en [`docs/DECISIONES.md`](docs/DECISIONES.md) y las brechas del diseño en [`docs/BRECHAS_DISENO.md`](docs/BRECHAS_DISENO.md).

## Tres servicios: entradas, procesos y resultados

| Servicio | Entrada | Proceso | Resultado |
|---|---|---|---|
| **Publicar un tutorial (UC6)** | Formulario: título, descripción, nivel, categoría, pasos/materiales y video opcional | `ContenidoFactory` valida la categoría e instancia `GuiaTutorial`, `Entrevista` o `ArticuloTecnico`; el `GestorEventos` avisa al autor y a moderación | Borrador `PENDIENTE`, aviso 🔔, correo simulado a moderación y registro en la bitácora; tras aprobación se publica y avisa a la comunidad |
| **Completar la ficha del directorio (RF-10/RF-32)** | Datos de la ficha: nombre, servicios, precios, región, redes y portafolio con texto alternativo | `PUT /api/directorio/mi-ficha` valida URLs http(s) y sincroniza `Perfil` ↔ `DirectorioItem`; `directorio_sync` calcula coordenadas | Ficha pública en el mapa, con servicios, resenas y opt-in respetado |
| **Sugerir y moderar un evento (RF-17)** | Formulario de sugerencia: nombre, tipo, fechas, lugar y región | `POST /api/eventos/sugerir` crea el evento `PENDIENTE` y notifica; el panel de moderación aprueba o rechaza | Evento visible en el calendario (o rechazo), aviso al autor y traza en auditoría |

## Patrones de diseño

| Patrón | Dónde | Qué hace |
|---|---|---|
| **Singleton** | `backend/app/db/session_manager.py` | Un único motor y pool de conexiones; los routers reciben sesiones por inyección (`get_db`) |
| **Factory Method** | `backend/app/patterns/contenido_factory.py` | `ContenidoFactory.crear_contenido(tipo, datos)` → `GuiaTutorial`, `Entrevista`, `ArticuloTecnico`, cada uno con su `validar()` |
| **Observer** | `backend/app/patterns/observer/` | `GestorEventos` notifica a `NotificacionInternaObserver`, `CorreoModeradorObserver` y `RegistroAuditoriaObserver` mediante `actualizar()` |
| **Adapter** | `backend/app/patterns/storage/` | `IAlmacenamientoArchivos` con `LocalStorageAdapter` (por defecto) y `CloudinaryStorageAdapter` (`STORAGE_BACKEND=cloudinary`) |

## Decisiones técnicas y trade-offs

- **FastAPI async + PostgreSQL.** El prototipo maneja búsqueda, mapa y moderación con muchas lecturas simultáneas; el ORM async y el pool acotado (Singleton) evitan bloquear el event loop. PostgreSQL permite `unaccent`/`pg_trgm` y columnas JSONB para los atributos polimórficos de contenido y directorio. El coste es necesitar un servidor de base de datos en vez de un archivo SQLite.
- **React 19 + Tailwind 4.** El diseño exportado usa tokens CSS y tipografías autoalojadas; Tailwind 4 permite mantenerlos en `index.css` sin configuración adicional. Se prefirió JS sobre TS en el frontend del diseño para no alterar los componentes entregados.
- **Observer con `BackgroundTasks`.** Los observadores que escriben en base lo hacen en la transacción de la petición; sólo el correo simulado queda diferido. Así no se repitió el problema de `database is locked` que apareció en la versión anterior con una segunda conexión sobre SQLite.
- **Adapter local en demo, Cloudinary en producción.** El plan free de Render tiene disco efímero: `local` sirve para la clase, `cloudinary` persiste imágenes en producción.
- **Entornos.** `local` (Docker o script), `test` (base `cosplay_test`, se recrea en cada corrida) y `production` (Render + PostgreSQL administrado). Los secretos se leen de variables de entorno; `.env` está en `.gitignore`.

## Cloud computing, ética y normativa (criterios 3.1.1 y 3.1.2)

| Concepto | Uso en el prototipo |
|---|---|
| **SaaS** | Render (despliegue de API y sitio estático), PostgreSQL administrado (Neon/Render), GitHub Actions (CI), Cloudinary (opcional) |
| **IaaS** | No se administan máquinas virtuales ni redes; por eso no se usa IaaS directamente |
| **Cloud Computing** | La API y el frontend se despliegan por separado; la base es un servicio gestionado y las imágenes pueden delegarse a un CDN |

La confiabilidad se sostiene con migraciones, semillas idempotentes, pruebas automáticas, auditoría y respaldo del repositorio. El código sigue el **Código de Ética ACM/IEEE-CS**: no se publican datos personales reales, se respeta el opt-in del directorio y se documentan las limitaciones. Se aplican **ISO/IEC 27002** (A.8.3 y A.8.15), **OWASP Top 10** A01/A02/A03, la **Ley 19.223** de delitos informáticos y la **Ley 21.719** de protección de datos personales.

## Configuración

Todas las variables están en [`.env.example`](.env.example). El repositorio no contiene secretos. Para usar Neon, basta con apuntar `DATABASE_URL` a `postgresql+asyncpg://…`.

## Fuera de alcance (según el informe)

Pagos y transacciones, venta de entradas (solo enlaces externos), moderación automática de imágenes y prueba de carga para 10.000 usuarios. Tampoco se ejecutó OWASP ZAP: los controles A01/A02/A03 se verifican con pruebas unitarias y de integración, y la brecha queda registrada en la matriz de casos.
