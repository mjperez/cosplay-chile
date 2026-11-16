"""Patrón Factory Method: ContenidoFactory.crear_contenido(tipo, datos)."""
import uuid

import pytest

from app.models import ArticuloTecnico, Entrevista, GuiaTutorial
from app.models.contenido import Contenido, ContenidoInvalido
from app.models.enums import EstadoPublicacion, TipoContenido
from app.patterns.contenido_factory import CategoriaNoEncontrada, ContenidoFactory, TipoContenidoDesconocido
from tests.conftest import crear_categoria


def _datos(categoria, autor, **extra):
    return {"titulo": "Mi primera armadura", "descripcion": "Guía para principiantes", "nivel": "PRINCIPIANTE",
            "categoria_id": str(categoria.id), "autor_id": autor.id, **extra}


@pytest.fixture
async def categoria(db):
    return await crear_categoria(db)


@pytest.mark.parametrize(
    "tipo,clase,extra",
    [
        ("GUIA", GuiaTutorial, {"pasos": ["Cortar", "Sellar"], "materiales": ["Goma EVA"]}),
        ("ENTREVISTA", Entrevista, {"entrevistado": "Rocío", "preguntas": ["¿Cómo partiste?"],
                                     "respuestas": ["Con un traje de mi anime favorito"]}),
        ("ARTICULO", ArticuloTecnico, {"enlaces": ["https://es.wikipedia.org/wiki/Cosplay"]}),
    ],
)
async def test_factory_crea_la_subclase_correcta_en_estado_pendiente(db, categoria, usuario, tipo, clase, extra):
    c = await ContenidoFactory(db).crear_contenido(tipo, _datos(categoria, usuario, **extra))
    assert type(c) is clase
    assert isinstance(c, Contenido)
    assert c.tipo == TipoContenido(tipo)
    assert c.estado == EstadoPublicacion.PENDIENTE
    assert c.categoria_id == categoria.id
    await db.commit()
    # La herencia de tabla única devuelve la subclase al leer desde la BD
    db.expunge_all()
    leido = await db.get(Contenido, c.id)
    assert type(leido) is clase


@pytest.mark.parametrize(
    "tipo,extra,mensaje",
    [
        ("GUIA", {"pasos": [], "materiales": ["EVA"]}, "al menos un paso"),
        ("GUIA", {"pasos": ["Cortar"], "materiales": []}, "materiales"),
        ("ENTREVISTA", {"entrevistado": "X", "preguntas": ["a", "b"], "respuestas": ["1"]}, "respuesta"),
        ("ENTREVISTA", {"preguntas": ["a"], "respuestas": ["1"]}, "entrevista"),
        ("ARTICULO", {"enlaces": []}, "enlace"),
        ("ARTICULO", {"enlaces": ["ftp://no-sirve"]}, "no válido"),
    ],
)
async def test_cada_subclase_aplica_su_propia_validacion(db, categoria, usuario, tipo, extra, mensaje):
    with pytest.raises(ContenidoInvalido, match=mensaje):
        await ContenidoFactory(db).crear_contenido(tipo, _datos(categoria, usuario, **extra))


async def test_factory_valida_que_la_categoria_exista(db, usuario):
    datos = {"titulo": "x", "descripcion": "y", "nivel": "PRINCIPIANTE", "autor_id": usuario.id,
             "pasos": ["a"], "materiales": ["b"]}
    for categoria_id in (str(uuid.uuid4()), "no-es-un-uuid", None):
        with pytest.raises(CategoriaNoEncontrada):
            await ContenidoFactory(db).crear_contenido("GUIA", {**datos, "categoria_id": categoria_id})


async def test_factory_rechaza_tipos_desconocidos(db, categoria, usuario):
    with pytest.raises(TipoContenidoDesconocido):
        await ContenidoFactory(db).crear_contenido("PODCAST", _datos(categoria, usuario))


async def test_imagen_sin_texto_alternativo_es_invalida(db, categoria, usuario):
    with pytest.raises(ContenidoInvalido, match="texto alternativo"):
        await ContenidoFactory(db).crear_contenido(
            "GUIA", _datos(categoria, usuario, pasos=["a"], materiales=["b"], imagen_url="/media/x.png"))


def test_factory_es_extensible_sin_tocar_controladores():
    assert set(ContenidoFactory.tipos_disponibles()) == {TipoContenido.GUIA, TipoContenido.ENTREVISTA,
                                                         TipoContenido.ARTICULO}
