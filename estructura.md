# Estructura de paquetes

Árbol real del repositorio tras integrar el diseño y su backend, con la responsabilidad de cada módulo y la regla de dependencia que lo mantiene ordenado.

## Árbol

```text
cosplay-chile/
├── .github/workflows/ci.yml       pytest + cobertura ≥90% y Vitest + build
├── .env.example                   variables de entorno (sin secretos)
├── .gitignore
├── README.md                      puesta en marcha, API, pruebas, decisiones y normativa
├── GUIA_DEMO.md                   guion para exponer la plataforma en clases
├── CORRECCIONES_ES3.md            criterio 3.1.5: 9 hallazgos con evidencia
├── estructura.md                  este archivo
├── docker-compose.yml             API + web + PostgreSQL
├── render.yaml                    despliegue de API y sitio estático
├── presentacion_3.docx            presentación de la Unidad 3
├── design/
│   └── Cosplay Chile — Frontend.html   diseño exportado (8 tableros, sin modificar)
├── docs/
│   ├── informe_requerimientos.pdf RF-01…RF-40 y RNF-01…RNF-11
│   ├── DECISIONES.md              decisiones técnicas y decisiones de diseño
│   ├── TRAZABILIDAD.md            estado de cada requerimiento
│   └── BRECHAS_DISENO.md          diferencias entre el diseño y la API
├── backend/
│   ├── .env.example
│   ├── alembic.ini
│   ├── pyproject.toml             pytest async + coverage con núcleo sysmon
│   ├── requirements.txt
│   ├── requirements-dev.txt       pytest, pytest-asyncio, httpx, pytest-cov
│   ├── alembic/
│   │   ├── env.py                 migraciones asíncronas
│   │   └── versions/0001_esquema_inicial.py
│   ├── app/
│   │   ├── main.py                compone routers, CORS, cabeceras y /media
│   │   ├── api/routers/           15 routers: auth, perfil, meta, archivos, contacto,
│   │   │                          contenidos, favoritos, notificaciones, moderación,
│   │   │                          directorio, eventos, reportes, comunidad, inicio, búsqueda
│   │   ├── core/                  configuración, deps (JWT/roles), seguridad argon2
│   │   ├── db/                    session_manager.py ← Singleton; base.py
│   │   ├── models/                entidades SQLAlchemy (tabla única para Contenido y DirectorioItem)
│   │   ├── patterns/
│   │   │   ├── contenido_factory.py      ← Factory Method
│   │   │   ├── observer/                 ← GestorEventos + 3 observadores
│   │   │   └── storage/                  ← Adapter local / Cloudinary
│   │   ├── schemas/               contratos Pydantic (pagina {items,total,pagina,paginas})
│   │   ├── services/              lógica de negocio por módulo
│   │   └── seed/                  datos demo + ilustraciones SVG propias
│   ├── scripts/
│   │   ├── dev.ps1                arranque local en Windows
│   │   └── recorrido_http.py      recorrido reproducible: 40/40 comprobaciones
│   └── tests/
│       ├── conftest.py            base de test, Alembic y limpieza por prueba
│       ├── casos_por_rf.md        matriz RF ↔ prueba (96 casos)
│       ├── test_auth.py           20 · registro/login/recuperación
│       ├── test_contenidos.py     11 · contents y descarga
│       ├── test_directorio_calendario.py  11 · directorio, mapa y eventos
│       ├── test_factory.py        13 · Factory Method
│       ├── test_comunidad_moderacion.py    8 · foros, desafíos y moderación
│       ├── test_busqueda_inicio.py 6 · portada y búsqueda
│       ├── test_observer.py       7 · Observer y bitácora
│       ├── test_patrones_base.py  8 · Singleton y Adapter
│       ├── test_cobertura_extra.py 7 · semillas y flujos adicionales
│       └── test_cobertura_final.py 5 · entrypoint, moderación, avisos y búsqueda
└── frontend/
    ├── package.json / package-lock.json   React 19, Tailwind 4, Leaflet, Vitest
    ├── vite.config.js             proxy /api y /media en desarrollo
    ├── public/
    └── src/
        ├── api/client.js           cliente REST y traducción de errores
        ├── App.jsx                 tabla de rutas (23 rutas, diseño aplicado)
        ├── assets/diseno/          ilustraciones del diseño (JPG propios)
        ├── components/
        │   ├── diseno/             Icono, Logo, Pestanas, Acordeon, Insignias
        │   ├── Layout.jsx          cabecera, pie, menú móvil y navegación
        │   ├── CampanaNotificaciones.jsx  avisos internos (RF-37)
        │   ├── BuscadorGlobal.jsx  autocompletado (RF-31)
        │   ├── SubirImagen.jsx     Adapter + texto alternativo obligatorio
        │   └── useApi.js, useFavoritos.js, Protegida.jsx
        ├── contexto/               AuthContext y MetaContext
        ├── pages/                  inicio, guías, directorio, calendario, comunidad,
        │                           desafíos, perfil, favoritos, búsqueda, seguridad,
        │                           contacto/privacidad y moderación
        ├── index.css               tokens de diseño, tipografías y componentes
        └── test/                   8 archivos · 59 pruebas de interfaz
```

## Responsabilidades por capa

| Capa | Hace | No hace |
|---|---|---|
| `models` | Define entidades y reglas de integridad de la base | No valida HTTP |
| `schemas` | Valida entradas y da forma a las salidas | No accede a la base |
| `repositories` / `services` | Consultas y lógica de negocio | No conocen FastAPI |
| `api/routers` | HTTP, permisos y códigos de estado | No contiene reglas de negocio |
| `patterns` | Singleton, Factory, Observer y Adapter transversales | No sustituyen a un servicio |
| `main.py` | Compone la aplicación | No contiene lógica de negocio |
| `frontend/src/api` | Comunicación con `/api` y errores en español | No decide diseño |
| `frontend/src/pages` | Pantallas del diseño | No implementan reglas de negocio |

## Dependencias entre capas

- `models` no importa nada de `schemas`, `services` ni `api`.
- `schemas` puede importar `models` para aliases y enums.
- `services` no importa nada de `api`.
- `api` puede importar todo lo anterior.
- `main.py` solo compone.

## Estado de la entrega

| Entregable | Estado | Evidencia |
|---|---|---|
| Diseño aplicado sin cambios | ✅ | `design/`, `frontend/src/components/diseno/`, 59 pruebas de interfaz |
| Prototipo funcional (35%) | ✅ | 60 rutas, 40/40 recorrido HTTP, 96 pruebas, 97% cobertura |
| Cuatro patrones del ES2 | ✅ | Factory, Observer, Adapter y Singleton con pruebas dedicadas |
| Criterios 3.1.1 y 3.1.2 | ✅ | README: SaaS/IaaS/Cloud, ética ACM/IEEE, Ley 19.223 y 21.719 |
| Criterio 3.1.5 | ✅ | `CORRECCIONES_ES3.md` con 9 hallazgos y evidencia |
| CI/CD y entornos | ✅ | `.github/workflows/ci.yml`, Render, local/test/production |
| Diagramas UML adaptativos e informe de testeo (ES4) | ⏳ | Aparcado a petición del usuario |
| OWASP ZAP y prueba de carga | ⏳ | Brechas documentadas en `backend/tests/casos_por_rf.md` |
