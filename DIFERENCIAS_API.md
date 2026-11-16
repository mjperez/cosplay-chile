# Diferencias entre los contratos de API

Comparación entre **nuestro proyecto desplegado** (`/api/v1`, 49 rutas, SQLite, 169 pruebas) y el **backend incluido en el ZIP del diseño** (`/api`, 64 rutas consumidas por el frontend, PostgreSQL).

> "Contrato de API" = la forma exacta en que el frontend y el backend se entienden: URL, verbo, cuerpo enviado, campos devueltos y valores permitidos. Cambiar el diseño no lo cambia; cambiar de backend sí.

---

## 1. Prefijo y superficie de rutas

| | Nuestro proyecto | ZIP del diseño |
|---|---|---|
| Prefijo | `/api/v1/...` | `/api/...` |
| Implementación actual | 49 operaciones OpenAPI | 64 patrones de ruta usados por el frontend |
| Documentación | `/docs` con esquema generado | `/docs` con esquema generado |
| Salud | `GET /health` | `GET /api/salud` |

Ejemplos directos:

| Acción | Nuestro proyecto | ZIP del diseño |
|---|---|---|
| Login | `POST /api/v1/auth/login` | `POST /api/auth/login` |
| Listar guías | `GET /api/v1/contenido` | `GET /api/contenidos` |
| Categorías | `GET /api/v1/contenido/categorias` | `GET /api/categorias` |
| Eventos | `GET /api/v1/eventos` | `GET /api/eventos` |
| Foro | `GET /api/v1/foro/temas` | `GET /api/foros/{foro}/temas` |
| Notificaciones | `GET /api/v1/notificaciones` | `GET /api/notificaciones` |
| Auditoría | `GET /api/v1/admin/auditoria` | `GET /api/moderacion/auditoria` |
| Subir imagen | `POST /api/v1/archivos` | `POST /api/archivos` |

---

## 2. Autenticación

**Nuestro proyecto**

```json
// POST /api/v1/auth/login
{ "correo": "demo@cosplay.cl", "password": "Demo2026!" }

// 200
{
  "access_token": "...",
  "token_type": "bearer",
  "expires_in": 3600,
  "usuario": {
    "id_usuario": "…",
    "nombre": "Usuario Administrador",
    "correo": "demo@cosplay.cl",
    "rol": "administrador",
    "region": "Metropolitana",
    "activo": true,
    "creado_en": "…"
  }
}
```

**ZIP del diseño**

```json
// POST /api/auth/login
{ "email": "admin@cosplaychile.cl", "password": "Admin2026!" }

// 200
{
  "access_token": "...",
  "token_type": "bearer",
  "expira_en": 3600,
  "usuario": {
    "id": "…",
    "nombre": "…",
    "email": "admin@cosplaychile.cl",
    "rol": "ADMIN",
    "estado": "ACTIVO",
    "perfil": {
      "tipo_perfil": "COSPLAYER",
      "region": "METROPOLITANA",
      "avatar_url": null,
      "redes_sociales": [],
      "portafolio": [],
      "perfil_publico": false
    }
  }
}
```

Diferencias relevantes: `correo` vs `email`, `expires_in` vs `expira_en`, `id_usuario` vs `id`, roles en minúsculas (`administrador`, `cosplayer`) vs mayúsculas (`ADMIN`, `USUARIO`), y nuestro perfil es una sola estructura mientras el del ZIP tiene `tipo_perfil`, `estado`, `redes_sociales`, `portafolio`, etc.

Además, el ZIP tiene `POST /api/auth/recuperar`, `POST /api/auth/restablecer` y `GET /api/auth/me`; nosotros solo tenemos `login`, `registro` y `me` (en `/api/v1/auth/me`). El registro también cambia: el nuestro exige `region`, `acepta_privacidad` y `consentimiento_version`; el del ZIP usa `tipo_perfil`, `perfil_publico` y `acepta_privacidad`.

---

## 3. Paginación

```json
// Nuestro proyecto
{ "total": 20, "limite": 12, "desplazamiento": 0, "elementos": [ … ] }

// ZIP del diseño
{ "total": 20, "pagina": 1, "por_pagina": 12, "paginas": 2, "items": [ … ] }
```

