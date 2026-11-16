"""Seed Fase 4: foros, historias, desafíos, reportes, contacto y bitácora."""
from datetime import date, datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    Contacto,
    DesafioMensual,
    Foro,
    ParticipacionDesafio,
    RegistroAuditoria,
    Reporte,
    Respuesta,
    Tema,
)

FOROS = [
    ("principiantes", "Dudas de principiantes", "Preguntas básicas sin miedo: aquí todos empezamos alguna vez."),
    ("confeccion", "Confección y patronaje", "Costura, telas, patrones y ajustes para todos los cuerpos."),
    ("props", "Props y armaduras", "Goma EVA, termoplásticos, impresión 3D y pintura."),
    ("maquillaje-pelucas", "Maquillaje y pelucas", "Caracterización, FX, lentes y estilizado de pelucas."),
    ("concursos", "Concursos y escenificación", "Consejos para pasarela, performance y jurados."),
    ("historias", "Historias de cosplayers", "Cuéntanos cómo llegaste al cosplay (RF-26, RF-29)."),
    ("compras", "Dónde comprar", "Datos de tiendas, precios y envíos en Chile."),
]

# (foro, autor, título, contenido, imagen, créditos, días atrás, [(autor, respuesta)])
TEMAS = [
    ("principiantes", "camila", "¿Qué personaje me recomiendan para mi primer cosplay?",
     "Tengo poco presupuesto y nunca he cosido. Me gusta el anime de fantasía. ¿Algún consejo para elegir?", None, None, 1,
     [("benja", "Elige uno con ropa que puedas adaptar de segunda mano. Así te enfocas en un solo accesorio."),
      ("rocio", "La guía «Cómo elegir tu primer personaje» me ayudó mucho. ¡Tú puedes!")]),
    ("historias", "valentina", "Cómo llegué al cosplay desde mi silla de ruedas",
     "Hace cinco años vi a una cosplayer en silla en una convención y pensé: yo también puedo. Mi primer traje fue una "
     "princesa y la silla fue su carruaje. Hoy organizo meetups adaptativos en Arica.",
     "grupo-diverso", ("Ignacia Pérez", "Valentina Quispe"), 3,
     [("camila", "¡Qué inspirador! Gracias por compartir."),
      ("matias", "Si necesitas ayuda con props livianos para la silla, escríbeme.")]),
    ("historias", "rocio", "Mi primer cosplay de talla grande",
     "Durante años pensé que el cosplay no era para cuerpos como el mío. Hasta que encontré una comunidad que me apoyó. "
     "Ahora comparto patrones adaptados.", None, None, 6,
     [("antonia", "Tus patrones son geniales, los usé para mi último traje.")]),
    ("props", "matias", "Foto: armadura terminada para el concurso del sur",
     "Les comparto el resultado final de la armadura que construí con EVA de 10 mm. ¡Gracias por los consejos del foro!",
     "armadura", ("Ignacia Pérez", "Matías Soto"), 2,
     [("joaquin", "¡Impecable el envejecido! ¿Qué lavado usaste?"),
      ("matias", "Acrílico negro diluido en agua, y lo retiro con un paño húmedo.")]),
    ("props", "camila", "La goma EVA se me cuartea al pintar",
     "Pinté mi corona y al doblarla se agrietó la pintura. ¿Qué hice mal?", None, None, 4,
     [("matias", "Te faltó sellar. Usa tres capas finas de cola fría o imprimante flexible antes de pintar.")]),
    ("confeccion", "rocio", "Patrones de capa para todas las tallas",
     "Armé una tabla para adaptar el patrón de capa de media circunferencia a cualquier contorno de hombros. "
     "¿Les sirve que la publique como guía?", None, None, 8,
     [("camila", "¡Sí, por favor!"), ("joaquin", "Muy útil. Súmale cómo agregar forro.")]),
    ("maquillaje-pelucas", "antonia", "Base para pieles morenas en cosplay de fantasía",
     "Para personajes de piel azul o verde en pieles morenas recomiendo una base naranja correctora primero. "
     "¿Qué marcas usan ustedes?", None, None, 5, []),
    ("concursos", "benja", "Checklist para el día del concurso",
     "Kit de reparación, música en dos formatos, agua, colación y llegar dos horas antes. ¿Qué más agregarían?",
     "concurso", ("Fotos en Ruta Iquique", "Benjamín Torres"), 7,
     [("valentina", "Confirmar con la organización que el escenario sea accesible."),
      ("camila", "Una copia impresa de la ficha técnica.")]),
    ("compras", "camila", "¿Dónde comprar EVA de alta densidad en regiones?",
     "Vivo en Rancagua y no encuentro EVA de 10 mm. ¿Alguna tienda que envíe?", None, None, 9,
     [("matias", "En el directorio está EVA Center Chile, envía a todo Chile.")]),
    ("principiantes", "camila", "Busco grupo para ir a la convención",
     "Es mi primera convención y me da nervio ir sola. ¿Alguien de Santiago que quiera ir en grupo?", None, None, 0,
     [("benja", "En «Crossplay y Diversidad Chile» siempre organizamos grupos para ir juntos.")]),
]


