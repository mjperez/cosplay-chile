# Matriz de casos por requerimiento

Trazabilidad entre los requerimientos, el código que los implementa y las pruebas que los verifican. La fuente de los identificadores RF/RNF es `docs/informe_requerimientos.pdf`; el detalle de cada requerimiento está en `docs/TRAZABILIDAD.md`.

**96 pruebas de backend** (`pytest`, PostgreSQL de prueba, esquema creado por la migración real de Alembic, tablas vaciadas antes de cada caso) y **59 pruebas de interfaz** (Vitest + Testing Library, API simulada). Cobertura real del backend: **97%** con el núcleo `sysmon` de coverage.

| Ámbito | Pruebas | Archivo |
|---|---:|---|
| Autenticación, registro y recuperación | 20 | `test_auth.py` |
| Directorio, mapa, reseñas y calendario | 11 | `test_directorio_calendario.py` |
| Contenidos y cola editorial | 11 | `test_contenidos.py` |
| Factory Method | 13 | `test_factory.py` |
| Comunidad, foro, desafíos y moderación | 8 | `test_comunidad_moderacion.py` |
| Búsqueda global y portada | 6 | `test_busqueda_inicio.py` |
| Observer y bitácora | 7 | `test_observer.py` |
| Singleton, Adapter y patrones base | 8 | `test_patrones_base.py` |
| **Semillas y flujos adicionales (ES3)** | **7** | `test_cobertura_extra.py` |
| **Entrypoint, moderación, avisos y búsqueda (ES3)** | **5** | `test_cobertura_final.py` |
| **Total backend** | **96** | |

Las 12 pruebas marcadas como ES3 son las añadidas durante la integración para cubrir semillas, favoritos, reportes, contacto, recuperación, eventos sugeridos, perfil, cola editorial, moderación de cuentas y desafíos, avisos internos y búsqueda.

## Casos por requerimiento

