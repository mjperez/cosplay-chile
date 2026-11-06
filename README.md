# Cosplay Chile — API

Backend de la plataforma de contenidos, directorio y comunidad para el cosplay
chileno. Proyecto de TI3043, Ingeniería de Software, INACAP.

**Estado:** US-01 (infraestructura), US-04a (registro, login, roles, hash y
JWT), US-03 (sistema de diseño, lado Tailwind) y US-02 (landing y navegación)
implementadas y verificadas contra la base real. 59 pruebas de backend en verde,
lint y compilación del frontend sin advertencias.

---

## Requisitos

- Python 3.13
- PostgreSQL 17 (Supabase en la nube, o local para desarrollo)
- Git

## Puesta en marcha

```bash
git clone https://github.com/mjperez/ti3043-cosplay-chile.git
cd ti3043-cosplay-chile/backend

python -m venv .venv
source .venv/Scripts/activate      # Windows (Git Bash)
# source .venv/bin/activate        # Linux y macOS

pip install -r requirements-dev.txt

cp .env.example .env
# completar DATABASE_URL y JWT_SECRET
```

Generar el secreto de JWT:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

## Base de datos

Aplicar el esquema:

```bash
alembic upgrade head
```

Ver el historial de migraciones:

```bash
alembic history
alembic current
```

Revertir todo:

```bash
alembic downgrade base
```

### Nota sobre el proveedor de base de datos

El informe de la asignatura describe el despliegue con **Neon**. La
implementación corre sobre **Supabase**, porque el proyecto de Neon se dio de
baja antes de la puesta en marcha.

El cambio no afecta al diseño: ambos son PostgreSQL 17, el esquema no usa
ninguna extensión específica de proveedor y la cadena de conexión se toma de
`DATABASE_URL`. Cambiar de proveedor es cambiar una variable de entorno, sin
tocar código ni migraciones.

La nota queda aquí y no en el informe porque el informe ya está entregado. El
repositorio es la fuente de verdad sobre lo que efectivamente corre.

## Ejecutar

```bash
uvicorn app.main:app --reload
```

| Ruta | Qué es |
|---|---|
| `GET /health` | estado del servicio y de la base |
| `GET /docs` | documentación interactiva |
| `POST /api/v1/auth/registro` | crear cuenta |
| `POST /api/v1/auth/login` | obtener token |
| `GET /api/v1/auth/me` | datos del usuario del token |
| `GET /api/v1/privacidad` | versión vigente de la política |
| `GET /api/v1/admin/usuarios` | listado de cuentas (solo administrador) |
| `GET /api/v1/proveedores` | directorio con filtros y paginación |
| `GET /api/v1/proveedores/opciones` | regiones y tipos con fichas cargadas |

## Datos semilla

```bash
python -m app.seed.proveedores
```

Carga las 20 fichas del directorio. Es idempotente y correctiva: crea las que
faltan y arregla las que cambiaron, sin duplicar. El origen de cada ficha está
documentado en `app/seed/proveedores.py`: salen del levantamiento de
requerimientos, no de una lista inventada. Solo se guarda lo que la cuenta
publica abiertamente (nombre comercial, tipo, región cuando corresponde,
usuario y sitio web); no hay correos ni teléfonos.

Once fichas declaran región: Metropolitana (7), Antofagasta, Valparaíso,
Coquimbo y Arica y Parinacota. Las otras nueve quedan sin región por dos
motivos distintos, ambos deliberados:

- **Tres tiendas solo venden online** (MotorLaser, Tienda Deck, FukuBox), así
  que no tienen una región de atención presencial que declarar.
- **Cinco cosmakers y un sastre son personas naturales.** Publicar su ubicación
  es un riesgo de doxxing y no aporta a la función del directorio, que es
  encontrar un servicio. La región se publica para negocios con dirección
  comercial, no para individuos.

## Frontend

```bash
cd frontend
npm install
npm run dev
```

Queda en http://localhost:5173. El `vite.config.ts` redirige `/api` y `/health`
al backend en el puerto 8000, así que en desarrollo no hace falta configurar
CORS ni variables.

| Script | Qué hace |
|---|---|
| `npm run dev` | servidor de desarrollo con recarga en caliente |
| `npm run build` | compila TypeScript y genera `dist/` |
| `npm run lint` | oxlint |
| `npm run preview` | sirve `dist/` para probar la compilación |

Páginas implementadas: inicio, registro, ingreso, política de privacidad y 404.

## Pruebas

```bash
pytest
```

Corren sobre SQLite en un directorio temporal, con el esquema aplicado por la
misma migración que se usa en producción. No tocan la base de desarrollo.

## Despliegue en Render

