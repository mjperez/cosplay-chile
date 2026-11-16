"""Seed Fase 1: categorías, usuarios demo, directorio por región y calendario."""
from datetime import date, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models import (
    CategoriaContenido,
    ComunidadGrupo,
    Evento,
    ParticipacionEvento,
    Perfil,
    ProveedorServicio,
    Resena,
    Tienda,
    Usuario,
)
from app.models.enums import Rol, normalizar
from app.seed import datos_base as D
from app.services.directorio_sync import sincronizar_ficha


async def seed_base(s: AsyncSession, ctx: dict) -> None:
    img = ctx["imagenes"]

    ctx["categorias"] = {}
    for slug, nombre, desc in D.CATEGORIAS:
        c = CategoriaContenido(slug=slug, nombre=nombre, descripcion=desc)
        s.add(c)
        ctx["categorias"][slug] = c

    ctx["usuarios"] = {}
    for clave, nombre, email, rol, estado, tipo, region, publico, bio in D.USUARIOS:
        u = Usuario(
            nombre=nombre, email=email, rol=rol, estado=estado,
            password_hash=hash_password(D.CLAVE_ADMIN if rol == Rol.ADMIN else D.CLAVE_DEMO),
            motivo_suspension="Infracción reiterada a las normas comunitarias (demo)." if clave == "suspendido" else None,
        )
        u.perfil = Perfil(tipo_perfil=tipo, region=region, perfil_publico=publico, biografia=bio,
                          redes_sociales=[{"red": "Instagram", "url": f"https://instagram.example/{clave}"}],
                          portafolio=[])
        s.add(u)
        ctx["usuarios"][clave] = u
    await s.flush()

    # Fichas del directorio creadas por opt-in (RF-10) y luego completadas
    joaquin = ctx["usuarios"]["joaquin"]
    joaquin.perfil.portafolio = [{"url": img["armadura"][0], "alt": img["armadura"][1]},
                                 {"url": img["concurso"][0], "alt": img["concurso"][1]}]
    ficha = ficha_joaquin = await sincronizar_ficha(s, joaquin)
    lat, lng = D._coord("Concepción", 0.01)
    ficha.comuna, ficha.lat, ficha.lng = "Concepción", lat, lng
    ficha.servicios = ["Trajes completos por encargo", "Patronaje para todos los cuerpos", "Arreglos para concursos"]
    ficha.precio_desde, ficha.precio_hasta = 45000, 380000
    ficha.contacto = "joaquin@demo.cl"
    ficha.imagen_url, ficha.imagen_alt = img["confeccion"]
    ficha.especialidades = ["COSMAKER", "SASTRERIA"]

    tienda_u = ctx["usuarios"]["tienda"]
    ficha = await sincronizar_ficha(s, tienda_u)
    lat, lng = D._coord("Valparaíso", -0.004)
    ficha.comuna, ficha.direccion, ficha.lat, ficha.lng = "Valparaíso", "Av. Pedro Montt 1234", lat, lng
    ficha.tipos_producto = ["TELAS", "ACCESORIOS"]
    ficha.alcance, ficha.envia_a_chile, ficha.tienda_fisica = "NACIONAL", True, True
    ficha.contacto = "tienda@demo.cl"
    ficha.sitio_web = "https://telasdelpuerto.example"
    ficha.imagen_url, ficha.imagen_alt = img["tienda"]

    ctx["directorio"] = {"Joaquín Huenchumán": ficha_joaquin, "Telas del Puerto": ficha}
    for i, p in enumerate(D.PROVEEDORES):
        lat, lng = D._coord(p["comuna"], 0.006 * (i % 3))
        item = ProveedorServicio(
            nombre=p["nombre"], descripcion=p["desc"], region=p["region"], comuna=p["comuna"],
            contacto=p["contacto"], sitio_web=p["web"], lat=lat, lng=lng, especialidades=p["esp"],
            servicios=p["servicios"], precio_desde=p["precio"][0], precio_hasta=p["precio"][1],
            portafolio=[{"url": img[p["img"]][0], "alt": img[p["img"]][1]}],
            imagen_url=img[p["img"]][0], imagen_alt=img[p["img"]][1],
        )
        s.add(item)
        ctx["directorio"][p["nombre"]] = item
    for t in D.TIENDAS:
        lat, lng = D._coord(t["comuna"], -0.005) if t["comuna"] else (None, None)
        item = Tienda(
            nombre=t["nombre"], descripcion=t["desc"], region=t["region"], comuna=t["comuna"],
            contacto=t["contacto"], sitio_web=t["web"], lat=lat if t["fisica"] else None,
            lng=lng if t["fisica"] else None, tipos_producto=t["tipos"], alcance=t["alcance"],
            envia_a_chile=True, tienda_fisica=t["fisica"], imagen_url=img["tienda"][0], imagen_alt=img["tienda"][1],
        )
        s.add(item)
        ctx["directorio"][t["nombre"]] = item
    for g in D.COMUNIDADES:
        lat, lng = D._coord(g["comuna"], 0.003)
        item = ComunidadGrupo(
            nombre=g["nombre"], descripcion=g["desc"], region=g["region"], comuna=g["comuna"],
            plataforma=g["plataforma"], sitio_web=g["web"], lat=lat, lng=lng,
            imagen_url=img["comunidad"][0], imagen_alt=img["comunidad"][1],
        )
        s.add(item)
        ctx["directorio"][g["nombre"]] = item

    hoy = date.today()
    ctx["eventos"] = {}
    for dias, duracion, nombre, tipo, region, comuna, lugar, desc, estado, imagen in D.EVENTOS:
        inicio = hoy + timedelta(days=dias)
        lat, lng = D._coord(comuna, 0.002)
        slug = normalizar(nombre.split(":")[0]).replace(" ", "-")[:40].strip("-")
        ev = Evento(
            nombre=nombre, tipo=tipo, region=region, comuna=comuna, lugar=lugar, descripcion=desc,
            fecha_inicio=inicio, fecha_fin=inicio + timedelta(days=duracion - 1) if duracion > 1 else None,
            lat=lat, lng=lng, enlace_oficial=f"https://{slug}.example/entradas", estado=estado,
            imagen_url=img[imagen][0], imagen_alt=img[imagen][1],
            creado_por=ctx["usuarios"]["camila" if estado == "PENDIENTE" else "admin"],
        )
        s.add(ev)
        ctx["eventos"][nombre] = ev
    await s.flush()

    # Reseñas (RF-19) y asistencias de ejemplo
    u = ctx["usuarios"]
    d = ctx["directorio"]
    resenas = [
        ("camila", "Taller Kintsugi Props", 5, "Me hicieron un escudo liviano y adaptaron las correas a mi espalda. Muy recomendable."),
        ("rocio", "Taller Kintsugi Props", 4, "Buen trabajo y cumplieron el plazo. La pintura quedó increíble."),
        ("valentina", "Hilo Rojo Sastrería Cosplay", 5, "Adaptaron mi traje a la silla de ruedas sin que perdiera el diseño."),
        ("benja", "Hilo Rojo Sastrería Cosplay", 5, "Patronaje perfecto para crossplay."),
        ("antonia", "EVA Center Chile", 4, "Buen stock de goma EVA de alta densidad. El despacho a Valparaíso tardó 3 días."),
        ("camila", "EVA Center Chile", 5, "Precios claros y te asesoran si eres principiante."),
        ("ignacia", "Lente Austral Fotografía", 5, "Sesión preciosa en el estrecho. Muy respetuosa con los tiempos."),
        ("rocio", "Costura Inclusiva Temuco", 5, "Por fin un traje en mi talla sin cobrar recargo."),
        ("matias", "Mercería Los Andes", 3, "Buenos precios, pero hay que ir temprano porque se llena."),
        ("camila", "Joaquín Huenchumán", 5, "Mi traje del concurso quedó impecable."),
    ]
    for autor, item, nota, comentario in resenas:
        s.add(Resena(usuario=u[autor], directorio_item_id=d[item].id, calificacion=nota, comentario=comentario))
    for autor, evento in [("camila", "Convención Andina de Cultura Pop"), ("valentina", "Meetup Cosplay Adaptativo"),
                          ("rocio", "Feria Otaku Temuco"), ("camila", "Taller de goma EVA para principiantes")]:
        s.add(ParticipacionEvento(usuario_id=u[autor].id, evento_id=ctx["eventos"][evento].id, rol="asistente"))
    await s.flush()
