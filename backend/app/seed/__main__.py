"""Carga datos semilla realistas para la demo.

Uso (desde backend/):
    python -m app.seed           # carga solo si la base está vacía
    python -m app.seed --reset   # vacía todas las tablas y vuelve a cargar
"""
import argparse
import asyncio
import logging

from sqlalchemy import func, select, text

from app.core.config import get_settings
from app.db.session_manager import DatabaseSessionManager
from app.models import Usuario
from app.seed.base import seed_base
from app.seed.imagenes import generar_todas

logger = logging.getLogger("cosplaychile.seed")

ETAPAS = [seed_base]

try:  # etapas de fases posteriores (se agregan a medida que existen)
    from app.seed.contenidos import seed_contenidos
    ETAPAS.append(seed_contenidos)
except ImportError:  # pragma: no cover
    pass
try:
    from app.seed.comunidad import seed_comunidad
    ETAPAS.append(seed_comunidad)
except ImportError:  # pragma: no cover
    pass


async def vaciar(s) -> None:
    tablas = (await s.execute(text(
        "SELECT tablename FROM pg_tables WHERE schemaname='public' AND tablename <> 'alembic_version'"
    ))).scalars().all()
    await s.execute(text(f"TRUNCATE {', '.join(tablas)} RESTART IDENTITY CASCADE"))


async def main(reset: bool) -> None:
    settings = get_settings()
    # Las ilustraciones viven en disco efímero en Render (plan free). El seed es
    # idempotente: si la BD ya tiene datos, antes se hacía `return` y los SVG no
    # se regeneraban tras un reinicio, dejando /media/seed/*.svg en 404.
    # Se generan SIEMPRE, antes de cualquier salida temprana.
    imagenes = generar_todas(settings.media_path)
    print(f"Ilustraciones listas: {len(imagenes)} SVG en {settings.media_path}")
    gestor = DatabaseSessionManager()
    gestor.init(settings.database_url)
    try:
        async with gestor.session() as s:
            if reset:
                await vaciar(s)
                await s.commit()
            elif (await s.scalar(select(func.count()).select_from(Usuario))) > 0:
                print("La base ya tiene datos. Usa --reset para recargar el seed.")
                return
            ctx = {"imagenes": imagenes}
            for etapa in ETAPAS:
                await etapa(s, ctx)
            await s.commit()
            print(f"Seed cargado ({len(ETAPAS)} etapas). Usuarios demo: clave 'Cosplay2026!', admin 'Admin2026!'.")
    finally:
        await gestor.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reset", action="store_true", help="vacía la base antes de cargar")
    asyncio.run(main(parser.parse_args().reset))
