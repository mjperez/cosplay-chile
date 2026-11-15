# Matriz de casos por requerimiento (EV4)

Trazabilidad entre los requerimientos funcionales, el código que los implementa
y las pruebas automatizadas que los verifican. Las **169 pruebas** se ejecutan
con `pytest` desde `backend/` y no requieren servicios externos; la cobertura
medida es **96%**. Los 31 casos añadidos en ES3 corresponden a los patrones
Observer (13) y Adapter (18) comprometidos en el informe ES2.

Convención: `ID de caso` identifica la fila; `Archivo` es la prueba que la
cubre; `Resultado` es el estado observado en la última ejecución completa.

## RF-01 · Infraestructura y configuración

| Caso | Requerimiento | Implementación | Prueba | Resultado |
|---|---|---|---|---|
| C-01 | `/health` informa el estado de la base | `app/api/routes/health.py` | `test_health.py` (3) | ✅ |
| C-02 | Migración aplicable sobre base vacía | `migrations/versions/0001_esquema_inicial.py` | `test_migraciones.py` (3) | ✅ |
| C-03 | Gestor de sesiones único | `app/core/database.py` | `test_singleton.py` (4) | ✅ |
| C-04 | Configuración por variables de entorno, DSN y CORS | `app/core/config.py` | `test_config.py` (11) | ✅ |

## RF-02 · Registro, autenticación y autorización

| Caso | Requerimiento | Implementación | Prueba | Resultado |
|---|---|---|---|---|
| C-05 | Registro con consentimiento y contraseña hasheada | `app/services/auth.py`, `app/core/security.py` | `test_registro.py` (11), `test_seguridad.py` (10) | ✅ |
| C-06 | Login sin revelar si el correo existe | `app/services/auth.py` | `test_login.py` (8) | ✅ |
| C-07 | Bloqueo tras 5 intentos fallidos en 15 min | `app/models/intento_login.py` | `test_login.py` (8) | ✅ |
| C-08 | Token válido entre peticiones; vencido o malformado da 401 | `app/api/deps.py` | `test_autorizacion.py` (9) | ✅ |
| C-09 | Rol sin permisos recibe 403; el rol se lee de la base | `app/api/deps.py` | `test_autorizacion.py` (9) | ✅ |

## RF-03 · Directorio de profesionales (US-13)

| Caso | Requerimiento | Implementación | Prueba | Resultado |
|---|---|---|---|---|
| C-10 | Listado con filtros, paginación y opciones | `app/api/routes/proveedores.py` | `test_proveedores.py` (13) | ✅ |
| C-11 | 20 fichas reales cargadas de forma idempotente | `app/seed/proveedores.py` | `test_proveedores.py`, `test_semilla_demo.py` | ✅ |

## RF-04 · Contenido editorial (US-08)

| Caso | Requerimiento | Implementación | Prueba | Resultado |
|---|---|---|---|---|
| C-12 | Fábrica crea guía, entrevista o artículo según el tipo | `app/factories/contenido_factory.py` | `test_contenido.py` (24) | ✅ |
| C-13 | Borrador, publicación y dominio de video permitido | `app/services/contenido.py` | `test_contenido.py` (24) | ✅ |
| C-14 | Solo contenido publicado aparece en el listado | `app/api/routes/contenido.py` | `test_contenido.py` (24) | ✅ |

## RF-05 · Calendario de eventos

| Caso | Requerimiento | Implementación | Prueba | Resultado |
|---|---|---|---|---|
| C-15 | Todas las rutas nuevas quedan en OpenAPI | `app/main.py` | `test_las_rutas_nuevas_estan_en_openapi` | ✅ |
| C-16 | Listado vacío, filtros por tipo/región/texto y paginación | `app/repositories/evento.py` | `test_listado_de_eventos_vacio`, `test_filtros_de_eventos` | ✅ |
| C-17 | Solo administrador crea eventos; rango de fechas válido | `app/api/routes/eventos.py`, `app/schemas/evento.py` | `test_crear_evento_exige_administrador`, `test_admin_crea_evento_y_el_listado_lo_muestra`, `test_fecha_de_termino_anterior_al_inicio_se_rechaza` | ✅ |
| C-18 | Inscripción única por usuario, cancelación y «mis eventos» | `app/services/evento.py` | `test_ciclo_completo_de_inscripcion` | ✅ |
| C-19 | Evento inexistente da 404 antes que 409 | `app/services/evento.py` | `test_inscribirse_en_evento_inexistente_da_404` | ✅ |

## RF-06 · Foro de la comunidad

