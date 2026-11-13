# Estructura de paquetes

Árbol real del repositorio al cierre del proyecto, con la responsabilidad de
cada módulo y la regla de dependencia que lo mantiene ordenado.

## Árbol

```
cosplay-chile/
├── .gitattributes
├── .gitignore
├── README.md                  puesta en marcha, API, despliegue y trazabilidad
├── GUIA_DEMO.md               guion para exponer la plataforma en clases
├── estructura.md              este archivo
├── render.yaml                dos servicios: API + sitio estático
├── backend/
│   ├── .env.example
│   ├── alembic.ini
│   ├── pytest.ini
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   └── app/
│       ├── __init__.py
│       ├── main.py            fábrica de la aplicación FastAPI
│       ├── api/
│       │   ├── __init__.py
│       │   ├── deps.py        sesión, usuario actual y control de roles
│       │   └── routes/
│       │       ├── health.py       GET /health
│       │       ├── auth.py         registro, login, /me y /privacidad
│       │       ├── admin.py        panel: métricas, editorial, eventos, foro, desafíos, comunidad
│       │       ├── proveedores.py  US-13 directorio
│       │       ├── contenido.py    US-08 contenido editorial
│       │       ├── eventos.py      calendario y participaciones
│       │       ├── comunidad.py    foro y desafíos mensuales
│       │       ├── perfiles.py     perfil público de cosplayer
│       │       └── directorio.py   tiendas y grupos
│       ├── core/
│       │   ├── config.py       Settings desde variables de entorno
│       │   ├── database.py     DatabaseSessionManager (Singleton) y get_db
│       │   ├── security.py     bcrypt y JWT
│       │   └── privacidad.py   texto y versión de la política
│       ├── models/
│       │   ├── base.py         Base declarativa y marcas de tiempo
│       │   ├── usuario.py      Usuario, PerfilCosplayer
│       │   ├── contenido.py    Contenido y sus tres subtipos
│       │   ├── evento.py       EventoCosplay, ParticipacionEvento
│       │   ├── directorio.py   Proveedor, DondeComprar, ComunidadGrupo
│       │   ├── comunidad.py    ForoTema, ForoRespuesta, DesafioMensual
│       │   └── intento_login.py contador para el bloqueo por fuerza bruta
│       ├── repositories/
│       │   ├── usuario.py      consultas de usuarios
│       │   ├── intento_login.py consultas de intentos
│       │   ├── proveedor.py    consultas del directorio
│       │   ├── contenido.py    consultas editoriales
│       │   ├── evento.py       eventos y participaciones
│       │   ├── comunidad.py    temas, respuestas y desafíos
│       │   ├── perfil.py       alta y actualización del perfil
│       │   ├── directorio.py   tiendas y grupos
│       │   └── admin.py        conteos y temas ocultos (solo panel)
│       ├── schemas/
│       │   ├── auth.py         entrada y salida de autenticación
│       │   ├── proveedor.py    fichas del directorio
│       │   ├── contenido.py    guías, entrevistas y artículos
│       │   ├── evento.py       eventos y participaciones
│       │   ├── comunidad.py    foro y desafíos
│       │   ├── perfil.py       perfil público
│       │   ├── directorio.py   tiendas y grupos
│       │   └── admin.py        resumen y entradas del panel
│       ├── services/
│       │   ├── auth.py         registro, login y política de bloqueo
│       │   ├── proveedor.py    reglas del directorio
│       │   ├── contenido.py    ciclo editorial
│       │   ├── evento.py       inscripciones y reglas del calendario
│       │   ├── comunidad.py    reglas del foro y de los desafíos
│       │   ├── perfil.py       reglas del perfil público
│       │   └── admin.py        transiciones editoriales, moderación y altas
│       ├── factories/
│       │   └── contenido_factory.py  crea el subtipo correcto de Contenido
│       └── seed/
│           ├── proveedores.py  20 fichas reales del directorio
│           ├── categorias.py   5 categorías de contenido
│           ├── datos_base.py   orquestador idempotente para producción
│           └── demo.py         cuentas y contenido para la demo en clases
│   ├── migrations/
│   │   ├── env.py
│   │   ├── script.py.mako
│   │   └── versions/
│   │       ├── 0001_esquema_inicial.py
│   │       └── 0002_intentos_login.py
│   ├── tests/
│   │   ├── conftest.py               esquema por Alembic y limpieza por prueba
│   │   ├── casos_por_rf.md           matriz de casos por requerimiento (EV4)
│   │   ├── test_config.py
│   │   ├── test_singleton.py
│   │   ├── test_health.py
│   │   ├── test_migraciones.py
│   │   ├── test_seguridad.py
│   │   ├── test_registro.py
│   │   ├── test_login.py
│   │   ├── test_autorizacion.py
│   │   ├── test_proveedores.py
│   │   ├── test_contenido.py
│   │   ├── test_modulos_nuevos.py    eventos, foro, desafíos, perfiles, catálogos
│   │   ├── test_panel_admin.py       permisos, resumen, editorial, moderación y altas
│   │   └── test_semilla_demo.py      idempotencia y bloqueo en producción
│   └── exp/                          apuntes de exploración, no es código del producto
└── frontend/
    ├── index.html                    documento raíz, lang="es-CL"
    ├── vite.config.ts                Tailwind y proxy hacia el backend
    ├── .env.example
    └── src/
        ├── main.tsx                  monta React, el router y el proveedor de sesión
        ├── App.tsx                   tabla de rutas (17 páginas)
        ├── index.css                 tokens del sistema de diseño (@theme)
        ├── lib/
        │   ├── api.ts                cliente HTTP y tipos del backend
        │   ├── auth.tsx              ProveedorAuth (solo el componente)
        │   ├── contextoAuth.ts       contexto y hook useAuth
        │   ├── contenido.ts          etiquetas y tonos del contenido
        │   ├── etiquetas.ts          etiquetas del directorio
        │   ├── modulos.ts            cliente y tipos de los seis módulos nuevos
        │   └── admin.ts              cliente y tipos del panel de administración
        ├── components/
        │   ├── ui/                   Boton, Campo, Tarjeta, Etiqueta
        │   ├── layout/               Disposicion, Encabezado, Pie
        │   ├── home/                 Portada, Modulos, Pasos
        │   └── directorio/           PanelFiltros, TarjetaProveedor
        └── pages/
            ├── InicioPagina.tsx
            ├── DirectorioPagina.tsx
            ├── ContenidoPagina.tsx
            ├── ContenidoDetallePagina.tsx
            ├── EditorContenidoPagina.tsx
            ├── EventosPagina.tsx
            ├── EventoDetallePagina.tsx
            ├── ForoPagina.tsx
            ├── TemaDetallePagina.tsx
            ├── DesafiosPagina.tsx
            ├── ComunidadPagina.tsx
            ├── PerfilPagina.tsx
            ├── AdminPagina.tsx       panel por pestañas, solo rol administrador
            ├── RegistroPagina.tsx
            ├── IngresarPagina.tsx
            ├── PrivacidadPagina.tsx
            └── NoEncontradaPagina.tsx
```

