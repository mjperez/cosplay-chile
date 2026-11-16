"""Infraestructura de pruebas.

- Usa TEST_DATABASE_URL (nunca la base de desarrollo).
- Recrea el esquema con la migración real de Alembic una vez por corrida.
- Vacía todas las tablas antes de cada prueba.
"""
import os
import tempfile

# Debe ocurrir ANTES de importar la app (get_settings queda en caché)
from app.core.config import get_settings  # noqa: E402

_s = get_settings()
os.environ["DATABASE_URL"] = _s.test_database_url
os.environ["MEDIA_DIR"] = tempfile.mkdtemp(prefix="cosplay-media-")
get_settings.cache_clear()

import asyncio  # noqa: E402
import uuid  # noqa: E402

import pytest  # noqa: E402
from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy import text  # noqa: E402
from sqlalchemy.ext.asyncio import create_async_engine  # noqa: E402
from sqlalchemy.pool import NullPool  # noqa: E402

from app.core.config import BACKEND_DIR  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.db.session_manager import DatabaseSessionManager  # noqa: E402
from app.main import app  # noqa: E402
from app.models import CategoriaContenido, Perfil, Usuario  # noqa: E402
from app.models.enums import EstadoUsuario, Region, Rol, TipoPerfil  # noqa: E402

TEST_URL = get_settings().database_url
assert "test" in TEST_URL, "Las pruebas solo pueden correr sobre una base de test"
PASSWORD = "Clave2026segura"


async def _reiniciar_esquema() -> None:
    engine = create_async_engine(TEST_URL, poolclass=NullPool)
    async with engine.begin() as conn:
        await conn.execute(text("DROP SCHEMA public CASCADE"))
        await conn.execute(text("CREATE SCHEMA public"))
    await engine.dispose()


@pytest.fixture(scope="session", autouse=True)
def esquema_bd():
    asyncio.run(_reiniciar_esquema())
    cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    cfg.attributes["database_url"] = TEST_URL
    command.upgrade(cfg, "head")
    yield


@pytest.fixture(scope="session")
async def gestor_bd(esquema_bd):
    gestor = DatabaseSessionManager()
    gestor.init(TEST_URL, poolclass=NullPool)
    yield gestor
    await gestor.close()


@pytest.fixture(autouse=True)
async def limpiar_tablas(gestor_bd):
    async with gestor_bd.session() as s:
        tablas = (await s.execute(text(
            "SELECT tablename FROM pg_tables WHERE schemaname='public' AND tablename <> 'alembic_version'"
        ))).scalars().all()
        await s.execute(text(f"TRUNCATE {', '.join(tablas)} RESTART IDENTITY CASCADE"))
        await s.commit()
    yield


@pytest.fixture
async def db(gestor_bd):
    async with gestor_bd.session() as s:
        yield s


@pytest.fixture
async def client(gestor_bd):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


# ---------------------------------------------------------------- helpers
async def crear_usuario(db, email: str, *, nombre: str = "Persona de prueba", rol: Rol = Rol.USUARIO,
                        estado: EstadoUsuario = EstadoUsuario.ACTIVO,
                        tipo: TipoPerfil = TipoPerfil.COSPLAYER, region: Region | None = Region.RM) -> Usuario:
    u = Usuario(nombre=nombre, email=email, password_hash=hash_password(PASSWORD), rol=rol, estado=estado)
    u.perfil = Perfil(tipo_perfil=tipo, region=region, redes_sociales=[], portafolio=[])
    db.add(u)
    await db.commit()
    return u


async def token_de(client, email: str) -> dict:
    r = await client.post("/api/auth/login", json={"email": email, "password": PASSWORD})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


async def crear_categoria(db, nombre: str = "Confección", slug: str = "confeccion") -> CategoriaContenido:
    c = CategoriaContenido(nombre=nombre, slug=slug, descripcion="")
    db.add(c)
    await db.commit()
    return c


@pytest.fixture
async def usuario(db):
    return await crear_usuario(db, "camila@test.cl", nombre="Camila")


@pytest.fixture
async def admin(db):
    return await crear_usuario(db, "admin@test.cl", nombre="Moderación", rol=Rol.ADMIN)


@pytest.fixture
async def auth_usuario(client, usuario):
    return await token_de(client, usuario.email)


@pytest.fixture
async def auth_admin(client, admin):
    return await token_de(client, admin.email)


def uid() -> str:
    return str(uuid.uuid4())
