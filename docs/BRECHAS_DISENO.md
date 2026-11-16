# Brechas entre el diseño y el backend

El frontend se rediseñó a partir de `design/Cosplay Chile — Frontend.html`, exportado desde Claude Design
(8 tableros a 1440 px: Inicio, Guías, Directorio, Calendario, Comunidad y foro, Acceso y perfil, Seguridad y
contacto, y Panel de moderación). **El backend y los contratos de la API no se modificaron.** Cuando el
diseño muestra algo que la API no entrega, no se inventó: se omitió, se reemplazó por el dato real más
cercano o se dejó como texto informativo. Este documento lista cada caso.

Estados: **Omitido** (no se muestra) · **Adaptado** (se muestra con lo que sí existe) · **Placeholder**
(se ve, pero no tiene funcionalidad) · **Estático** (contenido editorial escrito en el frontend).

## Brechas con la API

| # | Pantalla | Qué trae el diseño | Qué hace el frontend | Estado | Para cerrarla (backend) |
|---|---|---|---|---|---|
| B-01 | Guías | Minutos de lectura e insignia «Video» en cada tarjeta | `ContenidoResumen` no trae duración ni `video_url`. La tarjeta muestra «Descargable» y el autor; el video aparece en el detalle | Adaptado | Agregar `duracion_min` y `tiene_video` al resumen |
| B-02 | Guías | Formulario corto «Envía tu propio tutorial» con campo **Región** | El contenido no tiene región, y la Factory exige pasos y materiales. El bloque explica el proceso y lleva al formulario completo `/guias/publicar` (UC6 intacto) | Adaptado | `region` opcional en `Contenido` |
| B-03 | Directorio | «Precios estimados» con monto por servicio | Se muestran el rango `precio_desde`–`precio_hasta` y la lista de `servicios` sin montos | Adaptado | Servicios como lista de `{nombre, precio}` |
| B-04 | Directorio | Botón «Contactar por Instagram» | Se muestran el campo `contacto` (texto libre) y el botón del `sitio_web` | Adaptado | Redes estructuradas en la ficha |
| B-05 | Acceso | Registro simplificado de proveedores con nombre del taller, especialidad e Instagram | `RegistroIn` no acepta esos campos. Se registra con `tipo_perfil` y opt-in, y un recuadro explica que la ficha se completa en «Mi ficha» (RF-35 sigue parcial) | Adaptado | Aceptar esos campos en `POST /api/auth/registro` |
| B-06 | Acceso y perfil | Avatar con foto | `avatar_url` existe, pero no hay pantalla para subirlo en este alcance. Se muestra la inicial del nombre | Adaptado | Ninguno; falta la pantalla |
| B-07 | Seguridad | Reportar con «Tipo de contenido» + «Enlace» y opción **anónima** | `POST /api/reportes` exige sesión, `tipo_objeto` y `objeto_id`, y siempre guarda quién reporta. Se deducen tipo e id del enlace interno (guía, tema, respuesta, evento o ficha). Para reseñas y fotos de desafíos se pide usar el botón «Reportar» junto a ellas. No hay reporte anónimo | Adaptado / Omitido | Reporte anónimo o por URL |
| B-08 | Seguridad | Motivos «Acoso o discriminación, Contenido ofensivo, Spam o estafa, Suplantación, Otro» | Se usan los motivos de `MotivoReporte` (spam, acoso, inapropiado, información incorrecta, otro) | Adaptado | Ampliar el enumerado |
| B-09 | Contacto | Campo **Región**, 6 motivos y **número de seguimiento** | `ContactoIn` no tiene región ni devuelve un número. Se usan los 4 `TipoContacto` y se agrega el campo **Asunto**, que la API exige | Omitido / Adaptado | Región opcional e id público del mensaje |
| B-10 | Contacto | «Contacto directo: [CORREO DE CONTACTO]» | No existe un correo oficial; se omitió | Omitido | Definir el correo del equipo |
| B-11 | Calendario | Casilla «Es una actualización de un evento que ya está en el calendario» | La sugerencia no tiene ese campo. El formulario indica usar «Reportar un cambio» en el evento (motivo `ACTUALIZACION_EVENTO`) | Adaptado | Ninguno; flujo existente |
| B-12 | Moderación | Acciones «Advertir al autor», «Derivar» y **Deshacer** | No existen en la API. Se usan las acciones reales: descartar, resolver, ocultar, ocultar y suspender, aprobar y rechazar | Omitido | Nuevas acciones y reversión |
| B-13 | Moderación | Contadores «Cuentas suspendidas» y «Resueltos esta semana» | `/resumen` no los trae; se **calculan** con `GET /api/moderacion/usuarios?estado=SUSPENDIDO` y con los reportes resueltos y descartados de los últimos 7 días | Adaptado (sin cambio de API) | Incluirlos en `/resumen` |
| B-14 | Moderación | «Contenido de seguridad: Editar consejos» | Los consejos son estáticos (B-17); el bloque enlaza a los consejos publicados | Placeholder | CRUD de consejos |
| B-15 | Comunidad | Avatar del autor en cada tema | `TemaResumen` no trae avatar; se usan las iniciales | Adaptado | Avatar en `AutorResumen` |
| B-16 | Comunidad | Categoría de foro «Errores comunes» y «Desafíos mensuales» como foros | Se listan los foros reales del backend. Los desafíos tienen su propia sección | Adaptado | Ninguno |