`render.yaml` está en la raíz del repositorio con `rootDir: backend`. Al
conectar el repositorio, Render lee el archivo y crea el servicio con
despliegue automático desde `main`.

Variables que se cargan a mano en el panel:

| Variable | Valor |
|---|---|
| `DATABASE_URL` | cadena del pooler de Supabase, con `sslmode=require` |
| `JWT_SECRET` | la genera Render (`generateValue: true`) |

## Flujo de ramas

| Rama | Uso | Despliegue |
|---|---|---|
| `main` | código desplegable | automático en Render |
| `dev` | integración del sprint | manual |

---

## Decisiones de implementación

**Singleton con `__new__` y lock.** El gestor de sesiones no es una variable de
módulo: se sobreescribe `__new__`, que es el punto donde Python decide si
instancia. Así dos importaciones distintas no pueden construir dos motores. El
lock con doble verificación cubre el arranque concurrente.

**Tipos portables en lugar de tipos nativos de PostgreSQL.** `Uuid`, `JSON` y
`Enum` sin tipo nativo compilan a `UUID`, `JSON` y `VARCHAR` en PostgreSQL, y a
`CHAR(32)`, `JSON` y `VARCHAR` en SQLite. Eso permite correr la migración
completa en las pruebas sin levantar un servidor.

**`/health` devuelve 503 cuando la base no responde.** Render usa esa ruta para
decidir si enruta tráfico. Un 200 con la base caída mandaría peticiones a un
proceso que no puede atenderlas. En producción el mensaje del driver se
reemplaza por uno genérico para no filtrar host, puerto ni usuario.

**Herencia de tabla unida para `Contenido`.** El diagrama de clases declara una
clase abstracta con tres subclases. En la base se traduce a una tabla base más
una tabla por subtipo que comparte la clave primaria. Deja la creación a cargo
de la fábrica de US-08.

**El bloqueo por intentos vive en la base, no en memoria.** Un diccionario en
memoria se pierde al reiniciar y da un contador distinto por cada worker de
uvicorn. La tabla `intento_login` lo persiste y permite auditar.

**El rol se lee de la base, no del token.** `requiere_roles` consulta el rol
actual del usuario. Así revocar un permiso surte efecto de inmediato, sin
esperar a que venza el token emitido.

**El intento fallido se confirma antes de responder 401.** El endpoint va a
devolver un error y la sesión se revertiría al salir. Si el intento no se
confirmara ahí, el contador de bloqueo nunca avanzaría.

**`password_hash` y consentimiento existen desde la primera migración.** No son
parte del alcance de US-01, pero la tabla `usuario` sin ellos obligaría a una
segunda migración sobre la misma entidad en US-04a.

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
| Credenciales inválidas dan 401 sin revelar si el correo existe | `app/api/routes/auth.py`, `app/services/auth.py` | `test_login.py::test_correo_inexistente_responde_igual_que_contrasena_incorrecta` |
| Consentimiento con fecha y versión | `app/models/usuario.py`, `app/core/privacidad.py` | `test_registro.py::test_el_consentimiento_queda_con_fecha_y_version` |
| Sesión persiste tras recargar; token vencido da 401 | `app/core/security.py`, `app/api/deps.py` | `test_autorizacion.py::test_el_token_sirve_en_varias_peticiones` y `test_token_vencido_devuelve_401` |
| Rol sin permisos recibe 403 en administración | `app/api/deps.py` | `test_autorizacion.py::test_usuario_normal_recibe_403_en_endpoints_de_administracion` |
| 5 intentos fallidos en 15 min bloquean el login | `app/services/auth.py`, `app/models/intento_login.py` | `test_login.py::test_cinco_fallos_bloquean_el_login` |

**Nota sobre el criterio del rol.** El criterio dice «un usuario con rol
`usuario`». El modelo de actores del informe define ocho roles (visitante,
cosplayer, cosmaker, sastre, tienda, fotógrafo, organizador, administrador) y
no incluye `usuario`. La prueba usa `cosplayer`, que es el rol por defecto de
una cuenta nueva. El comportamiento es el mismo para los siete roles que no son
`administrador`.

---

## Limitaciones conocidas

- **El registro revela si un correo existe** (409). Es inevitable si se quiere
  dar un mensaje útil, y no permite probar contraseñas.
- **No hay refresh token.** Al vencer el token (60 min por defecto) hay que
  volver a iniciar sesión.
- **El bloqueo es por correo, no por IP.** Un atacante puede bloquear la cuenta
  de otra persona a propósito. Se mitiga con la ventana de 15 minutos.
- **Las pantallas de registro y login (T-04.5) no están en este repositorio.**
  Dependen del armazón de frontend que crea US-02.
