"""Datos de demostración para exponer la plataforma en clases.

Este módulo crea cuentas con contraseñas conocidas y contenido de ejemplo.
**No se ejecuta en producción**: el cargador se niega a correr si
`ENVIRONMENT=production`, salvo que se fuerce con `DEMO_SEED=1`. En Render se
usa `app.seed.datos_base`, que solo carga datos reales y no crea cuentas.

    python -m app.seed.demo

Cuentas que crea (todas con contraseña `Demo2026!`). El nombre visible dice
el rol a propósito: al exponer la plataforma en clases, quien mira la pantalla
debe saber de inmediato con qué permisos está entrando, sin tener que recordar
un nombre de persona inventado.

    demo@cosplay.cl         Usuario Administrador
    cosplayer@cosplay.cl    Usuario Cosplayer
    organizador@cosplay.cl  Usuario Organizador

Es idempotente: se puede ejecutar varias veces sin duplicar filas. Si las
cuentas ya existen, sincroniza su nombre visible con esta lista, de modo que
un cambio de etiqueta se refleje también en bases creadas con versiones
anteriores.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_session_manager
from app.core.privacidad import VERSION
from app.core.security import hash_password
from app.factories.contenido_factory import ContenidoFactory
from app.models.usuario import Usuario
from app.repositories import comunidad as repo_comunidad
from app.repositories import contenido as repo_contenido
from app.repositories import directorio as repo_directorio
from app.repositories import evento as repo_evento
from app.repositories import perfil as repo_perfil
from app.repositories import usuario as repo_usuarios
from app.schemas.contenido import ArticuloEntrada, EntrevistaEntrada, GuiaEntrada
from app.seed import datos_base

PASSWORD_DEMO = "Demo2026!"

USUARIOS_DEMO = [
    {"nombre": "Usuario Administrador", "correo": "demo@cosplay.cl", "rol": "administrador", "region": "Metropolitana"},
    {"nombre": "Usuario Cosplayer", "correo": "cosplayer@cosplay.cl", "rol": "cosplayer", "region": "Valparaíso"},
    {"nombre": "Usuario Organizador", "correo": "organizador@cosplay.cl", "rol": "organizador", "region": "Biobío"},
]

EVENTOS = [
    ("Convención Cosplay Santiago 2026", "convencion", 21, 2, "Estación Mapocho", "Metropolitana", "https://ejemplo.cl/ccs2026"),
    ("Concurso Nacional de Cosplay", "concurso", 35, 1, "Teatro Caupolicán", "Metropolitana", None),
    ("Feria de Insumos y Pelucas", "feria", 12, 1, "Centro de Eventos Sur", "Biobío", None),
    ("Taller de goma eva: armaduras", "taller", 7, 1, "Casa de la Cultura", "Valparaíso", None),
    ("Encuentro Cosplay Norte", "convencion", 48, 2, "Parque Croacia", "Antofagasta", None),
    ("Meetup de fotografía cosplay", "otro", 5, 1, "Parque Forestal", "Metropolitana", None),
]

TEMAS = [
    {
        "titulo": "¿Qué sellador recomiendan para la goma eva?",
        "categoria": "Armaduras y props",
        "contenido": "Estoy terminando una armadura y la pintura se me levanta en los bordes. ¿Usan imprimación acrílica o cola fría diluida?",
        "respuestas": [
            "Imprimación acrílica en dos capas delgadas, lijando entre medio. La cola fría sola no sella el poro.",
            "Yo agrego una capa de barniz mate al final; en Santiago la humedad levanta la pintura si no sellas bien.",
        ],
    },
    {
        "titulo": "Presupuesto real para un traje completo",
        "categoria": "Presupuesto y compras",
        "contenido": "Compartamos cuánto costó el último traje, incluyendo peluca y maquillaje, para tener una referencia honesta.",
        "respuestas": [
            "El mío salió cerca de $95.000 CLP contando goma eva, pinturas y peluca. Sin contar herramientas.",
        ],
    },
    {
        "titulo": "Cómo fijar una peluca sin dañar el cuero cabelludo",
        "categoria": "Pelucas y maquillaje",
        "contenido": "Busco una técnica que aguante ocho horas de convención sin irritar la piel. ¿Gorra de lycra o cinta?",
        "respuestas": [
            "Gorra de lycra + horquillas cruzadas, y cinta de doble faz solo en la frente. Prueba antes con un parche.",
        ],
    },
    {
        "titulo": "Patrones base para vestuario de personaje",
        "categoria": "Costura y vestuario",
        "contenido": "¿Parten de patrones comerciales o sacan el molde directamente de la referencia? Me cuesta escalar las piezas.",
        "respuestas": [],
    },
    {
        "titulo": "Coordinación para la próxima convención",
        "categoria": "Eventos y comunidad",
        "contenido": "Armemos el punto de encuentro y la lista de quienes van con traje grande para organizar el traslado.",
        "respuestas": [
            "Cuenten conmigo, llevo la armadura en dos maletas. Puedo ayudar con el traslado.",
        ],
    },
]

TIENDAS = [
    ("Telas La Cúpula", "telas", True, "https://ejemplo.cl/telas", "Metropolitana"),
    ("Insumos Cosplay CL", "insumos", True, "https://ejemplo.cl/insumos", "Metropolitana"),
    ("Pelucas Ñuñoa", "pelucas", True, "https://ejemplo.cl/pelucas", "Metropolitana"),
    ("Impresión 3D Sur", "impresion_3d", True, "https://ejemplo.cl/3d", "Biobío"),
    ("Goma Eva Express", "insumos", True, None, "Valparaíso"),
    ("Tienda Online Internacional", "otro", True, "https://ejemplo.cl/import", None),
]

GRUPOS = [
    ("Cosplay Chile Comunidad", None, "facebook", "https://ejemplo.cl/grupo"),
    ("Cosplayers Región Metropolitana", "Metropolitana", "discord", "https://ejemplo.cl/discord"),
    ("Cosplay Valpo", "Valparaíso", "instagram", "https://ejemplo.cl/valpo"),
    ("Cosmaker del Biobío", "Biobío", "whatsapp", None),
    ("Foro de Armaduras", None, "foro", None),
]


def _produccion_sin_autorizacion() -> bool:
    entorno = os.environ.get("ENVIRONMENT", "local").lower()
    return entorno in {"production", "produccion"} and os.environ.get("DEMO_SEED") != "1"


def _ahora() -> datetime:
    """UTC naive, igual que las fechas que guarda el esquema de eventos."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _usuarios(sesion: Session) -> dict[str, Usuario]:
    settings = get_settings()
    creados: dict[str, Usuario] = {}
    for dato in USUARIOS_DEMO:
        existente = repo_usuarios.obtener_por_correo(sesion, dato["correo"])
        if existente is None:
            existente = repo_usuarios.crear(
                sesion,
                nombre=dato["nombre"],
                correo=dato["correo"],
                password_hash=hash_password(PASSWORD_DEMO, settings),
                rol=dato["rol"],
                region=dato["region"],
                consentimiento_fecha=datetime.now(timezone.utc),
                consentimiento_version=VERSION,
            )
        elif existente.nombre != dato["nombre"]:
            # La cuenta puede venir de una versión anterior de la semilla, con
            # un nombre de persona. Sin esto, recargar no cambiaría la etiqueta
            # que se ve en el encabezado y en el panel de administración.
            repo_usuarios.actualizar_nombre(sesion, existente, nombre=dato["nombre"])
        creados[dato["correo"]] = existente
    return creados