| RF | Caso verificado | Prueba | Resultado |
|---|---|---|---|
| RF-01 | Portada con estadísticas, novedades y desafío actual | `test_semilla_completa_carga_datos_y_ilustraciones`, `inicio.test.jsx` | ✅ |
| RF-02 a RF-04 | Listado de guías, filtros por nivel/categoría/texto | `test_contenidos.py`, `guias.test.jsx` | ✅ |
| RF-05 | Compartir en redes | `guias.test.jsx` | ✅ |
| RF-06 | Descarga HTML del contenido | `test_publicar_tutorial_y_cola_editorial` | ✅ |
| RF-07 a RF-10 | Registro, login, recuperación, perfil y opt-in al directorio | `test_auth.py`, `test_perfil_actualizar_publico_y_suprimir_cuenta`, `acceso.test.jsx` | ✅ |
| RF-11 a RF-14 | Directorio, mapa, filtros, proveedores y tiendas | `test_directorio_calendario.py`, `test_busqueda_global_y_filtros_de_directorio`, `directorio.test.jsx` | ✅ |
| RF-15 a RF-17 | Calendario, detalle, asistencia y sugerencia de eventos | `test_directorio_calendario.py`, `test_sugerir_evento_asistir_y_decision_admin`, `calendario.test.jsx` | ✅ |
| RF-18 | Video embebido de YouTube/Vimeo (galería parcial, ver BRECHAS_DISENO B-01/B-02) | `test_contenidos.py` | ✅ / Parcial |
| RF-19 | Reseñas: una por persona, promedio y autor | `test_resenas_solo_con_sesion_una_por_persona` | ✅ |
| RF-20 a RF-21, RF-26, RF-28, RF-29 | Contenidos del seed: entrevistas, consejos, historias y errores comunes | `test_semilla_completa_carga_datos_y_ilustraciones` | ✅ |
| RF-22 a RF-23 | Foros, temas y respuestas | `test_crear_tema_responder_y_notificar_al_autor`, `comunidad.test.jsx` | ✅ |
| RF-24 | Publicar tutorial → pendiente → publicar/rechazar | `test_publicar_tutorial_y_cola_editorial`, `moderacion.test.jsx` | ✅ |
| RF-25 | Favoritos: agregar, listar, ids y quitar | `test_favoritos_se_pueden_agregar_listar_y_quitar`, `guias.test.jsx` | ✅ |
| RF-27 | Fotos con créditos obligatorios | `test_foto_sin_creditos_se_rechaza`, `comunidad.test.jsx` | ✅ |
| RF-30 | FAQ en acordeón (estática, ver BRECHAS_DISENO B-18) | `guias.test.jsx` | Parcial |
| RF-31 | Búsqueda global y autocompletado | `test_busqueda_global_y_filtros_de_directorio`, `inicio.test.jsx` | ✅ |
| RF-32 a RF-34 | Mi ficha, tiendas nacionales/internacionales y materia prima | `test_prestador_completa_su_ficha_y_no_puede_autocalificarse`, `directorio.test.jsx` | ✅ |
| RF-35 | Registro simplificado de proveedores (opt-in; campos ampliados pendientes, B-05) | `test_auth.py`, `acceso.test.jsx` | Parcial |
| RF-36 | Desafíos: participar, lanzar y elegir ganador | `test_participar_en_desafio_una_vez_y_solo_si_esta_abierto`, `test_moderacion_de_cuentas_desafios_y_auditoria` | ✅ |
| RF-37 | Avisos internos y marcar como leídos | `test_observer.py`, `test_avisos_internos_se_marcan_como_leidos` | ✅ |
| RF-38 | Reportar contenido y resolver desde moderación | `test_reporte_y_resolucion_por_moderacion`, `seguridad.test.jsx` | ✅ |
| RF-39 | Seguridad en eventos (contenido editorial) | `seguridad.test.jsx` | ✅ |
| RF-40 | Contacto público y atención por administración | `test_contacto_publico_y_atencion_por_admin`, `seguridad.test.jsx` | ✅ |
| RNF-01 a RNF-03 | Diseño, responsividad y accesibilidad | 59 pruebas de interfaz + `docs/BRECHAS_DISENO.md` | ✅ / Parcial |
| RNF-04 a RNF-05 | Arquitectura async y paginación; sin prueba de carga formal | `test_patrones_base.py` | Parcial |
| RNF-06 a RNF-07 | Validación, URLs seguras, argon2, hash de recuperación, cabeceras | `test_auth.py`, `test_patrones_base.py` | ✅ / Parcial |
| RNF-08 | Disponibilidad 24/7 (depende del despliegue) | — | Parcial |
| RNF-09 | Mantenibilidad: capas, patrones, CI, cobertura | `.github/workflows/ci.yml` | ✅ |
| RNF-10 | Ilustraciones propias y diversidad | `test_semilla_completa_carga_datos_y_ilustraciones` | ✅ |
| RNF-11 | Consentimiento, finalidad y supresión | `test_perfil_actualizar_publico_y_suprimir_cuenta`, `test_auth.py` | ✅ |
| Patrones | Singleton, Factory Method, Observer, Adapter | `test_factory.py`, `test_observer.py`, `test_patrones_base.py` | ✅ |

## Pruebas por tipo (rúbrica, actividad 2)

| Tipo | Evidencia |
|---|---|
| Unitarias | 96 pruebas pytest; cobertura 97% (>80% exigido) |
| Integración | `httpx.ASGITransport` sobre la app real, migración Alembic y PostgreSQL: todas las pruebas de router |
| Sistema / extremo a extremo | Recorrido reproducible en `scripts/recorrido_http.py` (**40/40**) + 59 pruebas que montan la aplicación completa |
| Autenticación | 20 pruebas de `test_auth.py`, incluidas suspensión, recuperación y contraseña débil |
| Autorización | Rutas de administración con 401/403 en `test_comunidad_moderacion.py` y pruebas adicionales |
| Penetración (OWASP ZAP) | **Pendiente**: no se ejecutó ZAP; los controles A01/A02/A03 se verifican con pruebas unitarias y de integración |
| Rendimiento | **Pendiente**: sin prueba de carga; la arquitectura async y la paginación están preparadas |

## Ejecución

```bash
cd backend
python -m pytest -q --cov=app --cov-report=term-missing --cov-fail-under=90

cd ../frontend
npm ci && npm test && npm run build
```