Los tokens viven en `src/index.css`, en el bloque `@theme` de Tailwind 4. Un
componente no escribe colores hexadecimales sueltos: si hace falta un color
nuevo, se declara ahí y se usa por nombre (por ejemplo `--color-exito-100`).

## Responsabilidad de cada capa

| Capa | Qué hace | Qué no hace |
|---|---|---|
| `app/core` | configuración, motor de base de datos, criptografía | no conoce reglas de negocio ni rutas |
| `app/models` | mapeo objeto-relacional y restricciones | no valida datos de entrada |
| `app/schemas` | validación y forma de los datos que entran y salen | no consulta la base |
| `app/repositories` | consultas SQL, una función por caso de uso | no decide reglas ni códigos HTTP |
| `app/services` | reglas de negocio y transacciones | no conoce HTTP ni serializa |
| `app/api/routes` | contrato HTTP: rutas, códigos, dependencias | no escribe SQL ni decide reglas |
| `app/factories` | construye la entidad correcta según el tipo | no valida ni persiste |
| `app/seed` | carga datos iniciales de forma idempotente | no define reglas de negocio |
| `migrations` | evolución del esquema | no crea datos de negocio |
| `tests` | verifica criterios de aceptación | no depende de servicios externos |

## Regla de dependencia

```
routes ──▶ services ──▶ repositories ──▶ models ──▶ base
   │            │
   └────────────┴────▶ core ──▶ config
```

La flecha significa «puede importar». Se cumple en un solo sentido:

- `models` no importa nada de `api`, `services` ni `repositories`.
- `repositories` no importa nada de `services` ni de `api`.
- `services` no importa nada de `api`.
- `api` puede importar todo lo anterior.
- `main.py` solo compone: no contiene lógica.

Si aparece un import que va contra la flecha, la solución no es moverlo: es
crear la capa que falta, no romper el orden.

## Por qué existe cada capa nueva

Las capas `schemas`, `services` y `repositories` no existían al cierre del
Sprint 1. Se crearon en US-04a porque el registro y el login tienen tres
responsabilidades que no pueden convivir en un endpoint:

1. **Validar** el cuerpo de la petición (Pydantic, `schemas`).
2. **Decidir** cuándo una credencial es válida y cuándo hay que bloquear
   (`services`).
3. **Consultar** la base sin mezclar SQL con reglas (`repositories`).

Los módulos de comunidad posteriores reutilizaron exactamente el mismo corte
vertical: un esquema, un repositorio, un servicio y un router por dominio. Por
eso las tablas que ya estaban en `0001_esquema_inicial.py` (eventos, foro,
desafíos, perfil, tiendas, grupos) pudieron activarse sin tocar el esquema ni
añadir una migración nueva.

El panel siguió el mismo corte (`schemas/admin.py`, `repositories/admin.py`,
`services/admin.py`, `routes/admin.py`) con una salvedad de seguridad: su
repositorio es **aparte** del público. La bandeja editorial necesita ver
borradores y temas ocultos, mientras que `repositories/contenido.py` y
`repositories/comunidad.py` los filtran a propósito. Poner una bandera
`incluir_ocultos` en esos repositorios dejaría un interruptor olvidable en
código que también sirve a visitantes anónimos.

## Estado de las historias

| Historia | Estado | Archivos |
|---|---|---|
| US-01 infraestructura | ✅ | `app/core/`, `migrations/`, `render.yaml` |
| US-04a registro, login, roles, hash y JWT | ✅ | `app/api/routes/auth.py`, `app/services/auth.py` |
| US-02 landing y navegación | ✅ | `frontend/src/App.tsx`, `components/layout/`, `components/home/` |
| US-13 directorio | ✅ | `app/api/routes/proveedores.py`, `frontend/src/pages/DirectorioPagina.tsx` |
| US-08 contenido editorial | ✅ | `app/api/routes/contenido.py`, `app/factories/contenido_factory.py` |
| Calendario de eventos | ✅ | `app/api/routes/eventos.py`, `frontend/src/pages/EventosPagina.tsx` |
| Foro y desafíos | ✅ | `app/api/routes/comunidad.py`, `frontend/src/pages/ForoPagina.tsx` |
| Perfil y complementos del directorio | ✅ | `app/api/routes/{perfiles,directorio}.py` |
| Panel de administración | ✅ | `app/api/routes/admin.py`, `app/services/admin.py`, `frontend/src/pages/AdminPagina.tsx` |
| EV4 pruebas funcionales y trazabilidad | ✅ | `tests/test_modulos_nuevos.py`, `tests/test_panel_admin.py`, `tests/test_semilla_demo.py`, `tests/casos_por_rf.md` |

## Correspondencia con la vista de desarrollo

| Paquete | Componente del diagrama |
|---|---|
| `app/api` | API REST |
| `app/core` | Gestor de configuración y acceso a datos |
| `app/models` | Modelo de dominio |
| `migrations` | Esquema de base de datos |
| `app/seed` | Carga inicial de datos |
| `frontend/src` | Cliente React + Tailwind |

## Convenciones

- Nombres de tablas y columnas en singular y `snake_case`.
- Identificadores primarios con prefijo del dominio: `id_usuario`, `id_evento`.
- Claves foráneas con el mismo nombre que la columna referenciada.
- Enumeraciones declaradas como constante en el módulo del modelo y aplicadas
  en la columna con `Enum(..., native_enum=False)`.
- Validación de entrada en `schemas` con Pydantic, no en los modelos.
- Una función por consulta en `repositories`; nada de SQL en los endpoints.
- Las excepciones de dominio se declaran en `services` y se traducen a códigos
  HTTP en `routes`.
- Las rutas literales se registran antes que las que capturan un UUID.
- Los listados devuelven `total` y `elementos`; los paginados añaden `limite` y
  `desplazamiento`.
