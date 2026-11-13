# Matriz de casos por requerimiento (EV4)

Trazabilidad entre los requerimientos funcionales, el código que los implementa
y las pruebas automatizadas que los verifican. Las 138 pruebas se ejecutan con
`pytest` desde `backend/` y no requieren servicios externos.

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

## Verificación no automatizada (recorrido de demo)

Además de las pruebas, se ejecutó un recorrido extremo a extremo real sobre
SQLite con el esquema de Alembic: migración, semillas, arranque de uvicorn y
26 comprobaciones HTTP (health, login de administrador y de cosplayer, 401/403
del panel, resumen, bandeja editorial con publicar/rechazar/borrador, alta y
baja de eventos, moderación del foro, desafíos, tiendas, grupos, rechazo de
URLs `javascript:` y OpenAPI con 43 rutas). **26/26 en verde.** El guion
reproducible está en [`GUIA_DEMO.md`](../../GUIA_DEMO.md).

## Resumen

| Ámbito | Pruebas |
|---|---|
| Infraestructura y configuración | 21 |
| Autenticación y autorización | 38 |
| Directorio y contenido | 37 |
| Módulos nuevos | 18 |
| Semillas de demostración | 9 |
| Panel de administración | 15 |
| **Total** | **138** |