async def seed_comunidad(s: AsyncSession, ctx: dict) -> None:
    u, img = ctx["usuarios"], ctx["imagenes"]
    ahora = datetime.now(timezone.utc)

    foros = {}
    for orden, (slug, titulo, desc) in enumerate(FOROS):
        foros[slug] = Foro(slug=slug, titulo=titulo, categoria=desc, orden=orden)
        s.add(foros[slug])
    await s.flush()

    temas = {}
    for foro, autor, titulo, texto, imagen, creditos, dias, respuestas in TEMAS:
        t = Tema(foro_id=foros[foro].id, autor=u[autor], titulo=titulo, contenido=texto,
                 created_at=ahora - timedelta(days=dias, hours=3))
        if imagen:
            t.imagen_url, t.imagen_alt = img[imagen]
            t.credito_fotografo, t.credito_cosplayer = creditos
        s.add(t)
        temas[titulo] = t
        await s.flush()
        for i, (autor_r, texto_r) in enumerate(respuestas):
            s.add(Respuesta(tema_id=t.id, autor=u[autor_r], contenido=texto_r,
                            created_at=t.created_at + timedelta(hours=i + 1)))
    # Respuesta problemática para la demo de moderación
    spam = Respuesta(tema_id=temas["Busco grupo para ir a la convención"].id, autor=u["suspendido"],
                     contenido="Vendo entradas falsas baratas, escríbeme por interno.", created_at=ahora - timedelta(hours=2))
    s.add(spam)
    await s.flush()

    # Desafíos mensuales (RF-36): el del mes actual (abierto) y el anterior (con ganador)
    hoy = date.today()
    ant_mes, ant_anio = (12, hoy.year - 1) if hoy.month == 1 else (hoy.month - 1, hoy.year)
    actual = DesafioMensual(titulo="Cosplay con materiales reciclados",
                            descripcion="Crea o mejora un traje usando al menos un 50 % de materiales reciclados: cartón, "
                                        "botellas, ropa de segunda mano. Sube tu foto con créditos al fotógrafo.",
                            mes=hoy.month, anio=hoy.year)
    anterior = DesafioMensual(titulo="Personaje de leyenda chilena",
                              descripcion="Interpreta un personaje de la mitología o las leyendas de Chile.",
                              mes=ant_mes, anio=ant_anio, ganador=u["valentina"])
    s.add_all([actual, anterior])
    await s.flush()
    participaciones = [
        (actual, "camila", "Armadura de cartón corrugado", "Hecha con cajas de mudanza y pintura acrílica.", "armadura",
         ("Ignacia Pérez", "Camila Rojas")),
        (actual, "rocio", "Capa con ropa de segunda mano", "Tres chalecos de feria cosidos en una capa.", "confeccion",
         ("Autorretrato", "Rocío Catalán")),
        (anterior, "valentina", "La Pincoya sobre ruedas", "Mi silla fue el mar de Chiloé.", "grupo-diverso",
         ("Fotos en Ruta Iquique", "Valentina Quispe")),
        (anterior, "benja", "El Caleuche", "Barco fantasma con luces LED.", "evento", ("Lente Austral", "Benjamín Torres")),
    ]
    for desafio, autor, titulo, desc, imagen, (foto, cos) in participaciones:
        s.add(ParticipacionDesafio(desafio_id=desafio.id, usuario=u[autor], titulo=titulo, descripcion=desc,
                                   imagen_url=img[imagen][0], imagen_alt=img[imagen][1],
                                   credito_fotografo=foto, credito_cosplayer=cos))

    # Reportes abiertos y contacto para la demo del panel de moderación
    s.add_all([
        Reporte(reportante_id=u["camila"].id, tipo_objeto="RESPUESTA", objeto_id=spam.id, motivo="SPAM",
                detalle="Está ofreciendo entradas falsas."),
        Reporte(reportante_id=u["rocio"].id, tipo_objeto="EVENTO",
                objeto_id=ctx["eventos"]["Meetup Cosplay Valpo en el Parque Italia"].id, motivo="ACTUALIZACION_EVENTO",
                detalle="El meetup se cambió al Parque Alemania por trabajos en el Parque Italia."),
        Contacto(nombre="Cuenta Suspendida", email="suspendido@demo.cl", tipo="CUENTA",
                 asunto="Mi cuenta aparece suspendida",
                 mensaje="Hola, no puedo ingresar. Creo que es un error, ¿pueden revisar mi caso?"),
        Contacto(nombre="Fernanda", email="fernanda@correo.example", tipo="SUGERENCIA",
                 asunto="Guías en lengua de señas", mensaje="Sería genial tener videos con interpretación en lengua de señas."),
    ])
    s.add_all([
        RegistroAuditoria(evento="USUARIO_REGISTRADO", actor_id=u["camila"].id, detalle={"tipo_perfil": "COSPLAYER"},
                          created_at=ahora - timedelta(days=20)),
        RegistroAuditoria(evento="USUARIO_SUSPENDIDO", actor_id=u["admin"].id,
                          detalle={"usuario_id": str(u["suspendido"].id), "motivo": "Infracción reiterada a las normas comunitarias"},
                          created_at=ahora - timedelta(days=1)),
        RegistroAuditoria(evento="NUEVO_TUTORIAL", actor_id=u["camila"].id,
                          detalle={"titulo": "Orejas de zorro con alambre y peluche"}, created_at=ahora - timedelta(hours=5)),
    ])
    await s.flush()
