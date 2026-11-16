# Análisis de brechas contra la rúbrica oficial (Unidad 3)

Basado en los dos documentos entregados y en los **cuatro PDF que venían
incrustados** dentro del DOCX (dos guías y dos rúbricas), contrastados con el
estado real del repositorio `cosplay-chile` al 15-11-2026.

> **Actualización 16-11-2026 (post-integración del ZIP).** Este análisis se escribió
> contra el stack **anterior** (SQLite, `/api/v1`, 138 pruebas). Después se sustituyó
> el frontend y el backend por los del ZIP y se migró encima la capa de calidad ES3.
> Las cifras vigentes son: **99 pruebas de backend / 97% de cobertura** (umbral CI 90%),
> **59 pruebas de interfaz**, **40/40 comprobaciones** en el recorrido HTTP real y
> **~60 rutas** OpenAPI; **sí existe `.github/workflows/ci.yml`** con PostgreSQL 16 en
> servicio y matrices Python 3.12/3.13. La base ahora es **PostgreSQL async**, no SQLite.
> **Actualización final 16-11:** el despliegue en Render quedó **operativo** (deploy `live`,
> `/api/salud` 200, 60 rutas, login y CORS correctos, 11/17/23/12 en las cifras de la
> portada). Ver `DIAGNOSTICO_RENDER.md` y `GUIA_DEMO.md`. **La conclusión sobre la ES4 no cambia**: el informe de diagramas
> UML adaptativos, el reporte de testing, ZAP y el formato APA siguen pendientes.


> **Actualización 16-11-2026 (cierre OWASP A07).** La tabla de condiciones de la
> guía de verificación afirmaba que el bloqueo tras 5 intentos ya existía; en la
> verificación en vivo no era así (8 intentos fallidos → ocho `401`, sin `429`). Se
> implementó el bloqueo temporal con migración `0002`, se añadieron 3 pruebas y la
> suite pasó de 96 a **99 pruebas** con **97% de cobertura**. Las cifras de este
> documento quedan actualizadas. **La conclusión sobre la ES4 no cambia**: sigue
> pendiente el informe de diagramas UML adaptativos, el reporte de testing y ZAP.

---

## 0. Primero, una aclaración importante

La guía dice textualmente:

> Evaluación Sumativa N° 3 — ponderación **35% para el prototipo**.
> Evaluación Sumativa N° 4 — ponderación **25% para el informe de Diagramas y Proceso de testeo**.

O sea que **son dos evaluaciones distintas**, aunque vengan en el mismo
documento. El prototipo funcional corresponde a la **ES3** y está **desplegado y
verificado en Render** con datos reales (ver `GUIA_DEMO.md`). El **informe de la
ES4 no existe todavía**: no hay ningún
documento de la Unidad 3 en el repo. Si el académico unificó ambas en una sola
entrega, el faltante es exactamente ese informe.

Corrección a mi respuesta anterior: cuando dije «no falta nada para la clase»,
me refería al **prototipo funcional**. Con la rúbrica a la vista eso es cierto
para la demo, pero **incompleto para la evaluación**: el informe de diagramas
adaptativos y el reporte de testing son obligatorios y aún no están redactados.

---

## 1. Qué se recuperó de los adjuntos

| Archivo | Contenido | Dónde quedó |
|---|---|---|
| `Guia Prototipo e Informes...docx` | Presentación, criterios, instrucciones, actividades, bibliografía | `documentos_evaluacion/00_...docx` |
| `Perez_Rubio_ES2 (1).pdf` | Informe Unidad 2, 68 páginas, 40 RF + 11 RNF, 11 diagramas 4+1, 4 patrones | `documentos_evaluacion/01_...pdf` |
| **OLE embebido 1** | Guía para la construcción del Prototipo Funcional (CI/CD, OWASP, logs) | `.../04_...pdf` |
| **OLE embebido 2** | Guía verificación seguridad: pauta de interfaz, UX y OWASP (3 procesos) | `.../05_...pdf` |
| **OLE embebido 3** | **Rúbrica Evaluación Prototipo** (4 dimensiones, 25/15/10/5) | `.../02_...pdf` |
| **OLE embebido 4** | **Rúbrica Informe de Diagramas UML y Testing** (5 dimensiones, 20/15/10/5) | `.../03_...pdf` |
| DOCX embebido | Plantilla del informe (portada, índice, glosario, APA, formato) | `.../06_...txt` |