| Caso | Requerimiento | Implementación | Prueba | Resultado |
|---|---|---|---|---|
| C-20 | Lectura pública del foro | `app/api/routes/comunidad.py` | `test_foro_es_publico_y_arranca_vacio` | ✅ |
| C-21 | Abrir tema requiere sesión; responder y ver detalle | `app/services/comunidad.py` | `test_crear_tema_responder_y_ver_detalle`, `test_crear_tema_sin_sesion_da_401` | ✅ |
| C-22 | Tema cerrado no admite respuestas; solo autor o admin cierra | `app/services/comunidad.py` | `test_tema_cerrado_no_admite_respuestas_y_solo_el_autor_lo_cierra` | ✅ |
| C-23 | Filtros por categoría y búsqueda | `app/repositories/comunidad.py` | `test_filtros_del_foro` | ✅ |

## RF-07 · Desafíos mensuales

| Caso | Requerimiento | Implementación | Prueba | Resultado |
|---|---|---|---|---|
| C-24 | Desafío vigente por mes e historial | `app/services/comunidad.py` | `test_desafio_vigente_y_historial` | ✅ |
| C-25 | Solo administrador crea desafíos; mes no duplicado | `app/api/routes/comunidad.py` | `test_crear_desafio_exige_admin` | ✅ |
| C-26 | Ganador debe existir | `app/services/comunidad.py` | `test_ganador_inexistente_da_404` | ✅ |

## RF-08 · Perfil y complementos

| Caso | Requerimiento | Implementación | Prueba | Resultado |
|---|---|---|---|---|
| C-27 | Perfil propio editable y visible sin sesión por id | `app/services/perfil.py` | `test_perfil_se_actualiza_y_se_ve_sin_sesion` | ✅ |
| C-28 | Tiendas y grupos disponibles, inicialmente vacíos | `app/repositories/directorio.py` | `test_tiendas_y_grupos_estan_disponibles_y_vacios` | ✅ |

## RF-09 · Datos de demostración

| Caso | Requerimiento | Implementación | Prueba | Resultado |
|---|---|---|---|---|
| C-29 | La semilla deja los seis módulos con datos | `app/seed/demo.py` | `test_la_semilla_deja_todos_los_modulos_con_datos` | ✅ |
| C-30 | El contenido de demo queda publicado | `app/seed/demo.py` | `test_el_contenido_de_demo_queda_publicado` | ✅ |
| C-31 | Las cuentas demo permiten entrar | `app/seed/demo.py` | `test_las_cuentas_demo_permiten_entrar` | ✅ |
| C-32 | El detalle de un evento muestra participantes | `app/seed/demo.py` | `test_el_detalle_de_un_evento_muestra_participantes` | ✅ |
| C-33 | La semilla es idempotente | `app/seed/demo.py` | `test_la_semilla_es_idempotente` | ✅ |
| C-34 | El perfil de ejemplo es público | `app/seed/demo.py` | `test_el_perfil_de_ejemplo_es_publico` | ✅ |
| C-35 | La semilla se rechaza en producción | `app/seed/demo.py` | `test_la_semilla_se_rechaza_en_produccion` | ✅ |
| C-50 | Las cuentas demo se nombran por su rol | `app/seed/demo.py` | `test_las_cuentas_demo_se_llaman_segun_su_rol` | ✅ |
| C-51 | Recargar corrige nombres de cuentas ya creadas | `app/repositories/usuario.py`, `app/seed/demo.py` | `test_recargar_la_semilla_corrige_nombres_de_cuentas_ya_creadas` | ✅ |

## RF-10 · Panel de administración

