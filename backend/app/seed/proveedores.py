"""Carga de las fichas semilla del directorio (T-13.5).

Origen de los datos
-------------------
Las 20 fichas salen del levantamiento de requerimientos del Sprint 1, no de
una lista inventada:

- 18 cuentas chilenas identificadas en los datasets de TikTok recogidos con
  Apify (`apify/dataset_tiktok-scraper_*.json`), cuyo perfil público declara
  una actividad de proveedor: tienda, cosmaker, sastre u organizadora de
  eventos.
- 2 tiendas nombradas por los propios usuarios en los comentarios de Instagram
  (Yui Chan Store y Arte Pierrot) no se incluyen: la mención no trae región ni
  tipo, y no hay perfil que lo confirme.

Qué se guarda y qué no
----------------------
Solo lo que la cuenta publica abiertamente: nombre comercial, tipo de
actividad, región cuando la declara, el usuario público y el sitio web de
negocio. **No se guardan correos, teléfonos ni nombres de personas**: aparecen
en varias biografías y no hacen falta para el directorio.

La región queda nula cuando la cuenta no la declara. Dos casos
(`Epic Animes`, `Hey Nana`) se deducen de la dirección comercial que publican
en su propia biografía; el resto se deja sin dato antes que rellenarlo con una
suposición.

Ejecución
---------
    python -m app.seed.proveedores

Es idempotente: no duplica fichas que ya existen.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.directorio import Proveedor

REGISTROS: list[dict] = [
    # --- Tiendas --------------------------------------------------------
    {
        "nombre": "Tienda Akiba-Kei",
        "tipo": "tienda",
        "region": None,
        "contacto": "@tienda.akibakei",
        "descripcion": "Tienda de artículos de anime con envíos a todo Chile, activa desde 2013.",
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
        "descripcion": "Corte láser de artículos de anime y cultura geek. Venta online.",
    },
    {
        "nombre": "Tienda Deck",
        "tipo": "tienda",
        "region": None,
        "contacto": "@tiendadeck",
        "sitio_web": "https://tiendadeck.cl",
        "descripcion": "Papelería, accesorios y artículos de colección.",
    },
    {
        "nombre": "FukuBox",
        "tipo": "tienda",
        "region": None,
        "contacto": "@fukubox.cl",
        "descripcion": "Servicio de compra y envío de productos japoneses a Chile.",
    },
    # --- Cosmaker -------------------------------------------------------
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
        "region": None,
        "contacto": "@fiestaotaku.cl",
        "descripcion": "Eventos de cultura otaku en Chile.",
    },
    {
        "nombre": "Feria Friki",
        "tipo": "organizador",
        "region": None,
        "contacto": "@feriafriki",
        "sitio_web": "https://www.feriafriki.cl",
        "descripcion": "Feria de cultura friki con sitio web propio.",
    },
    {
        "nombre": "Otaku Dance",
        "tipo": "organizador",
        "region": None,
        "contacto": "@otakudance",
        "descripcion": "Fiestas de música y cultura otaku.",
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


def cargar(sesion: Session) -> tuple[int, int]:
    """Inserta las fichas que falten. Devuelve (creadas, ya existentes)."""
    creadas = 0
    existentes = 0

    for registro in REGISTROS:
        ya_esta = sesion.scalar(
            select(Proveedor).where(
                Proveedor.nombre == registro["nombre"],
                Proveedor.contacto == registro["contacto"],
            )
        )
        if ya_esta is not None:
            existentes += 1
            continue

        sesion.add(Proveedor(**registro))
        creadas += 1

    sesion.flush()
    return creadas, existentes


def main() -> None:
    from app.core.database import get_session_manager

    with get_session_manager().session() as sesion:
        creadas, existentes = cargar(sesion)

    print(f"fichas creadas: {creadas}")
    print(f"ya existian:    {existentes}")
    print(f"total definido: {len(REGISTROS)}")


if __name__ == "__main__":
    main()
