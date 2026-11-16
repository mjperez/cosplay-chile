"""Singleton (DatabaseSessionManager) y Adapter (IAlmacenamientoArchivos)."""
import threading

import pytest

from app.db.session_manager import DatabaseSessionManager
from app.patterns.storage import CloudinaryStorageAdapter, IAlmacenamientoArchivos, LocalStorageAdapter

PNG_1x1 = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
    b"\x00\x00\x00\rIDATx\x9cc\xf8\xff\xff?\x00\x05\xfe\x02\xfe\xa7\x9a\x8d\x1f\x00\x00\x00\x00IEND\xaeB`\x82"
)


# ------------------------------------------------------------- Singleton
def test_singleton_devuelve_siempre_la_misma_instancia():
    instancias = []
    hilos = [threading.Thread(target=lambda: instancias.append(DatabaseSessionManager())) for _ in range(20)]
    for h in hilos:
        h.start()
    for h in hilos:
        h.join()
    assert len({id(i) for i in instancias}) == 1
    assert DatabaseSessionManager() is instancias[0]


async def test_singleton_comparte_un_solo_motor(gestor_bd):
    assert DatabaseSessionManager().engine is gestor_bd.engine
    gestor_bd.init("postgresql+asyncpg://otro/ignorado")  # idempotente: no reemplaza el motor
    assert DatabaseSessionManager().engine is gestor_bd.engine


async def test_get_db_entrega_sesiones_del_mismo_motor(gestor_bd):
    from app.db.session_manager import get_db

    gen = get_db()
    sesion = await anext(gen)
    assert sesion.bind is gestor_bd.engine
    await gen.aclose()


# --------------------------------------------------------------- Adapter
async def test_local_adapter_cumple_la_interfaz(tmp_path):
    adapter = LocalStorageAdapter(tmp_path)
    assert isinstance(adapter, IAlmacenamientoArchivos)
    clave = await adapter.guardar_archivo(PNG_1x1, "subidas/prueba.png", "image/png")
    assert (tmp_path / "subidas" / "prueba.png").read_bytes() == PNG_1x1
    assert adapter.obtener_enlace(clave) == "/media/subidas/prueba.png"
    await adapter.eliminar_archivo(clave)
    assert not (tmp_path / "subidas" / "prueba.png").exists()


async def test_local_adapter_bloquea_path_traversal(tmp_path):
    with pytest.raises(ValueError):
        await LocalStorageAdapter(tmp_path).guardar_archivo(b"x", "../fuera.png", "image/png")


class _SdkFalso:
    """Doble del SDK de Cloudinary para comprobar la traducción de llamadas."""

    def __init__(self):
        self.llamadas = []
        sdk = self

        class uploader:
            @staticmethod
            def upload(archivo, **kw):
                sdk.llamadas.append(("upload", kw))

            @staticmethod
            def destroy(public_id, **kw):
                sdk.llamadas.append(("destroy", public_id))

        class utils:
            @staticmethod
            def cloudinary_url(public_id, **kw):
                return f"https://res.cloudinary.com/demo/image/upload/{public_id}", {}

        self.uploader, self.utils = uploader, utils


async def test_cloudinary_adapter_traduce_a_la_api_externa():
    sdk = _SdkFalso()
    adapter = CloudinaryStorageAdapter("cloudinary://x:y@demo", sdk=sdk)
    clave = await adapter.guardar_archivo(PNG_1x1, "subidas/foto.png", "image/png")
    assert clave == "cosplaychile/subidas/foto"
    assert adapter.obtener_enlace(clave).startswith("https://res.cloudinary.com/")
    await adapter.eliminar_archivo(clave)
    assert [c[0] for c in sdk.llamadas] == ["upload", "destroy"]


async def test_subida_de_imagen_valida_tipo_y_tamano(client, auth_usuario):
    r = await client.post("/api/archivos", headers=auth_usuario,
                          files={"archivo": ("foto.png", PNG_1x1, "image/png")})
    assert r.status_code == 201, r.text
    assert r.json()["url"].startswith("/media/subidas/")

    # Un .png que en realidad es texto se rechaza por su firma binaria
    r = await client.post("/api/archivos", headers=auth_usuario,
                          files={"archivo": ("falso.png", b"<script>", "image/png")})
    assert r.status_code == 415

    # UC6 excepción 2: archivo demasiado grande indica el límite
    grande = PNG_1x1 + b"0" * (5 * 1024 * 1024)
    r = await client.post("/api/archivos", headers=auth_usuario,
                          files={"archivo": ("grande.png", grande, "image/png")})
    assert r.status_code == 413
    assert "5 MB" in r.json()["detail"]


async def test_subida_requiere_sesion(client):
    r = await client.post("/api/archivos", files={"archivo": ("foto.png", PNG_1x1, "image/png")})
    assert r.status_code == 401
