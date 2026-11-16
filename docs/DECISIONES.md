# Registro de decisiones

Fuente de verdad: `docs/informe_requerimientos.pdf`. Cuando el informe es ambiguo o se contradice, se elige
la opción más simple y se registra aquí. Formato: **D-NN · tema** — contexto → decisión.

## Inconsistencias del informe

- **D-01 · Modelo de clases (Fig. 11) frente al ER (Fig. 18).** El ER tiene `BlogTema` sin `Foro`, una relación
  N:M `DondeComprar`–`Proveedor` y una tabla `PerfilCosplayer`. → Se sigue la **estructura del diagrama de
  clases**: Foro→Tema→Respuesta (composición), `DirectorioItem` con herencia de tabla única
  (`ProveedorServicio`, `Tienda`, `ComunidadGrupo`) y `Perfil` 1:1. Del ER se toman los **atributos útiles**:
  comuna, dirección, sitio web, envía a Chile, activo, fecha inicio/fin, región del evento, especialidad y
  disponibilidad del perfil. La N:M Tienda–Proveedor se omite porque ningún RF la usa.
- **D-02 · Participaciones.** Se incluye `ParticipacionEvento` del ER (botón «Asistiré») y se agrega
  `ParticipacionDesafio`, que RF-36 necesita (la nota de la Fig. 18 dice que un usuario participa en muchos desafíos).
- **D-03 · Nombre de la subclase de artículo.** La Fig. 11 dice `Articulo`; la sección de patrones (págs. 29-30)
  dice `ArticuloTecnico`. → `ArticuloTecnico`.
- **D-04 · Nivel y categoría.** La nota de la Fig. 11 dice que `CategoriaContenido` clasifica «por temática y nivel»,
  pero `Contenido` ya tiene el atributo `nivel`. → `nivel` (PRINCIPIANTE/INTERMEDIO/AVANZADO) es un atributo de
  `Contenido` y `CategoriaContenido` es el tema. Se filtra por ambos.
- **D-05 · Quién valida la categoría.** En la secuencia (Fig. 13) la valida la Factory; en la comunicación
  (Fig. 14), `GuiaTutorial`. → La valida `ContenidoFactory`. Mensaje: «Categoría no encontrada» (Tabla 6 y Fig. 13),
  no «Categoría inválida» (Fig. 15).
- **D-06 · Descarga de tutoriales (RF-06).** La Fig. 6 la dibuja como extensión pública, pero su nota dice
  «exclusiva para usuarios registrados». → Requiere sesión. Formato: HTML autocontenido e imprimible a PDF.
- **D-07 · Búsqueda de proveedores.** La Fig. 3 la asocia solo al Usuario Registrado; el texto (pág. 33) y la Fig. 7,
  también al Visitante. → Pública.
- **D-08 · Registro (flujo 3a de UC-01).** «Al completarlo, el flujo continúa en el paso 4». → Tras registrarse, el
  usuario queda con sesión iniciada (se entrega el JWT).
- **D-09 · Contenido de la Fig. 11: `calificar()`** y el componente «Comentarios o evaluación de guías» (Fig. 16) no
  corresponden a ningún RF. → No se implementan (queda anotado en la trazabilidad).

## Supuestos del prototipo

- **D-10 · Roles.** `rol` ∈ {USUARIO, ADMIN}. ADMIN representa al actor «Administrador/Moderador». Cosplayer,
  cosmaker, tienda, etc. son `Perfil.tipo_perfil` (nota de la Fig. 3).
- **D-11 · Cuenta suspendida (excepción 2 de UC-01).** Se responde **403** con `codigo: CUENTA_SUSPENDIDA` y un enlace
  al formulario de contacto, **solo si la contraseña es correcta**; con una contraseña incorrecta se responde el mismo
  401 «Datos incorrectos», para no revelar qué cuentas existen. Un token vigente de una cuenta que luego se suspende
  deja de servir.
- **D-12 · Recuperación de contraseña.** Token aleatorio de un solo uso, válido por 30 minutos, guardado como hash
  SHA-256. El correo es **simulado**: se escribe en el log del backend. La respuesta es siempre la misma, exista o
  no el correo.
- **D-13 · Privacidad (RNF-11).** El consentimiento es obligatorio y se guarda su fecha (`consentimiento_at`); la
  finalidad se declara en el formulario de registro y en `/privacidad`. Para el derecho a supresión, «Eliminar mi
  cuenta» anonimiza los datos personales y borra favoritos y notificaciones; las publicaciones quedan como «Usuario
  eliminado».
- **D-14 · Opt-in al directorio (RF-10).** La casilla viene desmarcada. Si un perfil prestador (cosmaker, sastre,
  modelador, pintor, peluquero, maquillador, fotógrafo) o de tienda la activa, se crea una ficha vinculada en el
  directorio. Si la desactiva, la ficha se oculta (no se borra).