def _eventos(sesion: Session, usuarios: dict[str, Usuario]) -> dict[str, str]:
    ahora = _ahora()
    ids: dict[str, str] = {}
    for nombre, tipo, dias, duracion, lugar, region, enlace in EVENTOS:
        existente = repo_evento.por_nombre(sesion, nombre)
        if existente is None:
            existente = repo_evento.crear(
                sesion,
                nombre=nombre,
                tipo=tipo,
                fecha_inicio=ahora + timedelta(days=dias),
                fecha_fin=ahora + timedelta(days=dias + duracion),
                lugar=lugar,
                region=region,
                enlace_oficial=enlace,
            )
        ids[nombre] = str(existente.id_evento)

    # Dos inscripciones de ejemplo para que el detalle y «mis eventos» tengan
    # algo que mostrar en la demo.
    from uuid import UUID

    ejemplos = [
        (usuarios["cosplayer@cosplay.cl"], EVENTOS[0][0], "Sailor Moon"),
        (usuarios["organizador@cosplay.cl"], EVENTOS[0][0], "Staff / organización"),
        (usuarios["organizador@cosplay.cl"], EVENTOS[3][0], "Tallerista"),
    ]
    for usuario, nombre_evento, personaje in ejemplos:
        id_evento = UUID(ids[nombre_evento])
        if repo_evento.participacion(sesion, usuario.id_usuario, id_evento) is None:
            repo_evento.crear_participacion(
                sesion,
                id_usuario=usuario.id_usuario,
                id_evento=id_evento,
                personaje=personaje,
            )
    return ids