> Los cuatro OLE eran PDFs completos dentro del Word y el quinto adjunto era otro
> DOCX incrustado. Es decir, se revisaron **los cinco archivos** que el campus lista
> como «Plantilla: Informe», «Guía: Construcción Prototipo», «Guía: Pauta evaluación
> interfaz y seguridad OWASP», «Rúbrica Evaluación Prototipo» y «Rúbrica Informe de
> Diagramas UML Adaptativos y Testing». Conviene tenerlos a la vista porque son los
> que fijan la nota. Su contenido se contrastó con el repositorio y se resume en las
> secciones §2 a §5 de este documento.

---

## 2. Cumplimiento por criterio de evaluación

| Criterio | Qué pide | Estado real | Brecha |
|---|---|---|---|
| **3.1.1** SaaS / IaaS / Cloud Computing | Describir tendencias | ES2 menciona PostgreSQL en Neon y ClickUp; no hay sección explícita de SaaS/IaaS/PaaS ni del despliegue en Render | **Falta redactarlo** en el informe |
| **3.1.2** Confiabilidad, códigos de ética, instrumentos jurídicos | Explicar importancia para el negocio | ES2 tiene RNF-11 (Ley 21.719); no hay códigos de ética ni Ley 19.223 de delitos informáticos | **Falta redactarlo** |
| **3.1.3** Prototipo según requerimientos, OWASP, delitos informáticos | Ver tabla §3 | Prototipo completo, desplegado y verificado en Render y en local | Ver §3 y `DIAGNOSTICO_RENDER.md` |
| **3.1.4** Diagramas UML adaptativos + Actividades + Paquetes | Incluir, corregir y **adaptar** los del informe anterior | ES2 tiene 11 diagramas; **no hay diagrama de Paquetes ni adaptación por desafío de roles**; no existen fuentes `.puml`/`.drawio` en el repo | **Falta lo central de la ES4** |
| **3.1.5** Corrección del código a partir del testing + ISO 27000 | **Evidenciar** las correcciones | Hubo correcciones reales (nombres por rol, sincronización de semilla, rollback); **no están documentadas como resultado de pruebas** | **Falta el reporte de testing** |

---

## 3. ES3 · Rúbrica del Prototipo (35%)

| Dimensión | Nivel estimado | Evidencia | Pendiente |
|---|---|---|---|
| Evaluación de interfaz de usuario | **Destacado** | Reglas de estilo centralizadas, jerarquía visual, 23 archivos con `aria-*`/`role`/`alt`, 14 con breakpoints responsive, `type="password"` en login y registro | Documentar las 5 condiciones de la pauta en el informe |
| Evaluación experiencia de usuario | **Destacado** | Llamados a la acción reales, logout en encabezado (escritorio y móvil), mensajes `role="status"`/`role="alert"`, diseño responsive | Documentar las 5 condiciones; declarar explícitamente enfoque *responsive* vs *mobile first* |
| Desarrollo según «Guía Prototipo Funcional» + OWASP | **Habilitado / Destacado** | Git ✅, incremental ✅, A01 control de acceso en cada request ✅, A02 argon2id + TLS ✅, A03 consultas parametrizadas y validación Pydantic ✅, justificación técnica en README ✅, SOLID/Clean Code ✅, testing desde el inicio ✅ | **CI/CD ya cubierto** (`.github/workflows/ci.yml`: pytest + cobertura ≥90% + Vitest + build, con PostgreSQL 16); **bitácora de auditoría** presente vía Observer (`/api/moderacion/auditoria`); pendiente: declarar tres entornos separados y dejar evidencia de code review |
| Corrección de código desde el testing | **En desarrollo** | Existen correcciones pero sin traza hallazgo → corrección | Falta el reporte que las vincule con ISO 27002 |

