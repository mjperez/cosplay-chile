"""Vocabularios controlados del dominio. Se guardan como texto (VARCHAR + CHECK)."""
import enum
import unicodedata


class StrEnum(str, enum.Enum):
    def __str__(self) -> str:  # pragma: no cover
        return self.value


class Rol(StrEnum):
    USUARIO = "USUARIO"
    ADMIN = "ADMIN"  # actor "Administrador/Moderador"


class EstadoUsuario(StrEnum):
    ACTIVO = "ACTIVO"
    SUSPENDIDO = "SUSPENDIDO"
    ELIMINADO = "ELIMINADO"  # derecho a supresión (RNF-11): cuenta anonimizada


class TipoPerfil(StrEnum):
    """Atributo del perfil, NO un actor (nota Fig. 3)."""
    COSPLAYER = "COSPLAYER"
    AFICIONADO = "AFICIONADO"
    COSMAKER = "COSMAKER"
    SASTRE = "SASTRE"
    MODELADOR = "MODELADOR"
    PINTOR = "PINTOR"
    PELUQUERO = "PELUQUERO"
    MAQUILLADOR = "MAQUILLADOR"
    FOTOGRAFO = "FOTOGRAFO"
    TIENDA = "TIENDA"
    ORGANIZADOR = "ORGANIZADOR"


class Especialidad(StrEnum):
    """Filtro 'tipo de grupo' del directorio (RF-13, RF-14)."""
    COSMAKER = "COSMAKER"
    SASTRERIA = "SASTRERIA"
    MODELADO = "MODELADO"
    PINTURA = "PINTURA"
    PELUQUERIA = "PELUQUERIA"
    MAQUILLAJE = "MAQUILLAJE"
    FOTOGRAFIA = "FOTOGRAFIA"


# Tipo de perfil prestador -> especialidad con que aparece en el directorio (RF-10)
PERFIL_A_ESPECIALIDAD = {
    TipoPerfil.COSMAKER: Especialidad.COSMAKER,
    TipoPerfil.SASTRE: Especialidad.SASTRERIA,
    TipoPerfil.MODELADOR: Especialidad.MODELADO,
    TipoPerfil.PINTOR: Especialidad.PINTURA,
    TipoPerfil.PELUQUERO: Especialidad.PELUQUERIA,
    TipoPerfil.MAQUILLADOR: Especialidad.MAQUILLAJE,
    TipoPerfil.FOTOGRAFO: Especialidad.FOTOGRAFIA,
}


class TipoProducto(StrEnum):
    """Materia prima de las tiendas (RF-34)."""
    TELAS = "TELAS"
    TERMOPLASTICOS = "TERMOPLASTICOS"
    ACCESORIOS = "ACCESORIOS"
    PINTURAS = "PINTURAS"
    LENTES_CONTACTO = "LENTES_CONTACTO"
    PELUCAS = "PELUCAS"


class AlcanceTienda(StrEnum):
    NACIONAL = "NACIONAL"
    INTERNACIONAL = "INTERNACIONAL"


class TipoDirectorio(StrEnum):
    PROVEEDOR = "PROVEEDOR"
    TIENDA = "TIENDA"
    COMUNIDAD = "COMUNIDAD"


class TipoContenido(StrEnum):
    GUIA = "GUIA"
    ENTREVISTA = "ENTREVISTA"
    ARTICULO = "ARTICULO"


class Nivel(StrEnum):
    PRINCIPIANTE = "PRINCIPIANTE"
    INTERMEDIO = "INTERMEDIO"
    AVANZADO = "AVANZADO"


class EstadoPublicacion(StrEnum):
    PENDIENTE = "PENDIENTE"
    PUBLICADO = "PUBLICADO"
    RECHAZADO = "RECHAZADO"
    OCULTO = "OCULTO"  # retirado por moderación tras un reporte


class TipoEvento(StrEnum):
    CONVENCION = "CONVENCION"
    CONCURSO = "CONCURSO"
    MEETUP = "MEETUP"
    TALLER = "TALLER"


class TipoObjetoReporte(StrEnum):
    CONTENIDO = "CONTENIDO"
    TEMA = "TEMA"
    RESPUESTA = "RESPUESTA"
    EVENTO = "EVENTO"
    DIRECTORIO = "DIRECTORIO"
    RESENA = "RESENA"
    PARTICIPACION_DESAFIO = "PARTICIPACION_DESAFIO"


