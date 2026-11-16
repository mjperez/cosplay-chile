# Trazabilidad de requerimientos

Fuente: Tabla 1 (RF-01 a RF-40) y Tabla 2 (RNF-01 a RNF-11) de `docs/informe_requerimientos.pdf`.
Estados: **Implementado** · **Parcial** (cubierto en parte; se indica qué falta) · **Pendiente** (no implementado).
Las rutas son relativas a la raíz del repositorio. Pruebas automatizadas: `backend/tests/` (pytest) y
`frontend/src/test/` (Vitest + Testing Library).

Resumen: **37 implementados, 3 parciales y 0 pendientes** de 40 RF; **5 implementados, 5 parciales y
1 pendiente** de 11 RNF. Con el rediseño del frontend (ver `docs/BRECHAS_DISENO.md`), RF-05 pasó de
pendiente a implementado y RF-30 de pendiente a parcial.

## Requerimientos funcionales

| ID | Requerimiento (resumen) | Estado | Dónde |
|---|---|---|---|
| RF-01 | Portada con acceso a todas las secciones | Implementado | `frontend/src/pages/Inicio.jsx`, `backend/app/api/routers/inicio.py` |
| RF-02 | Sección de guías para principiantes | Implementado | `backend/app/api/routers/contenidos.py`, `frontend/src/pages/guias/Guias.jsx` (filtro por nivel; atajo «Empieza aquí» en la portada) |
| RF-03 | Guías de elección de personaje, medidas, técnicas, presupuesto y seguridad | Implementado | `backend/app/seed/contenidos.py` (una guía por tema) |
| RF-04 | Filtrar por nivel principiante, intermedio o avanzado | Implementado | `backend/app/services/contenido_service.py` (`listar_publicados`), chips de nivel en `Guias.jsx`; pruebas `test_filtros_por_nivel_categoria_y_texto` y `guias.test.jsx` |
| RF-05 | Botones para compartir en redes sociales | Implementado | `frontend/src/components/CompartirRedes.jsx` (WhatsApp, X, Facebook, copiar enlace y menú nativo del sistema), en guías, fichas, eventos, temas y galería; prueba en `guias.test.jsx` |
| RF-06 | Descarga directa de contenidos | Implementado | `GET /api/contenidos/{id}/descargar` en `contenidos.py` (HTML imprimible, solo con sesión; D-06) |
| RF-07 | Cuentas con perfiles diferenciados por rol | Implementado | `Perfil.tipo_perfil` en `backend/app/models/usuario.py`, chips de rol en `frontend/src/pages/auth/Acceso.jsx` |
| RF-08 | Perfil con biografía, portafolio, redes y región | Implementado | `frontend/src/pages/perfil/Perfil.jsx`, `PerfilPublico.jsx`, `backend/app/api/routers/perfil.py` |
| RF-09 | Registro, login y recuperación seguros | Implementado | `backend/app/services/auth_service.py`, `backend/app/api/routers/auth.py`, `Acceso.jsx`; `tests/test_auth.py`, `acceso.test.jsx` |
| RF-10 | Elegir si el perfil aparece en el directorio público | Implementado | `backend/app/services/directorio_sync.py`; interruptor en `Acceso.jsx` y `Perfil.jsx`; prueba `test_perfil_publico_opt_in_crea_ficha_en_directorio` |
| RF-11 | Directorio de comunidades por región | Implementado | `ComunidadGrupo` en `backend/app/models/directorio.py`, pestaña «Comunidades por región» en `Directorio.jsx` |
| RF-12 | Mapa interactivo de Chile | Implementado | Mapa esquemático por región (`pages/directorio/MapaEsquematico.jsx`) y mapa detallado Leaflet (`MapaChile.jsx`), `GET /api/directorio/mapa` |
| RF-13 | Filtros por región y por tipo (sastrería, maquillaje…) | Implementado | `routers/directorio.py` (`_filtros`), chips en `frontend/src/pages/directorio/Directorio.jsx` |
| RF-14 | Catálogo de cosmakers y proveedores locales | Implementado | `ProveedorServicio` + `Especialidad` en `backend/app/models/enums.py` |
| RF-15 | Calendario de eventos cosplay en Chile | Implementado | `backend/app/api/routers/eventos.py`, grilla mensual y lista en `frontend/src/pages/calendario/Calendario.jsx` |
| RF-16 | Nombre, fecha, lugar, tipo y enlace oficial | Implementado | `backend/app/models/evento.py`, `Calendario.jsx`, `EventoDetalle.jsx` |
| RF-17 | Reportar eventos o sugerir actualizaciones | Implementado | `POST /api/eventos/sugerir` (formulario en `Calendario.jsx` y `SugerirEvento.jsx`), `POST /api/reportes` con motivo `ACTUALIZACION_EVENTO` («Reportar un cambio») |
| RF-18 | Contenido multimedia: texto, imágenes y video embebido | **Parcial** | Texto, imagen principal y video de YouTube/Vimeo (`schemas/contenido.py`, `video_embed`). Falta una galería de imágenes por paso |
| RF-19 | Reseñas y calificaciones a proveedores | Implementado | `Resena` en `models/directorio.py`, `POST /api/directorio/{id}/resenas`, `pages/directorio/Ficha.jsx`; pruebas `test_resenas_solo_con_sesion_una_por_persona` y `directorio.test.jsx` |
| RF-20 | Entrevistas a cosplayers chilenos | Implementado | Subclase `Entrevista` (Factory) y 3 entrevistas en el seed; sección «Entrevistas, consejos y historias» en `Guias.jsx` |
| RF-21 | Sección de consejos de expertos sobre concursos | Implementado | Categoría `consejos-expertos` y artículo en `seed/contenidos.py` |
| RF-22 | Foros categorizados por temática | Implementado | `backend/app/api/routers/comunidad.py`, barra de foros en `frontend/src/pages/comunidad/Comunidad.jsx` |
| RF-23 | Crear temas, debatir y responder | Implementado | `POST /api/foros/{slug}/temas` (compositor en `Comunidad.jsx`), `POST /api/temas/{id}/respuestas`, `TemaDetalle.jsx` |
| RF-24 | Enviar tutoriales para revisión y publicación | Implementado | UC6: `contenido_service.publicar_tutorial`, `PublicarTutorial.jsx`, `ColaContenidos.jsx`; `tests/test_contenidos.py`, `guias.test.jsx`, `moderacion.test.jsx` |
| RF-25 | Guardar favoritos (guías, proveedores, eventos) | Implementado | `backend/app/api/routers/favoritos.py`, `BotonFavorito.jsx`, `useFavoritos.js`, `Favoritos.jsx` |
| RF-26 | Sección «Historias de cosplayers chilenos» | Implementado | Categoría `historias` (entrevistas) y foro `historias` (`seed/comunidad.py`) |
| RF-27 | Fotos con créditos al fotógrafo y al cosplayer | Implementado | `ImagenConCreditos` en `schemas/comunidad.py`, `components/FotoConCreditos.jsx` (galería y desafíos); prueba `test_foto_sin_creditos_se_rechaza` |
| RF-28 | Apartado «Errores comunes y cómo evitarlos» | Implementado | Categoría `errores-comunes` y dos artículos en el seed; franja «Errores comunes» en `Guias.jsx` |
| RF-29 | Subir historias de cómo entraste al cosplay | Implementado | Foro `historias` y llamado «Cuéntanos cómo empezaste» (`Comunidad.jsx`, `NuevoTema.jsx`) |
| RF-30 | FAQ autoadministrable | **Parcial** | Preguntas frecuentes en acordeón en `Guias.jsx`. Son estáticas: falta que moderación pueda editarlas (requiere backend) |
| RF-31 | Motor de búsqueda unificado por palabras clave | Implementado | `backend/app/services/busqueda_service.py`, `routers/busqueda.py`, `BuscadorGlobal.jsx`, `Buscar.jsx`; `tests/test_busqueda_inicio.py`, `inicio.test.jsx` |
| RF-32 | Ficha de proveedor: nombre, servicios, contacto, portafolio, precios, región | Implementado | Ficha lateral y completa (`Directorio.jsx`, `DirectorioDetalle.jsx`), «Mi ficha» (`MiFicha.jsx`, `PUT /api/directorio/mi-ficha`) |
| RF-33 | Tiendas nacionales e internacionales con envío a Chile | Implementado | `Tienda.alcance` y `envia_a_chile`; filtro «Internacionales con envío a Chile» en `Directorio.jsx` |
| RF-34 | Filtrar tiendas por materia prima | Implementado | `TipoProducto` y filtro `tipo_producto`; prueba `test_filtros_del_directorio` |
| RF-35 | Registro simplificado para proveedores y tiendas | **Parcial** | El registro con opt-in crea la ficha (`directorio_sync.py`) y `Acceso.jsx` explica cómo completarla, pero la API de registro no recibe nombre comercial, especialidad ni contacto |
| RF-36 | Desafíos mensuales | Implementado | `routers/comunidad.py` (participar), `routers/moderacion.py` (lanzar y elegir ganador), `pages/desafios/`, banner en `Comunidad.jsx` |
| RF-37 | Notificaciones internas de eventos, guías y desafíos | Implementado | `NotificacionInternaObserver` (`patterns/observer/observers.py`), `CampanaNotificaciones.jsx` y panel en `Comunidad.jsx`; `tests/test_observer.py` |
| RF-38 | Reportar contenido inapropiado | Implementado | `POST /api/reportes`, `BotonReportar.jsx`, pestaña «Reportar contenido» en `pages/seguridad/Seguridad.jsx`, `pages/moderacion/Reportes.jsx`; pruebas `test_reporte_ocultar_y_suspender_autor`, `seguridad.test.jsx` |
| RF-39 | Seguridad en eventos (acoso, transporte, salud) | Implementado | Categoría `seguridad-eventos`, consejos y urgencias en `/seguridad` (`Seguridad.jsx`), bloque en `Guias.jsx` y enlace en cada evento |
| RF-40 | Formulario de contacto | Implementado | `backend/app/api/routers/contacto.py`, pestaña «Contacto y denuncias» en `Seguridad.jsx` (`/contacto`), `pages/moderacion/Contactos.jsx` |