### Condiciones OWASP de la «Guía verificación seguridad» que requieren atención

| Condición | Estado |
|---|---|
| Validación de tipos, rangos, largos y caracteres peligrosos | ✅ Pydantic + rechazo con 422 |
| Hash de contraseñas, credenciales fuera del código | ✅ argon2id, `DATABASE_URL`/`JWT_SECRET` por entorno |
| Bloqueo tras 5 intentos, `input type=password` | ✅ **Implementado 16-11** (OWASP A07): `429 CUENTA_BLOQUEADA` tras 5 fallos, ventana de 15 min, contador por cuenta, umbrales por entorno. Ver `CORRECCIONES_ES3.md` §13 |
| Sesiones: logout en todas las páginas protegidas, expiración | ✅ JWT 60 min + logout global |
| TLS y cifrado en tránsito | ✅ Render HTTPS |
| **Logs de auditoría (Ley de Delitos Informáticos)** | ⚠️ **Parcial**: falta bitácora de accesos y cambios |
| **Cifrado de datos sensibles en reposo** | ⚠️ Solo contraseñas; el resto en texto claro (consentimiento, correos) |
| **Conexiones a BD por nivel de confianza** | ⚠️ Un solo usuario de BD |
| Cookies con dominio/ruta estrictos | N/A (JWT en `localStorage`, sin cookies) → **justificarlo** en el informe |

---

## 4. ES4 · Rúbrica del Informe (25%) — el faltante principal

| Dimensión | Estado |
|---|---|
| Diagramas UML Adaptativos (incluye, corrige **y adapta** los del ES2) | ❌ No existe el informe. Falta el **desafío de roles** que pide la guía como ejemplo: *«Desarrollador frontend no disponible → backend asume fullstack → actualizar responsabilidades en el diagrama de secuencia → funcionalidad con 1 semana de retraso»* |
| Diagramas de **Actividades** y de **Paquetes** | ⚠️ El ES2 tiene un diagrama de Actividades (Figura 15, «Publicar tutorial») y una Vista de Desarrollo por componentes, pero **no hay diagrama de Paquetes**. La guía pide ambos «correctamente elaborados y coherentes con los requerimientos» |
| Pruebas funcionales según la guía | Ver §5 |
| Reporte con resultados de las pruebas | ❌ No existe como documento (solo `casos_por_rf.md`, que es trazabilidad, no reporte con hallazgos/no conformidades) |
| Formato y condiciones del informe | ❌ Falta por completo: portada, índice, glosario, bibliografía **APA**, redacción en **tercera persona**, Calibrí 11, interlineado 1,5, justificado, márgenes 2,5 / 3 cm |

**Plantilla disponible**: el DOCX embebido trae la estructura exacta
(Introducción, Objetivo, Desarrollo, Conclusiones, Referencias) y las normas de
forma. La guía exige «estructura definida en su totalidad y no se recibirán
documentos incompletos» y «redactado en tercera persona».

**Bibliografía mínima que la propia guía entrega** (citar en APA 6ª):
OWASP (Prácticas de Codificación Segura), Pressman (2010), Sommerville (2011).

---

## 5. Las 7 pruebas funcionales exigidas