- **D-15 · Observer en segundo plano.** Los observers corren con `BackgroundTasks` de FastAPI, en paralelo
  (`asyncio.gather`, el Fork/Join de la Fig. 15). Cada uno abre su propia sesión desde el Singleton. Si un observer
  falla, se registra en el log sin afectar a los demás ni a la respuesta. `CorreoModeradorObserver` escribe en el
  log. `RegistroAuditoriaObserver` guarda en `registro_auditoria`, que se ve en el panel de moderación.
- **D-16 · Notificaciones masivas (RF-37).** Cuando se publican una guía, un evento o un desafío, se notifica a todos
  los usuarios activos con un único `INSERT … SELECT`, sin un bucle por usuario.
- **D-17 · Almacenamiento (Adapter).** `LocalStorageAdapter` es el predeterminado: guarda en `backend/media` y sirve
  en `/media`. `CloudinaryStorageAdapter` está implementado y probado con un SDK falso; se activa con
  `STORAGE_BACKEND=cloudinary`. Solo se aceptan JPG, PNG y WebP, detectados por su firma binaria, con un máximo de
  5 MB (excepción 2 de UC6).
- **D-18 · Regiones.** Las 16 regiones oficiales, como códigos (RM, BI, …). «Concepción» (RF-11) corresponde a la
  Región del Biobío. La búsqueda también reconoce nombres de capitales regionales.
- **D-19 · Imágenes del seed (RNF-10).** No se usan fotos de personas reales, por derechos de imagen. Se generan
  ilustraciones SVG propias con diversidad de tonos de piel, contexturas, géneros y ayudas técnicas (silla de
  ruedas, bastón), cada una con su texto alternativo.
- **D-20 · Datos ficticios.** Los negocios, comunidades y eventos del seed son inventados y usan el dominio
  reservado `.example`, para no suplantar marcas reales. Las fechas de los eventos se calculan relativas al día en
  que se carga el seed, para que la demo siempre tenga eventos próximos.
- **D-21 · Sesión en el frontend.** El JWT dura 60 minutos y se guarda en `localStorage`. Es aceptable para el
  prototipo; en producción convendría usar una cookie `HttpOnly`. Queda como deuda técnica.
- **D-22 · Frontend en JavaScript (JSX).** El informe pide React + Tailwind sin especificar el lenguaje. Se usa JSX sin
  TypeScript para acelerar el prototipo.
- **D-23 · Enumerados como VARCHAR + CHECK** en lugar de ENUM nativo de PostgreSQL, porque es más simple de migrar.
- **D-24 · Búsqueda global (RF-31).** PostgreSQL con `unaccent` + `pg_trgm` e índices GIN trigram sobre
  `f_unaccent(lower(col))` (función envoltorio IMMUTABLE). No se usa un motor externo.
- **D-25 · Escalabilidad (RNF-04).** No se prueba carga. Se diseñó para escalar: API async, pool acotado en el
  Singleton, paginación en todos los listados, índices por región y por estado + fecha.

## Entorno de desarrollo

- **D-26 · Sin Docker en la máquina de desarrollo.** Se entrega `docker-compose.yml` (comando único del README), pero
  el desarrollo y las pruebas corrieron contra el PostgreSQL nativo de la máquina (el servicio se llama
  `postgresql-x64-15`, pero el servidor es **PostgreSQL 18.7**), con el rol `cosplay` y las bases `cosplay` y
  `cosplay_test`. **El `docker-compose.yml` no pudo probarse en este equipo.**
- **D-27 · `psql.exe` del equipo no arranca** (falta una DLL, código 0xC0000135). Toda la administración de la base
  se hizo con `asyncpg` desde Python.
- **D-28 · Pruebas.** pytest recrea el esquema de `cosplay_test` con la **migración real de Alembic** al inicio de
  cada corrida y vacía las tablas antes de cada prueba. Nunca toca la base de desarrollo (hay un `assert` que lo
  impide).

## Decisiones tomadas durante la implementación

- **D-29 · Endpoint de reportes en la Fase 3.** RF-17 («reportar eventos») pertenece a la Fase 3, pero los
  reportes son de la Fase 4 (RF-38). → Se creó un único `POST /api/reportes` genérico en la Fase 3; el panel que
  los resuelve llegó en la Fase 4.
- **D-30 · Acciones de moderación sobre un reporte.** Descartar, Resolver (sin sanción; p. ej. evento corregido),
  Ocultar, u Ocultar y suspender al autor. Ocultar no borra nada: cambia el estado (`OCULTO`, `activo=false`,
  `oculta`/`oculto=true`). Moderación no puede suspender a otra cuenta de moderación ni a sí misma.
- **D-31 · Desafíos mensuales.** Un desafío está abierto mientras su mes no haya pasado y no tenga ganador. Hay
  una participación por persona, con foto y créditos obligatorios (RF-27).
- **D-32 · Búsqueda (RF-31).** Cada palabra de la consulta debe coincidir (AND) con texto o con el vocabulario del
  dominio: nombres de regiones y capitales regionales, etiquetas de especialidad, tipo de producto y tipo de
  evento, y algunos sinónimos («goma» → EVA). Se ignoran palabras vacías («de», «la», «en»…). El autocompletado
  entrega hasta 8 sugerencias que intercalan tipos.
