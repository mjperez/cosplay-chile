"""Carga de las fichas semilla del directorio (T-13.5).

Origen de los datos
-------------------
Las 20 fichas salen del levantamiento de requerimientos del Sprint 1, no de
una lista inventada:

- 18 cuentas chilenas identificadas en los datasets de TikTok recogidos con
  Apify (`apify/dataset_tiktok-scraper_*.json`), cuyo perfil público declara
  una actividad de proveedor: tienda, cosmaker, sastre u organizadora de
  eventos.
- Dos tiendas nombradas por los propios usuarios en los comentarios de
  Instagram (Yui Chan Store y Arte Pierrot) no se incluyen: la mención no trae
  región ni tipo, y no hay perfil que lo confirme.

Regla de privacidad
-------------------
La región se publica solo cuando el negocio la expone como parte de su
actividad comercial (dirección de local, alcance declarado, ciudad en el
perfil). **Las personas naturales quedan sin región a propósito**, aunque su
perfil permita deducirla: publicar la ubicación de un cosmaker o un sastre
individual es un riesgo de doxxing y no aporta a la función del directorio,
que es encontrar un servicio, no ubicar a una persona.

Por eso las cinco fichas de cosmaker y la de sastrería no tienen región. No es
un dato que falte: es un dato que no corresponde publicar.

Qué se guarda y qué no
----------------------
Solo lo que la cuenta publica abiertamente: nombre comercial, tipo de
actividad, región cuando corresponde según la regla anterior, el usuario
público y el sitio web de negocio. **No se guardan correos, teléfonos ni
nombres de personas**: aparecen en varias biografías y no hacen falta para el
directorio.

Ejecución
---------
    python -m app.seed.proveedores

Es idempotente y correctiva: crea las fichas que faltan y actualiza las que
cambiaron, sin duplicar.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.directorio import Proveedor

# Claves que puede tocar la carga. Las ausentes se normalizan a None para que
# una corrección pueda borrar un valor anterior.
CAMPOS = ("nombre", "tipo", "region", "contacto", "sitio_web", "descripcion")

REGISTROS: list[dict] = [
    # --- Tiendas --------------------------------------------------------
    {
        "nombre": "Tienda Akiba-Kei",
        "tipo": "tienda",
        "region": "Antofagasta",
        "contacto": "@tienda.akibakei",
        "descripcion": "Tienda de artículos de anime con locales en Antofagasta y Calama, y envíos a todo Chile desde 2013.",
    },
    {
        "nombre": "Epic Animes",
        "tipo": "tienda",
        "region": "Metropolitana",
        "contacto": "@_epic_animes",
        "descripcion": "Tienda de anime en el Minimall Paseo Concha y Toro, Puente Alto.",
    },
    {
        "nombre": "Hey Nana",
        "tipo": "tienda",
        "region": "Metropolitana",
        "contacto": "@heynanacl",
        "descripcion": "Tienda en Boulevard Alameda 333, locales 15 y 16, Santiago.",
    },
    {
        "nombre": "Komori Store",
        "tipo": "tienda",
        "region": "Metropolitana",
        "contacto": "@komoristore",
        "descripcion": "Tienda de artículos de anime en Santiago.",
    },
    {
        "nombre": "MotorLaser",
        "tipo": "tienda",
        "region": None,
        "contacto": "@motorlaser_",
        "descripcion": "Corte láser de artículos de anime y cultura geek. Solo venta online.",
    },
    {
        "nombre": "Tienda Deck",
        "tipo": "tienda",
        "region": None,
        "contacto": "@tiendadeck",
        "sitio_web": "https://tiendadeck.cl",
        "descripcion": "Papelería, accesorios y artículos de colección. Solo venta online.",
    },
    {
        "nombre": "FukuBox",
        "tipo": "tienda",
        "region": None,
        "contacto": "@fukubox.cl",
        "descripcion": "Servicio de compra por encargo (proxy) de productos japoneses. Opera desde Japón.",
    },
    # --- Cosmaker -------------------------------------------------------
    # Sin región: personas naturales. Ver la regla de privacidad del encabezado.
    {
        "nombre": "Shar Cosss",
        "tipo": "cosmaker",
        "region": None,
        "contacto": "@shar_cosss",
        "descripcion": "Talleres de pelucas y trabajo de cosmaker.",
    },
    {
        "nombre": "PrincessHaru",
        "tipo": "cosmaker",
        "region": None,
        "contacto": "@princessharuwu",
        "descripcion": "Cosmaker y fabricación de props.",
    },
    {
        "nombre": "Lovesick Cos",
        "tipo": "cosmaker",
        "region": None,
        "contacto": "@lovesick_cos",
        "descripcion": "Cosmaker con trabajo centrado en personajes de Vocaloid.",
    },
    {
        "nombre": "Sora Sonne",
        "tipo": "cosmaker",
        "region": None,
        "contacto": "@sora.sonne",
        "descripcion": "Cosplayer y cosmaker.",
    },
    {
        "nombre": "Claubailarinita",
        "tipo": "cosmaker",
        "region": None,
        "contacto": "@claubailarinita",
        "descripcion": "Cosmaker y bailarina.",
    },
    # --- Sastrería ------------------------------------------------------
    {
        "nombre": "By Nezu",
        "tipo": "sastre",
        "region": None,
        "contacto": "@by_nezu",
        "descripcion": "Diseño y confección de vestuario para cosplay.",
    },
    # --- Organizadores de eventos ---------------------------------------
    {
        "nombre": "Wonder Zone",
        "tipo": "organizador",
        "region": "Metropolitana",
        "contacto": "@wonderzone.cl",
        "descripcion": "Productora de eventos de cultura geek en Santiago.",
    },
    {
        "nombre": "Japan Geeks",
        "tipo": "organizador",
        "region": "Valparaíso",
        "contacto": "@japan.geeks",
        "descripcion": "Productora de eventos de la Región de Valparaíso.",
    },
    {
        "nombre": "Kizuna Fest",
        "tipo": "organizador",
        "region": "Coquimbo",
        "contacto": "@kizunafest.cl",
        "descripcion": "Festival de cultura japonesa en la Región de Coquimbo.",
    },
    {
        "nombre": "Fiesta Otaku",
        "tipo": "organizador",
        "region": "Metropolitana",
        "contacto": "@fiestaotaku.cl",
        "descripcion": "Eventos de cultura otaku en Santiago.",
    },
    {
        "nombre": "Feria Friki",
        "tipo": "organizador",
        "region": "Metropolitana",
        "contacto": "@feriafriki",
        "sitio_web": "https://www.feriafriki.cl",
        "descripcion": "Feria de cultura friki en Santiago, con sitio web propio.",
    },
    {
        "nombre": "Otaku Dance",
        "tipo": "organizador",
        "region": "Metropolitana",
        "contacto": "@otakudance",
        "descripcion": "Fiestas de música y cultura otaku en Santiago.",
    },
    # --- Otros oficios --------------------------------------------------
    {
        "nombre": "Kerochet",
        "tipo": "otro",
        "region": "Arica y Parinacota",
        "contacto": "@kerochet_",
        "descripcion": "Artículos de crochet hechos a mano en Arica.",
    },
]


def _normalizar(registro: dict) -> dict:
    return {campo: registro.get(campo) for campo in CAMPOS}


def cargar(sesion: Session) -> tuple[int, int]:
    """Crea las fichas que faltan y corrige las que cambiaron.

    Devuelve (creadas, actualizadas).
    """
    creadas = 0
    actualizadas = 0

    for bruto in REGISTROS:
        datos = _normalizar(bruto)
        existente = sesion.scalar(
            select(Proveedor).where(
                Proveedor.nombre == datos["nombre"],
                Proveedor.contacto == datos["contacto"],
            )
        )

        if existente is None:
            sesion.add(Proveedor(**datos))
            creadas += 1
            continue

        cambiado = False
        for campo, valor in datos.items():
            if getattr(existente, campo) != valor:
                setattr(existente, campo, valor)
                cambiado = True
        if cambiado:
            actualizadas += 1

    sesion.flush()
    return creadas, actualizadas


def main() -> None:
    from app.core.database import get_session_manager

    with get_session_manager().session() as sesion:
        creadas, actualizadas = cargar(sesion)

    print(f"fichas creadas:     {creadas}")
    print(f"fichas actualizadas: {actualizadas}")
    print(f"total definido:     {len(REGISTROS)}")


if __name__ == "__main__":
    main()