El frontend del diseño lee `datos.items.length`, `datos.pagina` y `datos.paginas`. Con nuestra respuesta, `items` es `undefined` y la pantalla se queda vacía aunque el backend devuelva datos.

---

## 4. Contenidos (guías, entrevistas, artículos)

| Concepto | Nuestro proyecto | ZIP del diseño |
|---|---|---|
| Identificador | `id_contenido` | `id` |
| Categoría | `id_categoria` (UUID) | `categoria_id` (entrada) / `categoria: {id, nombre, slug, descripcion}` (salida) |
| Resumen | `resumen` | `descripcion` |
| Nivel | `basico`, `intermedio`, `avanzado` | `PRINCIPIANTE`, `INTERMEDIO`, `AVANZADO` |
| Tipo | `guia`, `entrevista`, `articulo` | `GUIA`, `ENTREVISTA`, `ARTICULO` |
| Imagen | `imagenes: string[]` (URLs absolutas) | `imagen_url` + `imagen_alt` obligatorio |
| Estado | `pendiente`, `publicado`, `rechazado` | `PENDIENTE`, `PUBLICADO`, `RECHAZADO` |
| Fecha | `creado_en` | `created_at` + `publicado_at` |
| Autor | `id_autor` / `nombre_autor` | `autor: {id, nombre}` |
| Extras del detalle | `personaje`, `medidas`, `tecnicas`, `presupuesto`, `seguridad` | `video_embed`, `pasos`, `materiales`, `entrevistado`, `preguntas`, `respuestas`, `enlaces`, `es_favorito` |

El ZIP además expone `GET /api/contenidos/mios`, `GET /api/contenidos/{id}/descargar` y `POST /api/contenidos` con un cuerpo distinto (`descripcion`, `categoria_id`, `pasos`, `materiales`, …). Nuestro editor envía `titulo`, `resumen`, `id_categoria`, `cuerpo`, `video_url` e `imagenes`.

---

## 5. Directorio, tiendas y grupos

Nuestro proyecto separa tres recursos:

- `GET /api/v1/proveedores` → `ProveedorPublico {id_proveedor, nombre, tipo, region, sitio_web, contacto, descripcion}`
- `GET /api/v1/tiendas` → `TiendaPublica {id_tienda, nombre, tipo, envia_a_chile, enlace_web, region}`
- `GET /api/v1/grupos` → `GrupoPublico {id_comunidad, nombre, region, plataforma, enlace}`

El ZIP los unifica en **una sola entidad** `directorio_item` con `tipo = PROVEEDOR | TIENDA | COMUNIDAD`, y añade campos que nosotros no tenemos: `comuna`, `imagen_url`, `imagen_alt`, `especialidades`, `tipos_producto`, `alcance`, `precio_desde/hasta`, `lat/lng`, `promedio`, `total_resenas`, `servicios`, `portafolio`, `direccion`, `perfil_usuario_id`, `resenas[]`, `es_favorito`, `puede_resenar`, `ya_resenado`.

También tiene rutas que no existen aquí: `GET /api/directorio/mapa`, `GET/PUT /api/directorio/mi-ficha` y `POST /api/directorio/{id}/resenas`.

---

## 6. Eventos

| | Nuestro proyecto | ZIP del diseño |
|---|---|---|
| Lista | `GET /api/v1/eventos?tipo&desde&hasta` | `GET /api/eventos?tipo&desde&hasta&por_pagina` |
| Identificador | `id_evento` | `id` |
| Fechas | `fecha_inicio` / `fecha_fin` son `datetime` | son `date` |
| Estado | no se expone en el resumen | `estado: PUBLICADO/PENDIENTE` |
| Campos extra | `total_participantes`, `creado_en` | `comuna`, `lat/lng`, `enlace_oficial`, `imagen_url/alt`, `sugerido_por`, `asistentes`, `asistire`, `es_favorito` |
| Inscripción | `POST /api/v1/eventos/{id}/participar` con `{personaje}` | `POST /api/eventos/{id}/asistir` (devuelve `{asistire, asistentes}`) |
| Sugerencias | no existe | `POST /api/eventos/sugerir` + `GET /api/eventos/sugerir` |

---

## 7. Foro y desafíos

