"""Ilustraciones SVG propias para el seed (RNF-10: diversidad de cuerpos, géneros y capacidades).

No se usan fotos de personas reales (derechos de imagen). Cada figura combina
tono de piel, contextura, peinado y ayudas técnicas (silla de ruedas, bastón).
"""
from dataclasses import dataclass
from pathlib import Path

PIELES = {
    "oscura": "#5a3825", "morena": "#8d5524", "trigueña": "#c68642",
    "media": "#e0ac69", "clara": "#f1c27d", "muy_clara": "#ffdbac",
}


@dataclass
class Figura:
    piel: str = "media"
    ancho: int = 70            # contextura: 60 delgada, 80 media, 105 grande
    pelo: str = "#2b1d14"
    peinado: str = "corto"     # corto | largo | moño | rapado | rizado
    traje: str = "#7c3aed"
    detalle: str = "#fbbf24"
    ayuda: str | None = None   # silla | baston
    accesorio: str | None = None  # capa | orejas | espada | corona | camara


def _figura(f: Figura, x: int, suelo: int = 430) -> str:
    piel = PIELES.get(f.piel, f.piel)
    sentado = f.ayuda == "silla"
    alto_cuerpo = 105 if sentado else 150
    base = suelo - (60 if sentado else 0)
    tope_cuerpo = base - alto_cuerpo - (0 if sentado else 70)
    cabeza_y = tope_cuerpo - 42
    partes: list[str] = []

    if f.accesorio == "capa":
        partes.append(
            f'<path d="M{x - f.ancho / 2 - 8},{tope_cuerpo + 10} L{x - f.ancho / 2 - 35},{base} '
            f'L{x + f.ancho / 2 + 35},{base} L{x + f.ancho / 2 + 8},{tope_cuerpo + 10} Z" fill="{f.detalle}" opacity=".85"/>'
        )
    if f.peinado == "largo":
        partes.append(f'<rect x="{x - 42}" y="{cabeza_y - 10}" width="84" height="95" rx="40" fill="{f.pelo}"/>')
    # cuerpo
    partes.append(
        f'<rect x="{x - f.ancho / 2}" y="{tope_cuerpo}" width="{f.ancho}" height="{alto_cuerpo}" '
        f'rx="{min(30, f.ancho / 3)}" fill="{f.traje}"/>'
    )
    partes.append(
        f'<rect x="{x - f.ancho / 2}" y="{tope_cuerpo + 40}" width="{f.ancho}" height="12" fill="{f.detalle}"/>'
    )
    # brazos
    partes.append(
        f'<rect x="{x - f.ancho / 2 - 16}" y="{tope_cuerpo + 8}" width="18" height="{alto_cuerpo - 20}" rx="9" fill="{piel}"/>'
        f'<rect x="{x + f.ancho / 2 - 2}" y="{tope_cuerpo + 8}" width="18" height="{alto_cuerpo - 20}" rx="9" fill="{piel}"/>'
    )
    if sentado:
        # silla de ruedas
        partes.append(
            f'<rect x="{x - f.ancho / 2 - 10}" y="{base - 12}" width="{f.ancho + 50}" height="14" rx="7" fill="#334155"/>'
            f'<rect x="{x + f.ancho / 2 + 22}" y="{base - 95}" width="12" height="95" rx="6" fill="#334155"/>'
            f'<circle cx="{x + 5}" cy="{suelo - 28}" r="34" fill="none" stroke="#1e293b" stroke-width="9"/>'
            f'<circle cx="{x + 5}" cy="{suelo - 28}" r="5" fill="#1e293b"/>'
            f'<circle cx="{x - f.ancho / 2 - 4}" cy="{suelo - 8}" r="9" fill="#1e293b"/>'
            f'<rect x="{x - f.ancho / 2 + 4}" y="{base}" width="{f.ancho - 8}" height="22" rx="8" fill="{f.traje}"/>'
        )
    else:
        partes.append(
            f'<rect x="{x - f.ancho / 2 + 6}" y="{base - 72}" width="{f.ancho / 2 - 10}" height="72" rx="8" fill="#1f2937"/>'
            f'<rect x="{x + 4}" y="{base - 72}" width="{f.ancho / 2 - 10}" height="72" rx="8" fill="#1f2937"/>'
        )
    if f.ayuda == "baston":
        partes.append(
            f'<rect x="{x + f.ancho / 2 + 20}" y="{tope_cuerpo + 60}" width="7" height="{base - tope_cuerpo - 60}" fill="#e5e7eb"/>'
            f'<rect x="{x + f.ancho / 2 + 20}" y="{base - 20}" width="7" height="20" fill="#dc2626"/>'
        )
    # cabeza y pelo
    partes.append(f'<rect x="{x - 9}" y="{cabeza_y + 30}" width="18" height="18" fill="{piel}"/>')
    partes.append(f'<circle cx="{x}" cy="{cabeza_y}" r="38" fill="{piel}"/>')
    if f.peinado in ("corto", "largo"):
        partes.append(f'<path d="M{x - 39},{cabeza_y - 2} A39,39 0 0 1 {x + 39},{cabeza_y - 2} Z" fill="{f.pelo}"/>')
    elif f.peinado == "moño":
        partes.append(
            f'<path d="M{x - 39},{cabeza_y - 4} A39,39 0 0 1 {x + 39},{cabeza_y - 4} Z" fill="{f.pelo}"/>'
            f'<circle cx="{x}" cy="{cabeza_y - 44}" r="17" fill="{f.pelo}"/>'
        )
    elif f.peinado == "rizado":
        for dx in (-30, -15, 0, 15, 30):
            partes.append(f'<circle cx="{x + dx}" cy="{cabeza_y - 28 + abs(dx) / 3}" r="16" fill="{f.pelo}"/>')
    # rostro
    partes.append(
        f'<circle cx="{x - 13}" cy="{cabeza_y + 4}" r="4" fill="#111827"/>'
        f'<circle cx="{x + 13}" cy="{cabeza_y + 4}" r="4" fill="#111827"/>'
        f'<path d="M{x - 12},{cabeza_y + 17} Q{x},{cabeza_y + 27} {x + 12},{cabeza_y + 17}" '
        f'stroke="#111827" stroke-width="3" fill="none" stroke-linecap="round"/>'
    )
    if f.accesorio == "orejas":
        partes.append(
            f'<path d="M{x - 34},{cabeza_y - 20} L{x - 40},{cabeza_y - 66} L{x - 10},{cabeza_y - 36} Z" fill="{f.detalle}"/>'
            f'<path d="M{x + 34},{cabeza_y - 20} L{x + 40},{cabeza_y - 66} L{x + 10},{cabeza_y - 36} Z" fill="{f.detalle}"/>'
        )
    elif f.accesorio == "corona":
        partes.append(
            f'<path d="M{x - 26},{cabeza_y - 34} L{x - 26},{cabeza_y - 58} L{x - 12},{cabeza_y - 44} L{x},{cabeza_y - 64} '
            f'L{x + 12},{cabeza_y - 44} L{x + 26},{cabeza_y - 58} L{x + 26},{cabeza_y - 34} Z" fill="{f.detalle}"/>'
        )
    elif f.accesorio == "espada":
        partes.append(
            f'<rect x="{x - f.ancho / 2 - 22}" y="{tope_cuerpo - 70}" width="10" height="120" rx="3" fill="#cbd5e1"/>'
            f'<rect x="{x - f.ancho / 2 - 34}" y="{tope_cuerpo + 46}" width="34" height="9" rx="3" fill="{f.detalle}"/>'
        )
    elif f.accesorio == "camara":
        partes.append(
            f'<rect x="{x - 26}" y="{tope_cuerpo + 12}" width="52" height="34" rx="6" fill="#111827"/>'
            f'<circle cx="{x}" cy="{tope_cuerpo + 29}" r="11" fill="#475569"/>'
        )
    return "".join(partes)


