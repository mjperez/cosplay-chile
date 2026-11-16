"""Seed Fase 2: guías, entrevistas y artículos (RF-02, 03, 18, 20, 21, 26, 28, 39)."""
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ArticuloTecnico, Entrevista, GuiaTutorial, Notificacion

P, I, A = "PRINCIPIANTE", "INTERMEDIO", "AVANZADO"

CONTENIDOS = [
    # (clase, autor, categoría, nivel, imagen, título, descripción, cuerpo, campos propios, estado)
    (GuiaTutorial, "camila", "eleccion-personaje", P, "grupo-diverso",
     "Cómo elegir tu primer personaje",
     "Una guía para escoger un personaje que disfrutes, que calce con tu presupuesto y con el tiempo que tienes.",
     "No existe un personaje «correcto» para tu cuerpo, tu género o tu edad: el cosplay es para todas las personas.\n\n"
     "Para un primer proyecto conviene elegir un traje que te entusiasme, pero con pocas piezas rígidas. "
     "Así aprendes técnicas básicas sin frustrarte.\n\n"
     "Si usas silla de ruedas, bastón u otra ayuda técnica, piensa en ella como parte del diseño: muchas personas la "
     "transforman en un trono, una nave o una montura.",
     dict(pasos=["Haz una lista de 5 personajes que te gusten de verdad",
                 "Busca imágenes de referencia de frente, espalda y perfil",
                 "Separa el traje en piezas: ropa, accesorios, peluca y maquillaje",
                 "Marca qué piezas puedes comprar, reciclar o hacer tú",
                 "Calcula tiempo y costo estimado (ver guía de presupuesto)",
                 "Elige el que mejor equilibre ganas, tiempo y presupuesto"],
          materiales=["Cuaderno o planilla", "Imágenes de referencia", "Calendario de eventos"]), "PUBLICADO"),
    (GuiaTutorial, "rocio", "medidas", P, "confeccion",
     "Toma de medidas para trajes que calcen en todos los cuerpos",
     "Qué medidas tomar, cómo hacerlo sin ayuda y cómo adaptarlas a patrones comerciales.",
     "Los patrones vienen en tallas estándar, pero los cuerpos reales no. Tomar bien tus medidas evita la mayoría de "
     "los ajustes de último minuto.\n\n"
     "Mide sobre ropa interior ajustada, con la huincha firme pero sin apretar. Anota todo en centímetros y fecha tus "
     "medidas: cambian con el tiempo y está bien.\n\n"
     "Si haces cosplay sentada o sentado, mide también en esa posición: el largo de espalda y de pierna cambian.",
     dict(pasos=["Contorno de busto o pecho por la parte más ancha", "Contorno de cintura en la parte más angosta",
                 "Contorno de cadera por la parte más ancha", "Largo de espalda: de la nuca a la cintura",
                 "Largo de brazo con el codo levemente doblado", "Tiro y entrepierna (de pie y sentado si corresponde)",
                 "Compara con la tabla del patrón y elige la talla según la medida mayor"],
          materiales=["Huincha de medir flexible", "Espejo o celular con temporizador", "Cuaderno"]), "PUBLICADO"),
    (GuiaTutorial, "matias", "props-armaduras", P, "armadura",
     "Tu primera pieza de armadura en goma EVA",
     "Corta, sella y pinta un brazal de goma EVA con herramientas simples y materiales que encuentras en Chile.",
     "La goma EVA de alta densidad se vende en planchas en tiendas de manualidades y de insumos para cosplay. Para "
     "armaduras usa 5 a 10 mm.\n\n"
     "Trabaja en un lugar ventilado: el calor y los pegamentos de contacto liberan vapores. Usa mascarilla y gafas.",
     dict(pasos=["Haz el patrón en papel y pruébalo en tu brazo", "Traspasa el patrón a la EVA con plumón",
                 "Corta con cúter afilado en un solo movimiento", "Bisela los bordes en 45° para unir piezas",
                 "Une con pegamento de contacto (deja secar 10 minutos antes de juntar)",
                 "Termoforma con pistola de calor para darle curva",
                 "Sella con cola fría o imprimante flexible (3 capas)", "Pinta con acrílico y envejece con lavado oscuro"],
          materiales=["Goma EVA 5 mm", "Cúter y repuestos", "Pegamento de contacto", "Pistola de calor",
                      "Cola fría", "Pintura acrílica", "Mascarilla y gafas de seguridad"]), "PUBLICADO"),
    (GuiaTutorial, "camila", "confeccion", P, "confeccion",
     "Técnicas básicas de costura para cosplay",
     "Puntadas a mano, uso básico de máquina y cómo terminar costuras para que tu traje dure.",
     "No necesitas una máquina profesional para empezar. Muchas piezas se pueden hacer a mano con paciencia.\n\n"
     "Antes de cortar tu tela final, haz una prueba en tela barata (toile o muselina) para corregir el calce.",
     dict(pasos=["Lava y plancha la tela antes de cortar", "Prende el patrón con alfileres al hilo de la tela",
                 "Corta dejando 1,5 cm de margen de costura", "Hilvana a mano para probar",
                 "Cose a máquina con puntada recta", "Termina los bordes con zigzag para que no se deshilachen"],
          materiales=["Tela de prueba", "Tela final", "Alfileres", "Tijera de tela", "Hilo", "Máquina o aguja"]),
     "PUBLICADO"),
    (GuiaTutorial, "antonia", "maquillaje-pelucas", I, "maquillaje",
     "Estilizado básico de pelucas",
     "Cómo cortar, dar volumen y fijar una peluca sintética para que se parezca a tu personaje.",
     "Las pelucas resistentes al calor (hasta unos 180 °C) permiten usar plancha y secador con cuidado.\n\n"
     "Trabaja la peluca sobre una cabeza de espuma fijada a la mesa y corta siempre menos de lo que crees.",
     dict(pasos=["Desenreda con peineta de dientes anchos desde las puntas", "Corta el flequillo en seco, en vertical",
                 "Da volumen escarmenando la base de cada mechón", "Fija con laca fuerte y secador en frío",
                 "Para picos, usa pegamento textil en las puntas"],
          materiales=["Peluca resistente al calor", "Cabeza de espuma", "Tijera de pelo", "Laca fuerte",
                      "Peineta", "Pinches"]), "PUBLICADO"),
    (GuiaTutorial, "antonia", "maquillaje-pelucas", A, "maquillaje",
     "Maquillaje FX para todos los tonos de piel",
     "Efectos especiales de caracterización con productos que funcionan en pieles claras, morenas y oscuras.",
     "Muchos tutoriales usan solo pieles claras. Aquí ajustamos colores de base, rojos y morados para que los "
     "efectos se vean realistas en cualquier tono.\n\n"
     "Haz siempre una prueba de alergia 24 horas antes y retira el látex con aceite, nunca tirando.",
     dict(pasos=["Prueba de alergia en el antebrazo 24 horas antes", "Prepara la piel con hidratante sin aceite",
                 "Aplica látex en capas finas y seca con secador frío", "Usa correctores en tonos rojos más profundos en pieles oscuras",
                 "Sella con polvo translúcido adecuado a tu tono", "Retira con aceite desmaquillante"],
          materiales=["Látex líquido", "Paleta de correctores", "Esponjas", "Polvo translúcido", "Aceite desmaquillante"]),
     "PUBLICADO"),
    (GuiaTutorial, "valentina", "presupuesto", P, "presupuesto",
     "Presupuesto de un cosplay en pesos chilenos",
     "Planifica cuánto vas a gastar, dónde ahorrar y cómo evitar el sobrecosto de última hora.",
     "En la encuesta a la comunidad, el sobrecosto respecto a lo planeado fue una de las dificultades más repetidas. "
     "Una planilla simple ayuda mucho.\n\n"
     "Reutiliza ropa de segunda mano, compra planchas de EVA compartidas con tu grupo y suma siempre un 20 % de "
     "margen para imprevistos.",
     dict(pasos=["Lista cada pieza del traje", "Cotiza en 2 o 3 tiendas del directorio",
                 "Anota precio, despacho y tiempo de llegada", "Marca lo que puedes reciclar o pedir prestado",
                 "Suma 20 % de margen para imprevistos", "Revisa el presupuesto cada semana"],
          materiales=["Planilla de cálculo", "Directorio de tiendas de Cosplay Chile"]), "PUBLICADO"),
    (GuiaTutorial, "valentina", "seguridad-eventos", P, "seguridad",
     "Seguridad en eventos: acoso, transporte y salud",
     "Recomendaciones para disfrutar una convención de forma segura, desde que sales de casa hasta que vuelves.",
     "Cosplay no es consentimiento. Nadie puede tocarte, fotografiarte de forma invasiva ni comentar tu cuerpo sin "
     "tu permiso.\n\n"
     "Si vives o presencias acoso, aléjate, busca al staff del evento y, si quieres, denuncia. También puedes "
     "escribirnos desde el formulario de contacto.",
     dict(pasos=["Comparte tu ubicación con alguien de confianza",
                 "Planifica tu transporte de ida y vuelta (y una alternativa nocturna)",
                 "Lleva el traje en bolso si el trayecto es largo y cámbiate en el recinto",
                 "Hidrátate cada hora y come algo: los trajes dan calor",
                 "Identifica al staff, la enfermería y las salidas al llegar",
                 "Pide permiso antes de tomar fotos a otras personas y respeta un «no»",
                 "Si te sientes mal, quítate las piezas más pesadas y descansa"],
          materiales=["Botella de agua", "Colación", "Kit de reparación (cinta, alfileres, pegamento)",
                      "Celular con batería", "Bloqueador solar"]), "PUBLICADO"),
    (ArticuloTecnico, "matias", "seguridad-eventos", I, "seguridad",
     "Cuida tu salud al trabajar con pegamentos, resinas y lentes de contacto",
     "Ventilación, elementos de protección y por qué los lentes de fantasía requieren receta de especialista.",
     "El pegamento de contacto, las resinas y algunos imprimantes liberan compuestos que no conviene respirar. "
     "Trabaja con ventanas abiertas, usa mascarilla con filtro para vapores orgánicos y guantes de nitrilo.\n\n"
     "Los lentes de contacto de fantasía son dispositivos médicos: úsalos solo con indicación de un especialista, "
     "nunca los compartas y no superes las horas de uso recomendadas.",
     dict(enlaces=["https://www.minsal.cl", "https://www.ispch.cl"]), "PUBLICADO"),
    (ArticuloTecnico, "matias", "errores-comunes", P, "armadura",
     "Errores comunes con la goma EVA y cómo evitarlos",
     "Las fallas más frecuentes al construir props y armaduras, con su solución.",
     "Cortar con un cúter sin filo deja bordes desgarrados: cambia la hoja seguido.\n\n"
     "Pintar sin sellar hace que la pintura se cuartee al doblar la pieza: sella siempre con 3 capas finas.\n\n"
     "Unir piezas antes de que el pegamento de contacto esté seco al tacto hace que se despeguen. Espera.\n\n"
     "Armaduras demasiado rígidas impiden sentarse o subir escaleras: prueba la movilidad antes de pintar.",
     dict(enlaces=["https://es.wikipedia.org/wiki/Cosplay"]), "PUBLICADO"),
    (ArticuloTecnico, "rocio", "errores-comunes", P, "confeccion",
     "Errores frecuentes en la confección de trajes",
     "Desde la elección de telas hasta los cierres: lo que nadie te advierte en tu primer traje.",
     "No lavar la tela antes de cortar hace que encoja después: lávala siempre.\n\n"
     "Elegir telas sin elasticidad para trajes muy ajustados limita el movimiento. Prefiere telas con algo de elastano.\n\n"
     "Dejar los cierres para el final suele terminar en apuros. Piensa desde el principio cómo te vas a poner y "
     "sacar el traje, sobre todo si necesitas hacerlo sin ayuda.",
     dict(enlaces=["https://es.wikipedia.org/wiki/Costura"]), "PUBLICADO"),
    (ArticuloTecnico, "ignacia", "fotografia", I, "fotografia",
     "Cómo preparar una sesión de fotos cosplay",
     "Acuerdos previos, locaciones y créditos: lo básico para trabajar con una fotógrafa o fotógrafo.",
     "Antes de la sesión acuerden: locación, horario, cantidad de fotos editadas, plazos y uso de las imágenes.\n\n"
     "Al publicar, da siempre créditos al fotógrafo y al cosplayer. Es una forma de valorar el trabajo de ambos.",
     dict(enlaces=["https://es.wikipedia.org/wiki/Fotograf%C3%ADa"]), "PUBLICADO"),
    (ArticuloTecnico, "benja", "consejos-expertos", A, "concurso",
     "Consejos de jurado para tu primer concurso",
     "Qué miran los jurados, cómo preparar la ficha técnica y cómo manejar los nervios en el escenario.",
     "Los jurados suelen evaluar confección, fidelidad, interpretación y presencia escénica. Revisa siempre las bases.\n\n"
     "Prepara una ficha con fotos del proceso: demuestra tu trabajo y ayuda al jurado a valorar lo hecho a mano.\n\n"
     "Ensaya tu performance con el traje puesto. Lo que funciona en tu pieza puede ser incómodo con la armadura.",
     dict(enlaces=["https://es.wikipedia.org/wiki/Cosplay"]), "PUBLICADO"),
    (Entrevista, "admin", "escenificacion", I, "concurso",
     "Entrevista: crossplay y pasarela en el norte",
     "Benjamín Torres, crossplayer y jurado en Antofagasta, cuenta cómo prepara sus performances.",
     "Conversamos con Benjamín sobre crossplay, escenificación y el crecimiento de la escena del norte.",
     dict(entrevistado="Benjamín Torres",
          preguntas=["¿Cómo empezaste en el crossplay?", "¿Qué es lo más difícil de preparar una pasarela?",
                     "¿Qué le dirías a quien tiene miedo de hacer crossplay?"],
          respuestas=["Con un personaje de un anime que veía con mi hermana. Me pareció natural interpretarlo.",
                      "El tiempo: la pasarela dura un minuto y medio, pero ensayo semanas. Grabo cada ensayo.",
                      "Que el cosplay es interpretar, no parecerse. Busca comunidades seguras como la de Crossplay y Diversidad."]),
     "PUBLICADO"),
    (Entrevista, "admin", "historias", P, "grupo-diverso",
     "Entrevista: cosplay desde una silla de ruedas",
     "Valentina Quispe, cosplayer de Arica, comparte cómo integra su silla a cada personaje.",
     "Valentina hace cosplay hace cinco años y es parte de la comunidad Cosplay Adaptativo Chile.",
     dict(entrevistado="Valentina Quispe",
          preguntas=["¿Cómo integras tu silla a los trajes?", "¿Qué deberían mejorar los eventos?",
                     "¿Un consejo para quien empieza?"],
          respuestas=["La pienso como parte del personaje: ha sido carruaje, trono y hasta una moto.",
                      "Rampas reales, baños accesibles y escenarios a los que se pueda subir sin cargarnos.",
                      "Empieza con lo que tienes. Y busca comunidad: no estás sola."]),
     "PUBLICADO"),
    (Entrevista, "admin", "historias", P, "comunidad",
     "Entrevista: cosplay de talla grande con orgullo",
     "Rocío Catalán, de Temuco, habla de patronaje para cuerpos diversos y de comunidad.",
     "Rocío comparte patrones adaptados y organiza meetups en La Araucanía.",
     dict(entrevistado="Rocío Catalán",
          preguntas=["¿Qué te motivó a compartir patrones?", "¿Cómo respondes a los comentarios negativos?"],
          respuestas=["Los patrones comerciales nunca me quedaban. Ajustarlos me tomó años y quise ahorrarle ese camino a otras personas.",
                      "Bloqueo y sigo. La comunidad que me apoya es mucho más grande."]),
     "PUBLICADO"),
    (GuiaTutorial, "ignacia", "fotografia", P, "fotografia",
     "Poses básicas para fotos cosplay",
     "Ideas de poses según el tipo de personaje, incluidas poses sentadas y con ayudas técnicas.",
     "Una buena pose cuenta algo del personaje. Estudia sus imágenes oficiales y elige 3 o 4 poses emblemáticas.",
     dict(pasos=["Busca 3 poses emblemáticas del personaje", "Practica frente al espejo",
                 "Prueba poses sentadas: suelen verse más naturales", "Usa los props para guiar la mirada",
                 "Pide a la fotógrafa o fotógrafo que te indique el encuadre"],
          materiales=["Referencias del personaje", "Espejo", "Props"]), "PUBLICADO"),
    # Pendientes: para demostrar la cola de revisión del moderador
    (GuiaTutorial, "camila", "props-armaduras", I, None,
     "Orejas de zorro con alambre y peluche",
     "Cómo hacer orejas livianas que se mantengan firmes durante todo el evento.",
     "Usé alambre de jardín forrado y peluche de una tienda de telas del directorio.",
     dict(pasos=["Dobla el alambre en forma de oreja", "Forra con peluche", "Cose al cintillo"],
          materiales=["Alambre", "Peluche", "Cintillo", "Aguja e hilo"]), "PENDIENTE"),
    (ArticuloTecnico, "joaquin", "confeccion", A, None,
     "Patronaje de chaquetas militares de anime",
     "Adaptar un patrón de chaqueta sastre a los diseños de anime con hombreras y cuellos altos.",
     "Parto de un patrón base de chaqueta sastre y modifico hombros, cuello y largo.",
     dict(enlaces=["https://es.wikipedia.org/wiki/Patronaje"]), "PENDIENTE"),
]