## Requerimientos no funcionales

| ID | Requerimiento | Estado | Evidencia y pendientes |
|---|---|---|---|
| RNF-01 | Interfaz intuitiva y amigable | Implementado | Diseño de Claude Design aplicado a todas las pantallas, migas de pan, mensajes y validaciones en español de Chile, estados vacíos con sugerencias. No hubo pruebas con usuarios |
| RNF-02 | Diseño responsivo | Implementado | Tailwind *mobile-first*; menú móvil propio (el diseño solo traía escritorio); revisado con capturas a 500, 1280 y 1440 px contra la API real |
| RNF-03 | Soporte para discapacidad visual o motora | **Parcial** | Se hizo: HTML semántico, `label` en todos los campos, texto alternativo obligatorio, «Saltar al contenido», foco visible (cian sobre fondo oscuro), patrones ARIA (tabs horizontales y verticales, combobox, `dialog`, `switch`, acordeón), objetivos táctiles de 44 px, contraste AA del tema oscuro y lista equivalente al mapa. Falta: auditoría WCAG formal con lector de pantalla |
| RNF-04 | 10.000 usuarios simultáneos | **Parcial** | Diseño preparado: API async, pool acotado (Singleton), paginación, índices por región, estado y fecha, e `INSERT … SELECT` masivo. Falta: prueba de carga (fuera de alcance) |
| RNF-05 | Carga de página menor a 2 s | **Parcial** | JS inicial de unos 145 KB gzip; el mapa Leaflet se carga bajo demanda; fuentes autoalojadas. No se midió formalmente |
| RNF-06 | Protección contra ataques comunes | **Parcial** | Se hizo: validación con Pydantic, ORM parametrizado, escape en la descarga HTML, URLs restringidas a http(s), tipo de archivo por firma binaria, cabeceras `nosniff` y `DENY`, rutas por rol, 401 genérico, redirección `siguiente` solo a rutas internas. Falta: limitación de intentos y HTTPS (depende del despliegue) |
| RNF-07 | Encriptación de contraseñas y datos sensibles | **Parcial** | Contraseñas con argon2id y tokens de recuperación con hash SHA-256. El cifrado en tránsito y en reposo depende del despliegue (Neon/Render) |
| RNF-08 | Disponibilidad 24/7 | **Pendiente** | Depende del despliegue (Neon + Render), que no se configuró en el prototipo |
| RNF-09 | Fácil de mantener por un equipo pequeño | Implementado | Capas separadas, 4 patrones, migraciones Alembic, 84 pruebas de backend y 59 de frontend, tokens de diseño centralizados en `index.css`, seed reproducible, `docker-compose` |
| RNF-10 | Diversidad de cuerpos, géneros y capacidades | Implementado | `backend/app/seed/ilustraciones.py` e `imagenes.py`, ilustraciones del diseño con distintos tonos de piel, y contenidos sobre cosplay adaptativo, tallas grandes y crossplay |
| RNF-11 | Ley 21.719: consentimiento, finalidad y supresión | Implementado | Consentimiento obligatorio con fecha (`Usuario.consentimiento_at`), finalidad en `Acceso.jsx` y `Privacidad.jsx`, autorización en el formulario de contacto, opt-in al directorio, «Eliminar mi cuenta y mis datos» (`auth_service.eliminar_cuenta`) |

