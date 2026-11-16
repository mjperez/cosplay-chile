"""Catálogo de ilustraciones del seed con su texto alternativo."""
from pathlib import Path

from app.seed.ilustraciones import Figura, escena, guardar

CATALOGO: dict[str, tuple[list[Figura], tuple[str, str], str, str]] = {
    # nombre: (figuras, colores de fondo, decoración, texto alternativo)
    "grupo-diverso": (
        [Figura("oscura", 95, "#111827", "rizado", "#0f766e", "#fde68a", accesorio="corona"),
         Figura("clara", 70, "#b45309", "largo", "#7c3aed", "#fbbf24", ayuda="silla", accesorio="orejas"),
         Figura("trigueña", 62, "#1f2937", "corto", "#be123c", "#e5e7eb", accesorio="espada")],
        ("#6d28d9", "#db2777"), "estrellas",
        "Ilustración de tres cosplayers: una persona de piel oscura y contextura grande con corona, "
        "una persona en silla de ruedas con orejas de zorro y una persona delgada con espada.",
    ),
    "confeccion": (
        [Figura("morena", 100, "#3f2a1d", "moño", "#1d4ed8", "#f472b6"),
         Figura("muy_clara", 66, "#facc15", "corto", "#047857", "#fbbf24")],
        ("#0ea5e9", "#6366f1"), "ciudad",
        "Ilustración de dos personas confeccionando trajes: una de contextura grande con moño y otra rubia de pelo corto.",
    ),
    "maquillaje": (
        [Figura("media", 74, "#7c2d12", "largo", "#9333ea", "#22d3ee", accesorio="orejas"),
         Figura("oscura", 68, "#111827", "rapado", "#f59e0b", "#7c3aed")],
        ("#f472b6", "#a855f7"), "estrellas",
        "Ilustración de dos cosplayers maquillados: una persona con orejas de fantasía y otra de cabeza rapada.",
    ),
    "armadura": (
        [Figura("trigueña", 90, "#1f2937", "corto", "#475569", "#facc15", accesorio="espada"),
         Figura("clara", 78, "#78350f", "largo", "#991b1b", "#e5e7eb", ayuda="baston", accesorio="capa")],
        ("#334155", "#0f766e"), "montanas",
        "Ilustración de dos cosplayers con armaduras de goma EVA; una de ellas usa bastón y capa.",
    ),
    "fotografia": (
        [Figura("morena", 72, "#111827", "rizado", "#0f172a", "#38bdf8", accesorio="camara"),
         Figura("muy_clara", 98, "#9a3412", "largo", "#db2777", "#fde047", accesorio="corona")],
        ("#f97316", "#ef4444"), "montanas",
        "Ilustración de una sesión de fotos: una fotógrafa de pelo rizado con cámara y una cosplayer de contextura grande con corona.",
    ),
    "concurso": (
        [Figura("oscura", 84, "#111827", "moño", "#16a34a", "#fde68a"),
         Figura("clara", 66, "#1f2937", "corto", "#7c3aed", "#fbbf24", ayuda="silla", accesorio="capa"),
         Figura("media", 60, "#4b5563", "largo", "#e11d48", "#fbcfe8", accesorio="orejas")],
        ("#1e3a8a", "#7c3aed"), "estrellas",
        "Ilustración de un escenario de concurso con tres participantes; quien está al centro usa silla de ruedas y capa.",
    ),
    "seguridad": (
        [Figura("trigueña", 76, "#1f2937", "corto", "#0369a1", "#a7f3d0"),
         Figura("clara", 92, "#a16207", "largo", "#15803d", "#fef08a", ayuda="baston")],
        ("#0d9488", "#0284c7"), "ciudad",
        "Ilustración de dos personas caminando juntas hacia un evento; una de ellas usa bastón.",
    ),
    "presupuesto": (
        [Figura("morena", 64, "#111827", "moño", "#ca8a04", "#fef3c7"),
         Figura("media", 104, "#1f2937", "rizado", "#4338ca", "#c4b5fd")],
        ("#16a34a", "#65a30d"), "ciudad",
        "Ilustración de dos personas organizando el presupuesto de su cosplay.",
    ),
    "comunidad": (
        [Figura("muy_clara", 70, "#ea580c", "largo", "#0e7490", "#fda4af"),
         Figura("oscura", 100, "#111827", "rapado", "#9d174d", "#fde68a", accesorio="espada"),
         Figura("trigueña", 68, "#292524", "corto", "#6d28d9", "#a5f3fc", ayuda="silla")],
        ("#c026d3", "#2563eb"), "montanas",
        "Ilustración de una comunidad cosplay reunida al aire libre, con personas de distintos tonos de piel, contexturas y una en silla de ruedas.",
    ),
    "tienda": (
        [Figura("media", 82, "#3f3f46", "moño", "#b91c1c", "#fde68a")],
        ("#f59e0b", "#ea580c"), "ciudad",
        "Ilustración de una vendedora de materiales para cosplay frente a su tienda.",
    ),
    "taller": (
        [Figura("oscura", 72, "#111827", "corto", "#4d7c0f", "#fde047", accesorio="espada")],
        ("#475569", "#64748b"), "ciudad",
        "Ilustración de una persona en su taller de props sosteniendo una espada de goma EVA.",
    ),
    "evento": (
        [Figura("clara", 88, "#7c2d12", "largo", "#2563eb", "#facc15", accesorio="orejas"),
         Figura("morena", 64, "#111827", "rizado", "#be185d", "#fbcfe8", ayuda="silla", accesorio="corona")],
        ("#9333ea", "#f43f5e"), "estrellas",
        "Ilustración de dos asistentes a una convención; una de ellas en silla de ruedas con corona.",
    ),
}


def generar_todas(media_dir: Path) -> dict[str, tuple[str, str]]:
    """Escribe los SVG y devuelve {nombre: (url, alt)}."""
    resultado = {}
    for nombre, (figuras, colores, deco, alt) in CATALOGO.items():
        url = guardar(media_dir, nombre, escena(figuras, colores, alt, deco))
        resultado[nombre] = (url, alt)
    return resultado
