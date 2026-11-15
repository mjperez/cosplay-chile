"""Pruebas del patrón Adapter y de la subida de imágenes.

Verifican la traducción de la interfaz interna al proveedor externo, la
lista blanca de formatos (OWASP A03) y la autorización del borrado. El test
final fija en código que **los cuatro patrones del informe ES2** están
implementados y no solo descritos.
"""

from __future__ import annotations

import uuid
from pathlib import Path

import pytest

from app.adapters.almacenamiento import (
    AlmacenamientoLocalAdapter,
    AlmacenamientoNoConfigurado,
    ArchivoNoEncontrado,
    ClienteCloudinaryHTTP,
    CloudinaryStorageAdapter,
    IAlmacenamientoArchivos,
    obtener_almacenamiento,
)
from app.core.config import Settings
from app.services import archivos as servicio

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64
JPEG = b"\xff\xd8\xff" + b"\x00" * 64
WEBP = b"RIFF" + b"\x00\x00\x00\x00" + b"WEBP" + b"\x00" * 32
SVG = b'<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>'

ARCHIVOS = "/api/v1/archivos"


def _login(cliente, correo: str, password: str) -> str:
    respuesta = cliente.post(
        "/api/v1/auth/login", json={"correo": correo, "password": password}
    )
    assert respuesta.status_code == 200, respuesta.text
    return respuesta.json()["access_token"]


def _cabecera(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _settings(**cambios) -> Settings:
    base = {
        "database_url": "sqlite+pysqlite:///:memory:",
        "jwt_secret": "clave-de-prueba-con-mas-de-16-caracteres",
    }
    return Settings(_env_file=None, **{**base, **cambios})


# --- Interfaz y adaptadores ------------------------------------------------


def test_la_interfaz_tiene_los_tres_metodos_comprometidos_en_el_es2():
    metodos = {nombre for nombre in dir(IAlmacenamientoArchivos) if not nombre.startswith("_")}
    assert {"guardar_archivo", "eliminar_archivo", "obtener_enlace"} <= metodos


def test_el_adaptador_local_guarda_devuelve_enlace_y_borra(tmp_path):
    adaptador = AlmacenamientoLocalAdapter(tmp_path / "imagenes")

    enlace = adaptador.guardar_archivo("usuario-1/foto.png", PNG)
    assert enlace == "/archivos/usuario-1/foto.png"
    assert (tmp_path / "imagenes" / "usuario-1" / "foto.png").read_bytes() == PNG
    assert adaptador.obtener_enlace("usuario-1/foto.png") == enlace

    adaptador.eliminar_archivo("usuario-1/foto.png")
    with pytest.raises(ArchivoNoEncontrado):
        adaptador.eliminar_archivo("usuario-1/foto.png")


def test_el_adaptador_rechaza_salir_del_directorio(tmp_path):
    adaptador = AlmacenamientoLocalAdapter(tmp_path / "imagenes")
    with pytest.raises(ValueError, match="fuera del directorio"):
        adaptador.guardar_archivo("../../escape.png", PNG)


def test_cloudinary_traduce_las_tres_operaciones_al_cliente_externo():
    class Doble:
        cloud_name = "nube-demo"

        def __init__(self) -> None:
            self.subidas: list[tuple[str, bytes]] = []
            self.borrados: list[str] = []

        def subir(self, public_id: str, contenido: bytes) -> str:
            self.subidas.append((public_id, contenido))
            return "https://res.cloudinary.com/nube-demo/image/upload/foto.png"

        def borrar(self, public_id: str) -> None:
            self.borrados.append(public_id)

    cliente = Doble()
    adaptador = CloudinaryStorageAdapter(cliente)

    assert adaptador.guardar_archivo("usuario-1/foto.png", PNG).startswith("https://")
    assert cliente.subidas == [("cosplay-chile/usuario-1/foto", PNG)]

    adaptador.eliminar_archivo("usuario-1/foto.png")
    assert cliente.borrados == ["cosplay-chile/usuario-1/foto"]

    enlace = adaptador.obtener_enlace("usuario-1/foto.png")
    assert "res.cloudinary.com/nube-demo" in enlace
    assert "cosplay-chile/usuario-1/foto" in enlace


def test_el_cliente_http_firma_la_peticion_y_envia_el_binario():
    class Respuesta:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self) -> bytes:
            return b'{"secure_url": "https://cdn/x.png", "result": "ok"}'

    capturadas = []

    def abrir(peticion, timeout=None):
        capturadas.append(peticion)
        return Respuesta()

    cliente = ClienteCloudinaryHTTP("nube", "clave", "secreto", abrir=abrir)
    assert cliente.subir("carpeta/foto", PNG) == "https://cdn/x.png"

    peticion = capturadas[0]
    cuerpo = peticion.data
    assert "multipart/form-data" in peticion.get_header("Content-type")
    assert b'name="signature"' in cuerpo
    assert b'name="api_key"' in cuerpo
    assert b'name="timestamp"' in cuerpo
    assert PNG in cuerpo
    assert b"secreto" not in cuerpo  # el secreto se usa para firmar, nunca se envía

    cliente.borrar("carpeta/foto")
    assert len(capturadas) == 2