| Caso | Requerimiento | Implementación | Prueba | Resultado |
|---|---|---|---|---|
| C-36 | Las 16 rutas del panel están en OpenAPI | `app/api/routes/admin.py` | `test_las_rutas_del_panel_estan_en_openapi` | ✅ |
| C-37 | Todos los endpoints nacen protegidos: 401 sin token, 403 sin rol | `app/api/routes/admin.py` | `test_todos_los_endpoints_nacen_protegidos` | ✅ |
| C-38 | Los catálogos del panel coinciden con los modelos | `app/schemas/admin.py` | `test_los_catalogos_del_panel_coinciden_con_los_modelos` | ✅ |
| C-39 | El resumen cuenta lo que hay en la base | `app/repositories/admin.py` | `test_resumen_cuenta_lo_que_hay_en_la_base` | ✅ |
| C-40 | Bandeja ve borradores; publicar, rechazar y corregir | `app/services/admin.py` | `test_bandeja_ve_borradores_y_permite_publicar_rechazar_y_corregir` | ✅ |
| C-41 | Transición sobre contenido inexistente da 404 | `app/services/admin.py` | `test_transicion_a_contenido_inexistente_devuelve_404` | ✅ |
| C-42 | Un admin no puede desactivarse a sí mismo | `app/services/admin.py` | `test_admin_no_puede_desactivarse_a_si_mismo` | ✅ |
| C-43 | Desactivar una cuenta le quita el acceso | `app/api/deps.py` | `test_desactivar_un_usuario_le_quita_el_acceso` | ✅ |
| C-44 | Eliminar evento borra también las inscripciones | `app/repositories/admin.py` | `test_eliminar_evento_borra_tambien_las_inscripciones` | ✅ |
| C-45 | Ocultar un tema lo saca del foro público y se puede reabrir | `app/services/admin.py` | `test_ocultar_un_tema_lo_saca_del_foro_publico_y_se_puede_reabrir` | ✅ |
| C-46 | Estado de tema fuera de catálogo da 422 | `app/schemas/admin.py` | `test_estado_de_tema_fuera_de_catalogo_devuelve_422` | ✅ |
| C-47 | Crear desafío y elegir ganador desde el panel | `app/api/routes/admin.py` | `test_crear_desafio_y_elegir_ganador_desde_el_panel` | ✅ |
| C-48 | Alta de tienda y grupo valida duplicados y URLs | `app/schemas/admin.py` | `test_alta_de_tienda_y_grupo_valida_duplicados_y_urls` | ✅ |
| C-49 | Crear categoría desde el panel | `app/api/routes/admin.py` | `test_crear_categoria_desde_el_panel` | ✅ |

## RF-11 · Observer: notificaciones internas (RF-37)

| Caso | Requerimiento | Implementación | Prueba | Resultado |
|---|---|---|---|---|
| C-52 | El gestor registra exactamente los 3 observadores del ES2 | `app/events/gestor.py` | `test_el_gestor_registra_los_tres_observadores_del_informe` | ✅ |
| C-53 | `configurar_observadores()` es idempotente | `app/main.py`, `app/events/observadores.py` | `test_configurar_observadores_es_idempotente` | ✅ |
| C-54 | Enviar tutorial dispara aviso, correo y bitácora | `app/services/contenido.py` | `test_enviar_un_tutorial_dispara_los_tres_observadores` | ✅ |
| C-55 | La bitácora guarda actor, recurso y detalle | `app/events/observadores.py` | `test_la_bitacora_registra_actor_recurso_y_detalle` | ✅ |
| C-56 | Publicar contenido avisa al autor | `app/services/contenido.py` | `test_publicar_un_contenido_avisa_al_autor` | ✅ |
| C-57 | Crear evento avisa a la comunidad pero no al actor | `app/services/evento.py` | `test_crear_evento_avisa_a_la_comunidad_pero_no_al_actor` | ✅ |
| C-58 | Crear desafío dispara aviso y bitácora | `app/services/comunidad.py` | `test_crear_desafio_dispara_notificacion_y_bitacora` | ✅ |
| C-59 | Un UUID ajeno da 404, no 403 | `app/repositories/notificacion.py` | `test_marcar_como_leida_no_permite_avisos_ajenos` | ✅ |
| C-60 | Los endpoints de avisos exigen sesión | `app/api/routes/notificaciones.py` | `test_los_endpoints_de_notificaciones_exigen_sesion` | ✅ |
| C-61 | Un observador caído no impide a los demás | `app/events/gestor.py` | `test_un_observador_caido_no_impide_a_los_demas` | ✅ |
| C-62 | Un tipo fuera del catálogo se rechaza | `app/events/gestor.py` | `test_un_tipo_de_evento_fuera_del_catalogo_se_rechaza` | ✅ |

## RF-12 · Adapter: imágenes de contenidos (RF-18 / RF-27 / RF-08)

