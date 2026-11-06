"""Contenido editorial con Factory Method (US-08)."""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import update

from app.core.database import get_session_manager
from app.factories.contenido_factory import ContenidoFactory, TipoContenidoInvalido
from app.models.contenido import Articulo, Entrevista, GuiaTutorial
from app.models.usuario import Usuario

RUTA = "/api/v1/contenido"
ADMIN_CONTENIDO = "/api/v1/admin/contenido"


# --- Utilidades ---------------------------------------------------------


def _login(cliente, correo: str, password: str) -> str:
    respuesta = cliente.post(
        "/api/v1/auth/login", json={"correo": correo, "password": password}
    )
    assert respuesta.status_code == 200, respuesta.text
    return respuesta.json()["access_token"]


def _cabecera(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _promover_a_admin(correo: str) -> None:
    with get_session_manager().session() as sesion:
        sesion.execute(
            update(Usuario).where(Usuario.correo == correo).values(rol="administrador")
        )


@pytest.fixture
def autor(cliente, crear_usuario):
    """Usuario autenticado normal, con su token."""
    _, cuerpo = crear_usuario()
    return _login(cliente, cuerpo["correo"], cuerpo["password"])


@pytest.fixture
def admin(cliente, crear_usuario):
    """Usuario autenticado con rol administrador."""
    _, cuerpo = crear_usuario(correo="admin@ejemplo.cl")
    _promover_a_admin(cuerpo["correo"])
    return _login(cliente, cuerpo["correo"], cuerpo["password"])


@pytest.fixture
def categoria(cliente, admin) -> str:
    respuesta = cliente.post(
        f"{RUTA}/categorias",
        json={"nombre": "Armaduras", "descripcion": "Trabajo con goma eva y termoformado"},
        headers=_cabecera(admin),
    )
    assert respuesta.status_code == 201, respuesta.text
    return respuesta.json()["id_categoria"]


GUIA = {
    "tipo": "guia",
    "titulo": "Armadura de goma eva paso a paso",
    "resumen": "Cómo pasar de una plancha a una pieza con volumen",
    "nivel": "intermedio",
    "cuerpo": "<p>Primero se toma la <strong>medida</strong> del torso.</p>",
    "imagenes": ["https://ejemplo.cl/trazo.jpg"],
    "video_url": "https://www.youtube.com/watch?v=abc123",
    "personaje": "Knight Artorias",
    "medidas": [{"parte": "pecho", "valor": "98 cm"}],
    "tecnicas": ["termoformado", "sellado de bordes"],
    "presupuesto": "$45.000 a $60.000 CLP",
    "seguridad": "Ventilar el espacio al usar pegamento de contacto.",
    "pasos": ["Trazo", "Corte", "Termoformado", "Pintura"],
    "materiales": ["goma eva 10 mm", "pegamento de contacto"],
}

ENTREVISTA = {
    "tipo": "entrevista",
    "titulo": "Entrevista a una cosmaker de Valparaíso",
    "nivel": "basico",
    "cuerpo": "<p>Hablamos de cómo empezó.</p>",
    "preguntas": ["¿Cómo empezaste?", "¿Qué es lo más difícil?"],
    "respuestas": ["Con una peluca y una máquina prestada.", "El presupuesto."],
}

ARTICULO = {
    "tipo": "articulo",
    "titulo": "Dónde comprar telas en Santiago",
    "nivel": "basico",
    "cuerpo": "<p>Un recorrido por los locales del centro.</p>",
    "enlaces": ["https://ejemplo.cl/tiendas"],
}


# --- Criterio: el tipo produce la subclase correcta ----------------------


def _validar(cuerpo: dict):
    """Valida el cuerpo con el modelo Pydantic que corresponde al tipo."""
    from pydantic import TypeAdapter

    from app.schemas.contenido import ContenidoEntrada

    return TypeAdapter(ContenidoEntrada).validate_python(cuerpo)


@pytest.mark.parametrize(
    ("cuerpo", "clase"),
    [
        (GUIA, GuiaTutorial),
        (ENTREVISTA, Entrevista),
        (ARTICULO, Articulo),
    ],
)
def test_cada_tipo_produce_su_subclase(cuerpo, clase):
    creador = ContenidoFactory.para(cuerpo["tipo"])

    producto = creador.construir(_validar(cuerpo))

    assert isinstance(producto, clase)


def test_un_tipo_desconocido_no_tiene_creador():
    with pytest.raises(TipoContenidoInvalido):
        ContenidoFactory.para("podcast")


def test_un_tipo_desconocido_devuelve_422(cliente, autor):
    respuesta = cliente.post(
        RUTA, json={"tipo": "podcast", "titulo": "Algo"}, headers=_cabecera(autor)
    )
    assert respuesta.status_code == 422


# --- Criterio: los tres tipos se crean y serializan ---------------------


@pytest.mark.parametrize("cuerpo", [GUIA, ENTREVISTA, ARTICULO])
def test_crear_y_serializar_los_tres_tipos(cliente, autor, cuerpo):
    respuesta = cliente.post(RUTA, json=cuerpo, headers=_cabecera(autor))

    assert respuesta.status_code == 201, respuesta.text
    datos = respuesta.json()
    assert datos["tipo"] == cuerpo["tipo"]
    assert datos["titulo"] == cuerpo["titulo"]
    assert datos["estado"] == "pendiente"
    assert datos["cuerpo"] == cuerpo["cuerpo"]


def test_la_guia_conserva_sus_campos_propios(cliente, autor):
    datos = cliente.post(RUTA, json=GUIA, headers=_cabecera(autor)).json()

    assert datos["personaje"] == "Knight Artorias"
    assert datos["medidas"] == [{"parte": "pecho", "valor": "98 cm"}]
    assert datos["tecnicas"] == ["termoformado", "sellado de bordes"]
    assert datos["presupuesto"] == "$45.000 a $60.000 CLP"
    assert datos["seguridad"].startswith("Ventilar")
    assert datos["pasos"] == ["Trazo", "Corte", "Termoformado", "Pintura"]
    # Los campos de entrevista y artículo no aplican: llegan en null
    assert datos["preguntas"] is None
    assert datos["enlaces"] is None


# --- Criterio: validación de la URL de video ----------------------------


def test_video_de_dominio_no_permitido_se_rechaza(cliente, autor):
    respuesta = cliente.post(
        RUTA,
        json={**GUIA, "video_url": "https://vimeo.evil.example/video"},
        headers=_cabecera(autor),
    )
    assert respuesta.status_code == 422


def test_video_con_dominio_permitido_se_acepta(cliente, autor):
    for url in (
        "https://youtu.be/abc123",
        "https://vimeo.com/123456",
        "https://www.tiktok.com/@cuenta/video/1",
    ):
        respuesta = cliente.post(
            RUTA, json={**GUIA, "video_url": url}, headers=_cabecera(autor)
        )
        assert respuesta.status_code == 201, url


def test_video_vacio_se_interpreta_como_sin_video(cliente, autor):
    datos = cliente.post(
        RUTA, json={**GUIA, "video_url": ""}, headers=_cabecera(autor)
    ).json()
    assert datos["video_url"] is None


# --- Criterio: validación de categoría ----------------------------------


def test_categoria_inexistente_devuelve_422_con_mensaje(cliente, autor):
    respuesta = cliente.post(
        RUTA,
        json={**GUIA, "id_categoria": str(uuid.uuid4())},
        headers=_cabecera(autor),
    )

    assert respuesta.status_code == 422
    assert "no existe" in respuesta.json()["detail"]


def test_categoria_existente_se_acepta(cliente, autor, categoria):
    respuesta = cliente.post(
        RUTA, json={**GUIA, "id_categoria": categoria}, headers=_cabecera(autor)
    )

    assert respuesta.status_code == 201
    assert respuesta.json()["id_categoria"] == categoria


def test_categoria_duplicada_devuelve_409(cliente, admin):
    cuerpo = {"nombre": "Armaduras"}
    cliente.post(f"{RUTA}/categorias", json=cuerpo, headers=_cabecera(admin))
    respuesta = cliente.post(f"{RUTA}/categorias", json=cuerpo, headers=_cabecera(admin))

    assert respuesta.status_code == 409


def test_crear_categoria_exige_administrador(cliente, autor):
    respuesta = cliente.post(
        f"{RUTA}/categorias", json={"nombre": "Otra"}, headers=_cabecera(autor)
    )
    assert respuesta.status_code == 403


# --- Criterio: borrador oculto, publicación solo admin ------------------


def test_el_borrador_no_aparece_en_el_listado_publico(cliente, autor):
    cliente.post(RUTA, json=GUIA, headers=_cabecera(autor))

    publico = cliente.get(RUTA).json()

    assert publico["total"] == 0


def test_el_borrador_no_se_puede_ver_por_id(cliente, autor):
    creado = cliente.post(RUTA, json=GUIA, headers=_cabecera(autor)).json()

    respuesta = cliente.get(f"{RUTA}/{creado['id_contenido']}")

    assert respuesta.status_code == 404


def test_solo_el_administrador_publica(cliente, autor, admin):
    creado = cliente.post(RUTA, json=GUIA, headers=_cabecera(autor)).json()

    sin_permiso = cliente.post(
        f"{RUTA}/{creado['id_contenido']}/publicar", headers=_cabecera(autor)
    )
    assert sin_permiso.status_code == 403

    publicado = cliente.post(
        f"{RUTA}/{creado['id_contenido']}/publicar", headers=_cabecera(admin)
    )
    assert publicado.status_code == 200
    assert publicado.json()["estado"] == "publicado"
    assert publicado.json()["fecha_publicacion"] is not None


def test_tras_publicar_aparece_en_el_listado_y_por_id(cliente, autor, admin):
    creado = cliente.post(RUTA, json=GUIA, headers=_cabecera(autor)).json()
    cliente.post(f"{RUTA}/{creado['id_contenido']}/publicar", headers=_cabecera(admin))

    listado = cliente.get(RUTA).json()
    detalle = cliente.get(f"{RUTA}/{creado['id_contenido']}")

    assert listado["total"] == 1
    assert detalle.status_code == 200
    assert detalle.json()["titulo"] == GUIA["titulo"]


def test_crear_contenido_exige_autenticacion(cliente):
    assert cliente.post(RUTA, json=GUIA).status_code == 401


def test_la_bandeja_editorial_muestra_los_borradores(cliente, autor, admin):
    cliente.post(RUTA, json=GUIA, headers=_cabecera(autor))

    bandeja = cliente.get(ADMIN_CONTENIDO, headers=_cabecera(admin)).json()

    assert bandeja["total"] == 1
    assert bandeja["elementos"][0]["estado"] == "pendiente"


def test_la_bandeja_editorial_exige_administrador(cliente, autor):
    assert cliente.get(ADMIN_CONTENIDO, headers=_cabecera(autor)).status_code == 403


def test_filtro_por_tipo_en_el_listado_publico(cliente, autor, admin):
    for cuerpo in (GUIA, ENTREVISTA):
        creado = cliente.post(RUTA, json=cuerpo, headers=_cabecera(autor)).json()
        cliente.post(f"{RUTA}/{creado['id_contenido']}/publicar", headers=_cabecera(admin))

    guias = cliente.get(RUTA, params={"tipo": "guia"}).json()

    assert guias["total"] == 1
    assert guias["elementos"][0]["tipo"] == "guia"