def escena(figuras: list[Figura], fondo: tuple[str, str], titulo: str, decoracion: str = "estrellas") -> str:
    ancho, alto = 800, 500
    n = len(figuras)
    xs = [int(ancho * (i + 1) / (n + 1)) for i in range(n)]
    deco = ""
    if decoracion == "estrellas":
        for i, (cx, cy) in enumerate([(80, 70), (700, 90), (620, 40), (150, 140), (400, 50), (520, 150)]):
            deco += f'<circle cx="{cx}" cy="{cy}" r="{4 + i % 3 * 2}" fill="#ffffff" opacity=".7"/>'
    elif decoracion == "montanas":
        deco = ('<path d="M0,330 L160,170 L300,300 L450,140 L620,310 L800,190 L800,500 L0,500 Z" '
                'fill="#ffffff" opacity=".18"/>')
    elif decoracion == "ciudad":
        for i, h in enumerate([120, 180, 90, 210, 140, 170, 100]):
            deco += f'<rect x="{i * 115 + 10}" y="{430 - h}" width="90" height="{h}" fill="#ffffff" opacity=".15"/>'
    cuerpo = "".join(_figura(f, x) for f, x in zip(figuras, xs))
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {ancho} {alto}" role="img">'
        f"<title>{titulo}</title>"
        f'<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">'
        f'<stop offset="0" stop-color="{fondo[0]}"/><stop offset="1" stop-color="{fondo[1]}"/></linearGradient></defs>'
        f'<rect width="{ancho}" height="{alto}" fill="url(#g) {fondo[0]}"/>{deco}'
        f'<rect y="430" width="{ancho}" height="70" fill="#000000" opacity=".18"/>{cuerpo}</svg>'
    )


def guardar(directorio: Path, nombre: str, svg: str) -> str:
    destino = directorio / "seed" / f"{nombre}.svg"
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(svg, encoding="utf-8")
    return f"/media/seed/{nombre}.svg"