def _foro(sesion: Session, usuarios: dict[str, Usuario]) -> None:
    autores = [
        usuarios["cosplayer@cosplay.cl"],
        usuarios["organizador@cosplay.cl"],
        usuarios["demo@cosplay.cl"],
    ]
    for indice, dato in enumerate(TEMAS):
        tema = repo_comunidad.tema_por_titulo(sesion, dato["titulo"])
        if tema is None:
            tema = repo_comunidad.crear_tema(
                sesion,
                id_creador=autores[indice % len(autores)].id_usuario,
                titulo=dato["titulo"],
                categoria=dato["categoria"],
                contenido=dato["contenido"],
            )
        existentes = {
            respuesta.contenido
            for respuesta, _ in repo_comunidad.listar_respuestas(sesion, tema.id_tema)
        }
        for numero, texto in enumerate(dato["respuestas"]):
            if texto in existentes:
                continue
            repo_comunidad.crear_respuesta(
                sesion,
                id_tema=tema.id_tema,
                id_usuario=autores[(indice + numero + 1) % len(autores)].id_usuario,
                contenido=texto,
            )


def _desafios(sesion: Session, usuarios: dict[str, Usuario]) -> None:
    actual = datetime.now(timezone.utc)
    anterior = (actual.replace(day=1) - timedelta(days=1)).strftime("%Y-%m")
    mes_actual = actual.strftime("%Y-%m")

    definiciones = [
        (mes_actual, "Desafío del mes: personaje de anime clásico", None),
        (anterior, "Desafío del mes pasado: armadura de goma eva", usuarios["cosplayer@cosplay.cl"]),
    ]
    for mes, titulo, ganador in definiciones:
        fila = repo_comunidad.desafio_por_mes(sesion, mes)
        desafio = fila[0] if fila else repo_comunidad.crear_desafio(sesion, titulo=titulo, mes=mes)
        if ganador is not None and desafio.id_ganador is None:
            repo_comunidad.asignar_ganador(sesion, desafio, ganador.id_usuario)


def _directorio(sesion: Session) -> None:
    for nombre, tipo, envia, enlace, region in TIENDAS:
        if repo_directorio.tienda_por_nombre(sesion, nombre) is None:
            repo_directorio.crear_tienda(
                sesion,
                nombre=nombre,
                tipo=tipo,
                envia_a_chile=envia,
                enlace_web=enlace,
                region=region,
            )
    for nombre, region, plataforma, enlace in GRUPOS:
        if repo_directorio.grupo_por_nombre(sesion, nombre) is None:
            repo_directorio.crear_grupo(
                sesion, nombre=nombre, region=region, plataforma=plataforma, enlace=enlace
            )


def _perfil(sesion: Session, usuarios: dict[str, Usuario]) -> None:
    cosplayer = usuarios["cosplayer@cosplay.cl"]
    if repo_perfil.perfil_de(sesion, cosplayer.id_usuario) is None:
        repo_perfil.guardar(
            sesion,
            id_usuario=cosplayer.id_usuario,
            especialidad="Armaduras y props con goma eva",
            portafolio_url="https://ejemplo.cl/portafolio",
            biografia="Cosplayer desde 2019. Me especializo en armaduras ligeras y en documentar el proceso para quien recién parte.",
            region="Valparaíso",
        )