def test_la_fabrica_elige_el_backend_y_exige_credenciales(tmp_path):
    local = obtener_almacenamiento(
        _settings(storage_backend="local", storage_directorio=str(tmp_path / "f"))
    )
    assert isinstance(local, AlmacenamientoLocalAdapter)

    with pytest.raises(AlmacenamientoNoConfigurado, match="CLOUDINARY"):
        obtener_almacenamiento(_settings(storage_backend="cloudinary"))

    nube = obtener_almacenamiento(
        _settings(
            storage_backend="cloudinary",
            cloudinary_cloud_name="nube",
            cloudinary_api_key="clave",
            cloudinary_api_secret="secreto",
        )
    )
    assert isinstance(nube, CloudinaryStorageAdapter)


def test_las_credenciales_viven_en_la_configuracion_no_en_el_codigo():
    campos = Settings.model_fields
    assert {"cloudinary_cloud_name", "cloudinary_api_key", "cloudinary_api_secret"} <= set(campos)
    fuente = Path(__file__).resolve().parents[1] / "app/adapters/almacenamiento.py"
    texto = fuente.read_text()
    # El adaptador recibe el secreto por constructor y lo usa sólo para firmar.
    assert "get_settings" in texto
    assert "self._api_secret" in texto


# --- Whitelist del servicio -------------------------------------------------


def test_el_servicio_acepta_solo_los_tres_formatos_de_la_lista_blanca(tmp_path):
    adaptador = AlmacenamientoLocalAdapter(tmp_path / "f")
    for tipo, binario in (
        ("image/png", PNG),
        ("image/jpeg", JPEG),
        ("image/webp", WEBP),
    ):
        resultado = servicio.guardar(adaptador, binario, tipo, uuid.uuid4())
        assert resultado.tipo_mime == tipo
        assert resultado.enlace.startswith("/archivos/")


def test_el_servicio_rechaza_un_tipo_fuera_de_la_lista(tmp_path):
    adaptador = AlmacenamientoLocalAdapter(tmp_path / "f")
    with pytest.raises(servicio.TipoNoPermitido):
        servicio.guardar(adaptador, SVG, "image/svg+xml", uuid.uuid4())


def test_el_servicio_no_confia_en_el_content_type_declarado(tmp_path):
    adaptador = AlmacenamientoLocalAdapter(tmp_path / "f")
    with pytest.raises(servicio.ContenidoNoCoincide):
        servicio.guardar(adaptador, SVG, "image/png", uuid.uuid4())


def test_el_servicio_rechaza_vacios_y_demasiado_grandes(tmp_path):
    adaptador = AlmacenamientoLocalAdapter(tmp_path / "f")
    with pytest.raises(servicio.ArchivoVacio):
        servicio.guardar(adaptador, b"", "image/png", uuid.uuid4())
    with pytest.raises(servicio.ArchivoDemasiadoGrande):
        servicio.guardar(
            adaptador, PNG + b"0" * (5 * 1024 * 1024), "image/png", uuid.uuid4()
        )


# --- HTTP -------------------------------------------------------------------