async def seed_contenidos(s: AsyncSession, ctx: dict) -> None:
    img = ctx["imagenes"]
    ahora = datetime.now(timezone.utc)
    ctx["contenidos"] = {}
    for i, (clase, autor, cat, nivel, imagen, titulo, desc, cuerpo, propios, estado) in enumerate(CONTENIDOS):
        c = clase(
            titulo=titulo, descripcion=desc, cuerpo=cuerpo, nivel=nivel, estado=estado,
            categoria=ctx["categorias"][cat], autor=ctx["usuarios"][autor],
            imagen_url=img[imagen][0] if imagen else None, imagen_alt=img[imagen][1] if imagen else None,
            publicado_at=ahora - timedelta(days=2 * i + 1) if estado == "PUBLICADO" else None,
            created_at=ahora - timedelta(days=2 * i + 2),
            **propios,
        )
        c.validar()  # el seed respeta las mismas reglas que la Factory
        s.add(c)
        ctx["contenidos"][titulo] = c
    await s.flush()

    # Notificaciones de ejemplo para la demo (RF-37)
    camila, admin = ctx["usuarios"]["camila"], ctx["usuarios"]["admin"]
    pendiente = ctx["contenidos"]["Orejas de zorro con alambre y peluche"]
    s.add_all([
        Notificacion(usuario_id=camila.id, tipo="NUEVO_TUTORIAL", enlace="/perfil#mis-envios",
                     mensaje=f"Tu tutorial «{pendiente.titulo}» está en revisión."),
        Notificacion(usuario_id=camila.id, tipo="EVENTO_PUBLICADO", enlace="/calendario", leida=True,
                     mensaje="Nuevo evento en el calendario: «Taller de goma EVA para principiantes»."),
        Notificacion(usuario_id=admin.id, tipo="NUEVO_TUTORIAL", enlace="/moderacion?tab=contenidos",
                     mensaje=f"Nuevo tutorial pendiente de revisión: «{pendiente.titulo}»."),
    ])
    await s.flush()