## Contenido estático (sin API)

| # | Dónde | Contenido | Nota |
|---|---|---|---|
| B-17 | `/seguridad` | Seis consejos de seguridad (acoso, traslado, salud, utilería, compras, datos) y bloque de urgencias (133, 131, 132) | Texto editorial del diseño |
| B-18 | `/guias` | Preguntas frecuentes (acordeón) | **RF-30 parcial**: el informe pide FAQ autoadministrable |
| B-19 | `/guias` | Franja «Errores comunes y cómo evitarlos» | Enlaza a la categoría real `errores-comunes` |
| B-20 | Inicio | Bloques «Aprende / Encuentra / Conecta», «Qué encuentras aquí» y tarjetas por rol | Descriptivos; todos los enlaces llevan a secciones reales |
| B-21 | Pie de página | Chips de Instagram, TikTok, Discord y YouTube | **Placeholder**: la plataforma aún no tiene redes; no son enlaces |

## Datos de ejemplo del diseño que no se usaron

El diseño trae textos de muestra (por ejemplo «Taller Aurora», «Meetup cosplay de diciembre», créditos como
«@aiko.cl», «[N]», «$[MONTO]», «[RECINTO]»). **Ninguno se muestra como si fuera real**: todas las listas,
cifras, créditos y fichas vienen de la API. Las ilustraciones del diseño (`frontend/src/assets/diseno/`)
se usan solo como decoración, con `alt=""`, y nunca acompañadas de créditos inventados.

## Estados que el diseño no mostraba y se derivaron

- **Móvil:** el diseño solo tiene la versión de 1440 px. Se agregaron un menú móvil, grillas que se apilan,
  chips con desplazamiento horizontal y el mapa esquemático reducido a un botón en pantallas pequeñas.
- **Sesión iniciada:** campana de notificaciones, menú de cuenta (perfil, favoritos, enviar tutorial,
  moderación para el rol administrador y cerrar sesión) y llamados que cambian según la sesión.
- **Estados vacíos, de carga y de error**, y los mensajes de la API (por ejemplo «Datos incorrectos»).
- **Páginas sin tablero propio:** búsqueda, detalle de guía, de evento, de tema y de desafío, ficha completa del
  directorio, perfil público, favoritos, restablecer contraseña, privacidad y 404. Siguen el mismo sistema.