class MotivoReporte(StrEnum):
    SPAM = "SPAM"
    ACOSO = "ACOSO"
    INAPROPIADO = "INAPROPIADO"
    INFORMACION_INCORRECTA = "INFORMACION_INCORRECTA"
    ACTUALIZACION_EVENTO = "ACTUALIZACION_EVENTO"  # RF-17
    OTRO = "OTRO"


class EstadoReporte(StrEnum):
    ABIERTO = "ABIERTO"
    RESUELTO = "RESUELTO"
    DESCARTADO = "DESCARTADO"


class TipoContacto(StrEnum):
    DUDA = "DUDA"
    SUGERENCIA = "SUGERENCIA"
    DENUNCIA = "DENUNCIA"
    CUENTA = "CUENTA"  # p. ej. cuenta suspendida (UC-01, excepción 2)


class EstadoContacto(StrEnum):
    NUEVO = "NUEVO"
    ATENDIDO = "ATENDIDO"


class Region(StrEnum):
    """Las 16 regiones de Chile, de norte a sur."""
    AP = "AP"
    TA = "TA"
    AN = "AN"
    AT = "AT"
    CO = "CO"
    VA = "VA"
    RM = "RM"
    LI = "LI"
    ML = "ML"
    NB = "NB"
    BI = "BI"
    AR = "AR"
    LR = "LR"
    LL = "LL"
    AI = "AI"
    MA = "MA"


REGIONES = {
    Region.AP: "Arica y Parinacota",
    Region.TA: "Tarapacá",
    Region.AN: "Antofagasta",
    Region.AT: "Atacama",
    Region.CO: "Coquimbo",
    Region.VA: "Valparaíso",
    Region.RM: "Metropolitana de Santiago",
    Region.LI: "Libertador General Bernardo O'Higgins",
    Region.ML: "Maule",
    Region.NB: "Ñuble",
    Region.BI: "Biobío",
    Region.AR: "La Araucanía",
    Region.LR: "Los Ríos",
    Region.LL: "Los Lagos",
    Region.AI: "Aysén del General Carlos Ibáñez del Campo",
    Region.MA: "Magallanes y de la Antártica Chilena",
}

# Ciudades capitales usadas para que la búsqueda por ciudad encuentre la región
# (ej. "Concepción" -> Biobío, "Santiago" -> RM).
CIUDADES_REGION = {
    "arica": Region.AP, "iquique": Region.TA, "antofagasta": Region.AN, "calama": Region.AN,
    "copiapo": Region.AT, "la serena": Region.CO, "coquimbo": Region.CO,
    "valparaiso": Region.VA, "vina del mar": Region.VA, "santiago": Region.RM,
    "rancagua": Region.LI, "talca": Region.ML, "chillan": Region.NB, "concepcion": Region.BI,
    "temuco": Region.AR, "valdivia": Region.LR, "puerto montt": Region.LL, "osorno": Region.LL,
    "coyhaique": Region.AI, "punta arenas": Region.MA,
}


# Coordenadas de la capital regional: posición por defecto en el mapa si una ficha no indica la suya
REGION_CENTRO = {
    Region.AP: (-18.4783, -70.3126), Region.TA: (-20.2307, -70.1357), Region.AN: (-23.6509, -70.3975),
    Region.AT: (-27.3668, -70.3323), Region.CO: (-29.9045, -71.2489), Region.VA: (-33.0472, -71.6127),
    Region.RM: (-33.4489, -70.6693), Region.LI: (-34.1708, -70.7444), Region.ML: (-35.4264, -71.6554),
    Region.NB: (-36.6066, -72.1034), Region.BI: (-36.8201, -73.0444), Region.AR: (-38.7359, -72.5904),
    Region.LR: (-39.8142, -73.2459), Region.LL: (-41.4689, -72.9411), Region.AI: (-45.5712, -72.0685),
    Region.MA: (-53.1638, -70.9171),
}


def normalizar(texto: str) -> str:
    """minúsculas y sin tildes (para comparar 'Concepción' con 'concepcion')."""
    sin_tildes = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return sin_tildes.lower().strip()


def regiones_que_coinciden(q: str) -> list[Region]:
    nq = normalizar(q)
    if len(nq) < 3:
        return []
    encontradas = {r for r, nombre in REGIONES.items() if nq in normalizar(nombre)}
    encontradas |= {r for ciudad, r in CIUDADES_REGION.items() if nq in ciudad or ciudad in nq}
    return sorted(encontradas, key=lambda r: list(Region).index(r))
