# Estructura de paquetes

Árbol real del repositorio al cierre del Sprint 2, con la responsabilidad de
cada módulo y la regla de dependencia que lo mantiene ordenado.

## Árbol

```
ti3043-cosplay-chile/
├── .gitattributes
├── .gitignore
├── README.md
├── estructura.md
├── render.yaml
└── backend/
    ├── .env.example
    ├── alembic.ini
    ├── pytest.ini
    ├── requirements.txt
    ├── requirements-dev.txt
    ├── app/
    │   ├── __init__.py
    │   ├── main.py                  fábrica de la aplicación FastAPI
    │   ├── api/
    │   │   ├── __init__.py
    │   │   ├── deps.py              sesión, usuario actual y control de roles
    │   │   └── routes/
    │   │       ├── __init__.py
    │   │       ├── health.py        GET /health
    │   │       ├── auth.py          registro, login, /me y /privacidad
    │   │       └── admin.py         listado de cuentas (solo administrador)
    │   ├── core/
    │   │   ├── __init__.py
    │   │   ├── config.py            Settings desde variables de entorno
    │   │   ├── database.py          DatabaseSessionManager (Singleton) y get_db
    │   │   ├── security.py          bcrypt y JWT
    │   │   └── privacidad.py        texto y versión de la política
    │   ├── models/
    │   │   ├── __init__.py          reexporta todos los modelos
    │   │   ├── base.py              Base declarativa y marcas de tiempo
    │   │   ├── usuario.py           Usuario, PerfilCosplayer
    │   │   ├── contenido.py         Contenido y sus tres subtipos
    │   │   ├── evento.py            EventoCosplay, ParticipacionEvento
    │   │   ├── directorio.py        Proveedor, DondeComprar, ComunidadGrupo
    │   │   ├── comunidad.py         ForoTema, ForoRespuesta, DesafioMensual
    │   │   └── intento_login.py     contador para el bloqueo por fuerza bruta
    │   ├── repositories/
    │   │   ├── __init__.py
    │   │   ├── usuario.py           consultas de usuarios
    │   │   └── intento_login.py     consultas de intentos
    │   ├── schemas/
    │   │   ├── __init__.py
    │   │   └── auth.py              entrada y salida de autenticación
    │   └── services/
    │       ├── __init__.py
    │       └── auth.py              registro, login y política de bloqueo
    ├── migrations/
    │   ├── env.py
    │   ├── script.py.mako
    │   └── versions/
    │       ├── 0001_esquema_inicial.py
    │       └── 0002_intentos_login.py
    ├── tests/
    │   ├── conftest.py              esquema por Alembic y limpieza por prueba
    │   ├── test_config.py
    │   ├── test_singleton.py
    │   ├── test_health.py
    │   ├── test_migraciones.py
    │   ├── test_seguridad.py
    │   ├── test_registro.py
    │   ├── test_login.py
    │   └── test_autorizacion.py
    └── exp/                         apuntes de exploración, no es código del producto
```

## Frontend

```
frontend/
├── index.html                     documento raíz, lang="es-CL"
├── vite.config.ts                 plugin de Tailwind y proxy hacia el backend
├── .env.example
└── src/
    ├── main.tsx                   monta React, el router y el proveedor de sesión
    ├── App.tsx                    tabla de rutas
    ├── index.css                  tokens del sistema de diseño (@theme)
    ├── lib/
    │   ├── api.ts                 cliente HTTP y tipos del backend
    │   ├── auth.tsx               ProveedorAuth (solo el componente)
    │   └── contextoAuth.ts        contexto y hook useAuth
    ├── components/
    │   ├── ui/
    │   │   ├── Boton.tsx          variantes primario, secundario y fantasma
    │   │   ├── Campo.tsx          etiqueta, ayuda y error accesibles
    │   │   ├── Tarjeta.tsx
    │   │   └── Etiqueta.tsx       badge
    │   ├── layout/
    │   │   ├── Disposicion.tsx    armazón con enlace de salto
    │   │   ├── Encabezado.tsx     navegación y sesión
    │   │   └── Pie.tsx
    │   └── home/
    │       ├── Portada.tsx
    │       ├── Modulos.tsx
    │       └── Pasos.tsx
    └── pages/
        ├── InicioPagina.tsx
        ├── RegistroPagina.tsx
        ├── IngresarPagina.tsx
        ├── PrivacidadPagina.tsx
        └── NoEncontradaPagina.tsx
```

Los tokens viven en `src/index.css`, en el bloque `@theme` de Tailwind 4. Un
componente no escribe colores hexadecimales sueltos: si hace falta un color
nuevo, se declara ahí y se usa por nombre.

## Responsabilidad de cada capa

| Capa | Qué hace | Qué no hace |
|---|---|---|
| `app/core` | configuración, motor de base de datos, criptografía | no conoce reglas de negocio ni rutas |
| `app/models` | mapeo objeto-relacional y restricciones | no valida datos de entrada |
| `app/schemas` | validación y forma de los datos que entran y salen | no consulta la base |
| `app/repositories` | consultas SQL, una función por caso de uso | no decide reglas ni códigos HTTP |
| `app/services` | reglas de negocio y transacciones | no conoce HTTP ni serializa |
| `app/api/routes` | contrato HTTP: rutas, códigos, dependencias | no escribe SQL ni decide reglas |
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

## Dónde entra el código de los próximos sprints

| Sprint | Historia | Archivos previstos |
|---|---|---|
| 2 | US-13 directorio | `app/api/routes/proveedores.py`, `app/schemas/proveedor.py`, `app/repositories/proveedor.py`, `app/services/proveedor.py` |
| 2 | US-02 landing | fuera de este repositorio: va en el frontend React |
| 3 | US-08 contenido editorial | `app/api/routes/contenido.py`, `app/factories/contenido_factory.py`, `app/schemas/contenido.py` |
| 4 | EV4 pruebas | `tests/funcionales/`, `tests/casos_por_rf.md` |

## Correspondencia con la vista de desarrollo

| Paquete | Componente del diagrama |
|---|---|
| `app/api` | API REST |
| `app/core` | Gestor de configuración y acceso a datos |
| `app/models` | Modelo de dominio |
| `migrations` | Esquema de base de datos |
| frontend (repositorio aparte) | Cliente React + Tailwind |

## Convenciones

- Nombres de tablas y columnas en singular y `snake_case`.
- Identificadores primarios con prefijo del dominio: `id_usuario`, `id_evento`.
- Claves foráneas con el mismo nombre que la columna referenciada.
- Enumeraciones declaradas como constante en el módulo del modelo y aplicadas
  en la columna con `Enum(..., native_enum=False)`.
- Validación de entrada en `schemas` con Pydantic, no en los modelos.
- Una función por consulta en `repositories`; nada de SQL en los endpoints.