def test_subir_una_imagen_por_http_y_servirla(cliente, crear_usuario):
    _, cuerpo = crear_usuario(correo="fotos@ejemplo.cl")
    token = _login(cliente, cuerpo["correo"], cuerpo["password"])

    respuesta = cliente.post(
        ARCHIVOS,
        files={"archivo": ("foto.png", PNG, "image/png")},
        headers=_cabecera(token),
    )
    assert respuesta.status_code == 201, respuesta.text
    datos = respuesta.json()
    assert datos["tipo_mime"] == "image/png"
    assert datos["tamano"] == len(PNG)
    assert datos["identificador"].endswith(".png")
    # URL absoluta: el frontend la guarda en un campo HttpUrl del contenido.
    assert datos["enlace"].startswith("http")

    servido = cliente.get(datos["enlace"])
    assert servido.status_code == 200
    assert servido.content == PNG


@pytest.mark.parametrize(
    "nombre,binario,tipo,esperado",
    [
        ("falso.png", SVG, "image/png", 415),
        ("vector.svg", SVG, "image/svg+xml", 415),
        ("vacio.png", b"", "image/png", 400),
    ],
)
def test_la_api_rechaza_entradas_peligrosas(
    cliente, crear_usuario, nombre, binario, tipo, esperado
):
    _, cuerpo = crear_usuario(correo="validacion@ejemplo.cl")
    token = _login(cliente, cuerpo["correo"], cuerpo["password"])
    respuesta = cliente.post(
        ARCHIVOS,
        files={"archivo": (nombre, binario, tipo)},
        headers=_cabecera(token),
    )
    assert respuesta.status_code == esperado, respuesta.text


def test_sin_token_no_se_puede_subir(cliente):
    respuesta = cliente.post(
        ARCHIVOS, files={"archivo": ("foto.png", PNG, "image/png")}
    )
    assert respuesta.status_code == 401


def test_no_se_puede_borrar_un_archivo_de_otra_cuenta(cliente, crear_usuario):
    _, dueno = crear_usuario(correo="dueno@ejemplo.cl")
    _, otro = crear_usuario(correo="otro@ejemplo.cl")
    token_dueno = _login(cliente, dueno["correo"], dueno["password"])
    token_otro = _login(cliente, otro["correo"], otro["password"])

    subida = cliente.post(
        ARCHIVOS,
        files={"archivo": ("foto.png", PNG, "image/png")},
        headers=_cabecera(token_dueno),
    )
    identificador = subida.json()["identificador"]

    ajeno = cliente.delete(
        f"{ARCHIVOS}/{identificador}", headers=_cabecera(token_otro)
    )
    assert ajeno.status_code == 403

    propia = cliente.delete(
        f"{ARCHIVOS}/{identificador}", headers=_cabecera(token_dueno)
    )
    assert propia.status_code == 204


# --- Trazabilidad con el informe -------------------------------------------


def test_los_cuatro_patrones_del_informe_estan_implementados(cliente):
    """Singleton, Factory Method, Observer y Adapter, no solo documentados."""
    from app.core.database import DatabaseSessionManager
    from app.events.gestor import GestorEventos, Observador, gestor_eventos
    from app.factories.contenido_factory import ContenidoFactory, CreadorContenido

    # 1. Singleton: dos llamadas devuelven el mismo objeto.
    assert DatabaseSessionManager() is DatabaseSessionManager()

    # 2. Factory Method: creadores polimórficos registrados por tipo.
    assert set(ContenidoFactory.tipos()) == {"guia", "entrevista", "articulo"}
    assert issubclass(ContenidoFactory.para("guia").__class__, CreadorContenido)

    # 3. Observer: sujeto con suscriptores que implementan actualizar().
    assert isinstance(gestor_eventos, GestorEventos)
    assert len(gestor_eventos.observadores()) == 3
    assert all(
        callable(getattr(observador, "actualizar", None))
        and isinstance(observador, Observador)
        for observador in gestor_eventos.observadores()
    )

    # 4. Adapter: interfaz interna con un adaptador concreto hacia el externo.
    assert issubclass(CloudinaryStorageAdapter, IAlmacenamientoArchivos)
    assert issubclass(AlmacenamientoLocalAdapter, IAlmacenamientoArchivos)