- **D-33 · Fichas del directorio creadas por opt-in.** Al cambiar de región sin coordenadas, la ficha se ubica en
  la capital regional (`REGION_CENTRO`) para que aparezca en el mapa.
- **D-34 · RF fuera de las fases pedidas.** RF-05 (compartir en redes) y RF-30 (FAQ) quedan pendientes. RF-18
  (galería por paso) y RF-35 (flujo de registro propio para proveedores) quedan parciales. Ver
  `docs/TRAZABILIDAD.md`. *(Actualizado por D-45: RF-05 implementado y RF-30 parcial.)*
- **D-35 · Revisión visual.** Además del build, las páginas se revisaron con capturas de Edge *headless* a 500, 600
  y 1280 px, sin errores en la consola. Bajo ~500 px la ventana *headless* no se reduce más, así que no hubo
  captura útil a 400 px.

## Rediseño del frontend (Claude Design)

Fuente: `design/Cosplay Chile — Frontend.html`. El backend no se modificó. Las diferencias con la API están en
`docs/BRECHAS_DISENO.md`.

- **D-36 · Ubicación del diseño.** Se pidió en `docs/design/`, pero el archivo está en `design/` (raíz del
  repositorio). Se usó desde ahí sin moverlo.
- **D-37 · Tema oscuro único.** El diseño es solo oscuro; se eliminó el tema claro anterior. Los colores se
  tomaron del diseño y los pares texto/fondo usados cumplen contraste AA. El foco visible es un contorno cian
  de 2 px, como en el diseño.
- **D-38 · Tokens en Tailwind 4.** Colores, tipografías (Playfair Display para títulos, DM Sans para texto),
  radios (2 px en botones, 18 px en paneles), *gutter* `clamp(20px,5vw,72px)` y ancho máximo de 1296 px están
  en `@theme` (`frontend/src/index.css`). Los componentes compartidos usan variables semánticas (`--texto`,
  `--borde`, `--campo-fondo`…).
- **D-39 · Fuentes autoalojadas.** Se usan con `@fontsource`, sin pedir nada a Google Fonts. Así no se
  envían datos de los visitantes a terceros (Ley 21.719) y no se depende de una red externa.
- **D-40 · Migración por pantallas.** Durante la migración, las páginas no migradas se mostraron dentro de un
  panel claro (`.legado`). Ese mecanismo se eliminó al terminar.
- **D-41 · Mapa del directorio.** El mapa esquemático del diseño funciona como filtro por región. La posición
  de cada región se calcula desde la latitud media de los puntos reales de `/api/directorio/mapa`. El mapa
  Leaflet se conserva como «Ver mapa detallado» (RF-12) y se carga bajo demanda. En móvil la silueta se oculta,
  porque las mismas regiones están como chips.
- **D-42 · Ficha del directorio.** En escritorio (≥ 1280 px), «Ver ficha» muestra la ficha a la derecha, como en
  el diseño. En pantallas más chicas abre la ficha completa `/directorio/:id`.
- **D-43 · Rutas conservadas.** `/ingresar`, `/registro` y `/recuperar` muestran la misma vista con pestañas.
  `/comunidad/:slug` reutiliza la página de comunidad con el foro elegido. `/contacto` es la pestaña de contacto
  de la nueva ruta `/seguridad`, y se mantiene el enlace de UC-01 para cuentas suspendidas
  (`/contacto?tipo=CUENTA`). El calendario recuerda el mes en la URL (`?mes=AAAA-MM`).
- **D-44 · Imágenes del diseño.** Las 15 ilustraciones del diseño están en `frontend/src/assets/diseno/`. Se usan
  solo como decoración (`alt=""`), nunca con créditos inventados. Los trajes, la galería y las fichas usan
  imágenes y créditos reales de la API.
- **D-45 · RF-05 y RF-30 sin backend.** Compartir en redes (`CompartirRedes.jsx`) usa enlaces de intención de
  WhatsApp, X y Facebook, «copiar enlace» y el menú nativo del sistema; no incrusta scripts de terceros. Las
  preguntas frecuentes son estáticas, así que RF-30 («autoadministrable») queda parcial.
- **D-46 · Reportar desde /seguridad.** La API exige `tipo_objeto` y `objeto_id`. El formulario deduce ambos
  del enlace interno que pega la persona (`enlaceReportable.js`) y requiere sesión, igual que la API.
- **D-47 · Pruebas del frontend.** Se agregaron Vitest, Testing Library y jsdom (solo de desarrollo), con
  59 pruebas que montan la app completa y simulan la API. Además, cada pantalla se verificó contra la API
  real con Edge *headless*, con y sin sesión.
- **D-48 · Cierre de sesión desde una ruta protegida.** React Router 7 navega con transiciones. Si la sesión se
  cerraba antes, `RequiereSesion` alcanzaba a redirigir a `/ingresar`. Ahora la navegación y el cierre van en la
  misma transición (`startTransition`). El error existía antes del rediseño y lo detectó una prueba nueva.