| Tipo | Exigencia de la guía | Estado | Falta |
|---|---|---|---|
| Unitarias | pytest, **>80% cobertura** | ✅ **97%** de cobertura real (núcleo `sysmon`), **99 pruebas** de backend + **59** de interfaz, umbral CI 90% | Reportar la medición con `pytest-cov` en el informe |
| Integración | APIs, servicios externos, BD | ✅ 99 pruebas sobre **PostgreSQL** de prueba con migración Alembic real | Declarar qué se consideró «servicio externo» (no hay ninguno) |
| Sistema | End-to-end + **pruebas de rendimiento** | ✅ **40/40** comprobaciones en `scripts/recorrido_http.py` contra la API real | ❌ **Pruebas de rendimiento/carga no realizadas** |
| **Penetración** | **OWASP ZAP**, vulnerabilidades conocidas, hallazgos y no conformidades | ❌ **No se ha ejecutado ZAP** | Ejecutar y documentar hallazgos |
| Autenticación | Login, sesiones, política de contraseñas | ✅ `test_login.py`, `test_autorizacion.py` | — |
| Autorización | Controles, escalación de privilegios, segregación | ✅ 401/403 en los 16 endpoints del panel | — |
| **Resultado** | Reporte de Testing con **solución y recomendaciones** | ❌ | Documentar hallazgos → corrección → recomendación (ISO 27002) |

---

## 6. Prioridades de cierre

| # | Acción | Impacto | Esfuerzo |
|---|---|---|---|
| **P0** | Redactar el **informe ES4** con la plantilla embebida: portada, índice, glosario, APA, tercera persona y formato | 25% de la nota | Alto |
| **P0** | Generar **diagrama de Paquetes** y la **adaptación de roles** sobre los diagramas del ES2 (secuencia, comunicación, actividades) | Dimensión central de la rúbrica | Medio |
| **P0** | Ejecutar **OWASP ZAP** contra `https://cosplay-chile-api.onrender.com` (ya operativa) y documentar hallazgos/no conformidades | Condición explícita de la guía | Medio |
| **P1** | Escribir el **Reporte de Testing** vinculando las 7 pruebas con las correcciones ya hechas y con ISO 27002 | Criterio 3.1.5, dos dimensiones | Medio |
| **P1** | Añadir secciones de **SaaS/IaaS/Cloud**, **ética y normativa** (Ley 19.223, 21.719, ISO 27000) | Criterios 3.1.1 y 3.1.2 | Bajo |
| ~~P1~~ | ~~**CI/CD** con GitHub Actions~~ → **HECHO**: `.github/workflows/ci.yml` con PostgreSQL 16, cobertura ≥90%, Vitest y build | Condición de la guía de prototipo | — |
| **P2** | Pruebas de **rendimiento** (p. ej. 100 peticiones concurrentes a `/api/salud` y al directorio) | Cierra «pruebas de sistema» | Bajo |
| **P2** | ~~Bitácora de auditoría~~ → **HECHA** (`/api/moderacion/auditoria`, Observer); queda justificar `localStorage` vs cookies | Sube el nivel OWASP | Bajo |
| **P2** | Cierre de seguridad post-clase: `DEMO_SEED=0`, borrar cuentas demo, revocar PAT | Riesgo real, no nota | Bajo |

---

## 7. Lo que ya juega a favor

- Prototipo funcional **desplegado en Render** con los módulos del ZIP + panel de administración, y verificado también en local.
- **99 pruebas de backend + 59 de interfaz**, **97% de cobertura** (por sobre el 80% exigido), puerta de CI en 90%.
- Control de acceso, hash argon2id, JWT, bloqueo por fuerza bruta, validación de
  entradas y sanitización de URLs: cubren A01, A02, A03 y **A07** de OWASP.
- Trazabilidad RF → prueba ya escrita en `backend/tests/casos_por_rf.md`
  (matriz de 23 filas, 99 pruebas), reutilizable como anexo del reporte de testing.
- Informe ES2 con 11 diagramas y 4 patrones de diseño documentados: base
  directa para los «diagramas adaptativos» que pide la ES4.
- `GUIA_DEMO.md` con recorrido 40/40 y evidencia de extremo a extremo; `DIAGNOSTICO_RENDER.md` con el sondeo del despliegue y `scripts/verificar_render.sh` para comprobarlo.
