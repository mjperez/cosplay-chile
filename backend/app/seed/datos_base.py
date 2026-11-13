"""Datos base que deben existir en cualquier despliegue.

Son datos reales del levantamiento de requerimientos (categorías y fichas del
directorio), no datos de demostración. Los dos cargadores son idempotentes, así
que se puede ejecutar en cada arranque sin duplicar ni sobreescribir cambios
hechos a mano.

    python -m app.seed.datos_base
"""

from __future__ import annotations

from app.core.database import get_session_manager
from app.seed import categorias, proveedores


def cargar(sesion) -> dict[str, tuple[int, int]]:
    return {
        "categorias": categorias.cargar(sesion),
        "proveedores": proveedores.cargar(sesion),
    }


def main() -> None:
    with get_session_manager().session() as sesion:
        resultado = cargar(sesion)
    for nombre, (creados, existentes) in resultado.items():
        print(f"{nombre}: creados={creados}, ya existian={existentes}")


if __name__ == "__main__":
    main()