| Caso | Requerimiento | Implementación | Prueba | Resultado |
|---|---|---|---|---|
| C-63 | La interfaz tiene los 3 métodos comprometidos en el ES2 | `app/adapters/almacenamiento.py` | `test_la_interfaz_tiene_los_tres_metodos_comprometidos_en_el_es2` | ✅ |
| C-64 | El adaptador local guarda, devuelve enlace y borra | `AlmacenamientoLocalAdapter` | `test_el_adaptador_local_guarda_devuelve_enlace_y_borra` | ✅ |
| C-65 | Rechaza `../` fuera del directorio (OWASP A01/A03) | `AlmacenamientoLocalAdapter._ruta()` | `test_el_adaptador_rechaza_salir_del_directorio` | ✅ |
| C-66 | Cloudinary traduce las 3 operaciones al cliente externo | `CloudinaryStorageAdapter` | `test_cloudinary_traduce_las_tres_operaciones_al_cliente_externo` | ✅ |
| C-67 | La firma HTTP no envía el `api_secret` en el body | `ClienteCloudinaryHTTP` | `test_el_cliente_http_firma_la_peticion_y_envia_el_binario` | ✅ |
| C-68 | La fábrica elige backend y exige credenciales | `obtener_almacenamiento()` | `test_la_fabrica_elige_el_backend_y_exige_credenciales` | ✅ |
| C-69 | Las credenciales viven en `Settings`, no en el código | `app/core/config.py` | `test_las_credenciales_viven_en_la_configuracion_no_en_el_codigo` | ✅ |
| C-70 | Lista blanca PNG/JPEG/WebP | `app/services/archivos.py` | `test_el_servicio_acepta_solo_los_tres_formatos_de_la_lista_blanca` | ✅ |
| C-71 | Rechaza SVG y tipos fuera de lista | `app/services/archivos.py` | `test_el_servicio_rechaza_un_tipo_fuera_de_la_lista` | ✅ |
| C-72 | No confía en el `Content-Type`: verifica magic bytes | `app/services/archivos.py::_coincide` | `test_el_servicio_no_confia_en_el_content_type_declarado` | ✅ |
| C-73 | Rechaza vacíos y archivos de más de 5 MB | `app/services/archivos.py` | `test_el_servicio_rechaza_vacios_y_demasiado_grandes` | ✅ |
| C-74 | Subida por HTTP y posterior GET del enlace absoluto | `app/api/routes/archivos.py` | `test_subir_una_imagen_por_http_y_servirla` | ✅ |
| C-75 | La API traduce errores a 415/400/413 y exige token | `app/api/routes/archivos.py` | `test_la_api_rechaza_entradas_peligrosas`, `test_sin_token_no_se_puede_subir` | ✅ |
| C-76 | Borrado ajeno da 403; el propio da 204 | `app/api/routes/archivos.py` | `test_no_se_puede_borrar_un_archivo_de_otra_cuenta` | ✅ |
| C-77 | Los cuatro patrones del ES2 están implementados | todos | `test_los_cuatro_patrones_del_informe_estan_implementados` | ✅ |

## RF-13 · Auditoría, normativa y CI/CD (ES3)

| Caso | Requerimiento | Implementación | Prueba | Resultado |
|---|---|---|---|---|
| C-78 | La bitácora es de solo lectura para administradores | `app/api/routes/admin.py` | `test_la_bitacora_solo_la_lee_un_administrador` | ✅ |
| C-79 | La bitácora sobrevive a la baja del actor (sin FK) | `0005_observer_notificaciones_auditoria.py` | `test_la_bitacora_no_tiene_clave_foranea_hacia_usuario` | ✅ |
| C-80 | Pipeline con cobertura ≥90%, lint y build | `.github/workflows/ci.yml` | ejecución local `pytest --cov-fail-under=90` | ✅ |
| C-81 | Los defectos encontrados quedan documentados | `CORRECCIONES_ES3.md` | 9 hallazgos con corrección y evidencia | ✅ |

## Verificación no automatizada (recorrido de demo)

Además de las pruebas, `backend/scripts/recorrido_http.py` prepara una base
SQLite temporal, aplica `alembic upgrade head`, carga ambas semillas, levanta
`uvicorn` y ejecuta peticiones HTTP **reales** con `httpx` (sin `TestClient`):
health, OpenAPI con **49 rutas**, login de las tres cuentas demo, 401/403 del
panel y de la auditoría, los siete catálogos, subida de PNG con verificación de
magic bytes y rechazo de SVG/vacío, borrado ajeno 403 y propio 204, borrador con
imagen, avisos internos, correo a moderación encolado, bitácora, creación de
evento con avisos masivos, marcar leída, publicación editorial y alta de tema
en el foro. **51/51 comprobaciones en verde** (salida 0). El guion de exposición
está en [`GUIA_DEMO.md`](../../GUIA_DEMO.md).

## Resumen

| Ámbito | Pruebas |
|---|---|
| Infraestructura y configuración | 21 |
| Autenticación y autorización | 38 |
| Directorio y contenido | 37 |
| Módulos nuevos | 18 |
| Semillas de demostración | 9 |
| Panel de administración | 15 |
| **Observer (ES3)** | **13** |
| **Adapter (ES3)** | **18** |
| **Total** | **169** |

La cobertura medida es **96%** (2550 sentencias, 100 sin cubrir) y el umbral
exigido por el pipeline es 90%. Los defectos detectados durante el desarrollo
y sus correcciones están en
[`CORRECCIONES_ES3.md`](../../CORRECCIONES_ES3.md).