def _contenido(sesion: Session, usuarios: dict[str, Usuario]) -> None:
    autor = usuarios["cosplayer@cosplay.cl"]
    categoria = repo_contenido.categoria_por_nombre(sesion, "Armaduras y props")
    id_categoria = categoria.id_categoria if categoria else None
    ahora = datetime.now(timezone.utc).replace(tzinfo=None)

    entradas = [
        GuiaEntrada(
            tipo="guia",
            titulo="Armadura de goma eva: del trazo a la pintura",
            resumen="Una guía práctica con medidas, materiales y advertencias de seguridad.",
            nivel="intermedio",
            id_categoria=id_categoria,
            cuerpo="<p>Primero se toma la medida del torso y se traslada al patrón.</p>",
            personaje="Knight Artorias",
            medidas=[{"parte": "pecho", "valor": "98 cm"}],
            tecnicas=["termoformado", "sellado de bordes"],
            presupuesto="$45.000 a $60.000 CLP",
            seguridad="Ventilar el espacio al usar pegamento de contacto.",
            pasos=["Trazo", "Corte", "Termoformado", "Sellado", "Pintura"],
            materiales=["Goma eva 10 mm", "Pistola de calor", "Imprimación acrílica"],
        ),
        EntrevistaEntrada(
            tipo="entrevista",
            titulo="Conversando con la comunidad: cómo empezar en el cosplay",
            resumen="Tres cosplayers cuentan qué habría cambiado de su primer traje.",
            nivel="basico",
            id_categoria=id_categoria,
            cuerpo="<p>Una conversación sobre presupuesto, tiempo y paciencia.</p>",
            preguntas=["¿Qué fue lo más difícil de tu primer traje?", "¿Qué le dirías a quien parte hoy?"],
            respuestas=["Aprender a fallar sin abandonar el proyecto.", "Empieza por una pieza pequeña y termínala."],
        ),
        ArticuloEntrada(
            tipo="articulo",
            titulo="Calendario de convenciones: cómo planificar tu año",
            resumen="Ordena fechas, presupuesto y transporte antes de inscribirte.",
            nivel="basico",
            id_categoria=id_categoria,
            cuerpo="<p>Planificar con meses de anticipación evita gastos de último minuto.</p>",
        ),
    ]

    for datos in entradas:
        if repo_contenido.por_titulo(sesion, datos.titulo) is not None:
            continue
        contenido = ContenidoFactory.crear(datos, autor.id_usuario)
        contenido.estado = "publicado"
        contenido.fecha_publicacion = ahora
        sesion.add(contenido)
    sesion.flush()


def cargar(sesion: Session) -> dict[str, object]:
    """Carga todo el conjunto de demostración. Idempotente."""
    datos_base.cargar(sesion)
    usuarios = _usuarios(sesion)
    ids_eventos = _eventos(sesion, usuarios)
    _foro(sesion, usuarios)
    _desafios(sesion, usuarios)
    _directorio(sesion)
    _perfil(sesion, usuarios)
    _contenido(sesion, usuarios)
    sesion.flush()
    return {
        "usuarios": len(usuarios),
        "eventos": len(ids_eventos),
        "temas": len(TEMAS),
        "tiendas": len(TIENDAS),
        "grupos": len(GRUPOS),
    }


def main() -> None:
    if _produccion_sin_autorizacion():
        raise SystemExit(
            "demo: rechazado en producción. Usa DEMO_SEED=1 si sabes lo que haces, "
            "o ejecuta `python -m app.seed.datos_base` para cargar solo datos reales."
        )
    with get_session_manager().session() as sesion:
        resultado = cargar(sesion)
    print("Datos de demostración listos:")
    for clave, valor in resultado.items():
        print(f"  {clave}: {valor}")
    print(f"  contraseña de las cuentas demo: {PASSWORD_DEMO}")


if __name__ == "__main__":
    main()