| | Nuestro proyecto | ZIP del diseño |
|---|---|---|
| Foros | categorías fijas en el tema | entidad `foro` con `id`, `titulo`, `slug`, `categoria`, `temas`, `ultima_actividad` |
| Rutas | `/api/v1/foro/temas` | `/api/foros`, `/api/foros/{slug}/temas`, `/api/temas/{id}`, `/api/temas/{id}/respuestas` |
| Tema | `id_tema`, `id_creador`, `categoria`, `contenido`, `estado`, `nombre_autor`, `total_respuestas` | `id`, `autor {id,nombre}`, `respuestas`, `tiene_imagen`, `foro_slug`, `foro_titulo`, fotos con créditos |
| Cierre | `POST /api/v1/foro/temas/{id}/cerrar` | no tiene ruta equivalente; `oculto` se gestiona desde moderación |
| Desafío | `mes: "2026-11"`, `id_desafio`, `id_ganador` | `mes: 11`, `anio: 2026`, `abierto`, `ganador`, `participaciones`, `ya_participo` |
| Participar | no existe como ruta pública | `POST /api/desafios/{id}/participar` con foto + créditos obligatorios |

---

## 8. Notificaciones

```json
// Nuestro proyecto: GET /api/v1/notificaciones
{
  "total": 4, "sin_leer": 2, "limite": 15, "desplazamiento": 0,
  "elementos": [
    { "id_notificacion": "…", "tipo": "…", "titulo": "…", "mensaje": "…",
      "id_recurso": "…", "leida": false, "creado_en": "…" }
  ]
}

// ZIP del diseño: GET /api/notificaciones?limite=15
{
  "no_leidas": 2,
  "items": [
    { "id": "…", "tipo": "…", "mensaje": "…", "enlace": "/guias/…",
      "leida": false, "created_at": "…" }
  ]
}
```

Cambios además del nombre del array: el ZIP no devuelve `titulo` ni `id_recurso`, sí devuelve `enlace` para navegar al abrir la campana, y usa `created_at`. Para marcar leídas: nosotros usamos `PATCH /api/v1/notificaciones/{id}/leer`; el diseño usa `POST /api/notificaciones/{id}/leer` y además `POST /api/notificaciones/leer-todas` (que aquí no existe).

---

## 9. Archivos

| | Nuestro proyecto | ZIP del diseño |
|---|---|---|
| Subida | `POST /api/v1/archivos` | `POST /api/archivos` |
| Respuesta | `{identificador, enlace, tipo_mime, tamano}` | `{clave, url}` |
| Borrado | `DELETE /api/v1/archivos/{identificador}` | no expone borrado |
| Tipos | PNG, JPEG, WebP (magic bytes) | PNG, JPEG, WebP (magic bytes) |
| Límite | 5 MB | 5 MB (`MAX_UPLOAD_MB`) |

`SubirImagen.jsx` del diseño hace `onSubida({ url: r.url, alt })`: con nuestra respuesta, `r.url` es `undefined`.

---

## 10. Perfil

| | Nuestro proyecto | ZIP del diseño |
|---|---|---|
| Ver el propio | `GET /api/v1/perfiles/mio` | `GET /api/perfil` |
| Editar | `PUT /api/v1/perfiles/mio` | `PATCH/PUT /api/perfil` (según pantalla) |
| Ver ajeno | `GET /api/v1/perfiles/{id_usuario}` | `GET /api/perfil/{id}` |
| Campos | `especialidad`, `portafolio_url`, `biografia`, `region` (texto libre) | `tipo_perfil`, `biografia`, `region` (enum), `redes_sociales[]`, `portafolio: [{url, alt}]`, `especialidad`, `disponibilidad`, `avatar_url`, `perfil_publico` |
| Borrar cuenta | no existe | `DELETE /api/perfil` (anonimización, Ley 21.719) |

El ZIP additionally vincula la ficha pública del directorio con el perfil mediante `/api/directorio/mi-ficha`.

---

## 11. Administración, moderación y auditoría