## Casos de uso y diagramas del informe

| Artefacto | Implementación |
|---|---|
| UC-01 Identificarse (Tabla 5, Fig. 12) | `auth_service.autenticar` (401 «Datos incorrectos», 403 si la cuenta está suspendida), `registrar` (flujo 3a, inicia sesión), `solicitar_recuperacion` (flujo 3b); vista `Acceso.jsx` |
| UC6 Publicar tutorial (Tabla 6, Figs. 13 a 15) | `contenido_service.publicar_tutorial` → `ContenidoFactory` → `PENDIENTE` → `GestorEventos.notificar("NUEVO_TUTORIAL")`; excepciones 1 (borrador y redirección) y 2 (límite de 5 MB) |
| Fig. 10 Moderación (Gestionar Soporte y Reportes «extend» Bloquear/Sancionar) | `moderacion_service.resolver_reporte` (acción `OCULTAR_Y_SUSPENDER`), `POST /api/moderacion/usuarios/{id}/suspender`; panel `pages/moderacion/` |
| Fig. 11 Diagrama de clases | `backend/app/models/` (herencia de tabla única para `Contenido` y `DirectorioItem`; `Favorito` implementa la interfaz `Favoritable`) |
| Fig. 18 ER | Migración `backend/alembic/versions/0001_esquema_inicial.py` (diferencias en D-01 y D-02) |
| Patrones (págs. 29-31) | Ver la tabla «Patrones de diseño» del `README.md` |