| Funcionalidad | Nuestro proyecto | ZIP del diseño |
|---|---|---|
| Resumen | `GET /api/v1/admin/resumen` (15 contadores) | `GET /api/moderacion/resumen` (4 contadores) |
| Cola editorial | `/api/v1/admin/contenido`, `/publicar`, `/rechazar`, `/borrador` | `/api/moderacion/contenidos`, `/publicar`, `/rechazar` |
| Eventos | `/api/v1/admin/eventos` | `/api/moderacion/eventos/{id}/{decision}` |
| Foro | `/api/v1/admin/foro/temas` | ocultar desde reportes |
| Usuarios | `/api/v1/admin/usuarios`, activar/desactivar con `activo: bool` | `/api/moderacion/usuarios`, `suspender` con `{motivo}`, `reactivar`, estados `ACTIVO/SUSPENDIDO/ELIMINADO` |
| Reportes | **no existe** | `/api/reportes`, `/api/moderacion/reportes?estado=`, `/resolver` |
| Contacto | **no existe** | `/api/contacto`, `/api/moderacion/contactos`, `/atender` |
| Auditoría | `/api/v1/admin/auditoria` → `{total, elementos:[{id_registro, ocurrido_en, categoria, tipo_evento, correo_actor, id_recurso, detalle, ip_origen}]}` | `/api/moderacion/auditoria` → `{items:[{id, evento, actor, detalle, created_at}]}` |

---

## 12. Rutas que solo existen en el ZIP

Estas son las que el frontend del diseño llama y nuestro backend no tiene en absoluto:

- `GET /api/inicio` — estadísticas, novedades, próximos eventos, temas destacados, trajes recientes y desafío actual para la portada.
- `GET /api/meta` — regiones y etiquetas para los `<select>` del diseño.
- `GET /api/busqueda/sugerencias?q=` — autocompletado global de la portada.
- `GET/POST/DELETE /api/favoritos…` y `GET /api/favoritos/ids`.
- `POST /api/reportes`.
- `POST /api/contacto`.
- `POST /api/auth/recuperar`, `POST /api/auth/restablecer`.
- `GET /api/directorio/mapa`, `GET/PUT /api/directorio/mi-ficha`, `POST /api/directorio/{id}/resenas`.
- `POST /api/eventos/sugerir`, `POST /api/eventos/{id}/asistir`.
- `GET /api/foros`, `POST /api/foros/{foro}/temas`, `GET /api/temas/{id}`, `POST /api/temas/{id}/respuestas`.
- `POST /api/desafios/{id}/participar`.
- Prácticamente todo `/api/moderacion/*` (reportes, contactos, suspensiones, eventos pendientes, desafíos, bitácora).
- `POST /api/notificaciones/leer-todas`.
- `GET /api/contenidos/mios`, `GET /api/contenidos/{id}/descargar`.

---

## 13. Modelo de datos y tecnología (detrás del contrato)

| | Nuestro proyecto | ZIP del diseño |
|---|---|---|
| ORM | SQLAlchemy síncrono | SQLAlchemy async |
| Base de datos | SQLite (Render, archivo local) | PostgreSQL (`asyncpg`, JSONB, índices GIN) |
| Contraseñas | bcrypt (`BCRYPT_ROUNDS`) | argon2 (`pwdlib`) |
| Migraciones | Alembic `migrations/versions/0001…0005` | Alembic `alembic/versions/0001` |
| Modelos de usuario | `usuario`, `perfil_cosplayer`, `proveedor`, `tienda`, `grupo`, `contenido` + tablas hijas | `usuario`, `perfil`, `directorio_item`, `contenido` con columnas JSONB |
| Nombres de tabla en común | `usuario`, `contenido`, `notificacion`, `evento`, `desafio_mensual` | los mismos, con columnas distintas |

Esto último importa: **no se pueden ejecutar ambos backends sobre la misma base de datos** porque usan las mismas tablas con esquemas incompatibles. Cada uno necesita su propia base o su propio archivo SQLite.

---

## 14. Consecuencia práctica

Copiar el frontend del diseño y conectarlo a `/api/v1` sin más produciría, entre otros:

1. Login: el frontend envía `email`, nuestro endpoint espera `correo` → **422**.
2. Campana: pide `/api/notificaciones?limite=15` → **404**.
3. Guías: lee `datos.items` → lista vacía aunque haya 20 contenidos.
4. Subida de imagen: lee `r.url`, nuestro JSON trae `enlace` → imagen no se muestra.
5. Portada, búsqueda, favoritos, reportes, contacto, seguridad y moderación avanzada → **404** o pantallas vacías.

Por eso la integración exige una de estas vías: **traducir** las diferencias (capa de compatibilidad sobre nuestro backend), **adoptar** el backend del ZIP, o **limitar** la integración a la capa visual.
