"""Directorio de proveedores: listado, filtros y paginación (US-13)."""

from __future__ import annotations

from app.core.database import get_session_manager
from app.seed import proveedores as semilla

RUTA = "/api/v1/proveedores"


def _cargar_semilla() -> None:
    with get_session_manager().session() as sesion:
        semilla.cargar(sesion)


def test_directorio_vacio_devuelve_total_cero(cliente):
    respuesta = cliente.get(RUTA)

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["total"] == 0
    assert cuerpo["elementos"] == []


def test_la_semilla_carga_las_veinte_fichas(cliente):
    _cargar_semilla()

    cuerpo = cliente.get(RUTA, params={"limite": 100}).json()

    assert cuerpo["total"] == 20
    assert len(cuerpo["elementos"]) == 20


def test_la_semilla_es_idempotente(cliente):
    _cargar_semilla()
    _cargar_semilla()

    assert cliente.get(RUTA, params={"limite": 100}).json()["total"] == 20


def test_filtra_por_region(cliente):
    _cargar_semilla()

    cuerpo = cliente.get(RUTA, params={"region": "Valparaíso"}).json()

    assert cuerpo["total"] == 1
    assert cuerpo["elementos"][0]["nombre"] == "Japan Geeks"


def test_el_filtro_de_region_no_distingue_mayusculas(cliente):
    _cargar_semilla()

    en_minusculas = cliente.get(RUTA, params={"region": "valparaíso"}).json()
    en_mayusculas = cliente.get(RUTA, params={"region": "VALPARAÍSO"}).json()

    assert en_minusculas["total"] == en_mayusculas["total"] == 1


def test_filtra_por_tipo(cliente):
    _cargar_semilla()

    cuerpo = cliente.get(RUTA, params={"tipo": "organizador", "limite": 100}).json()

    assert cuerpo["total"] == 6
    assert all(p["tipo"] == "organizador" for p in cuerpo["elementos"])


def test_busqueda_por_texto_libre(cliente):
    _cargar_semilla()

    cuerpo = cliente.get(RUTA, params={"q": "peluca"}).json()

    assert cuerpo["total"] >= 1
    assert any("peluca" in (p["descripcion"] or "").lower() for p in cuerpo["elementos"])


def test_filtra_fichas_sin_region_declarada(cliente):
    _cargar_semilla()

    cuerpo = cliente.get(RUTA, params={"sin_region": True, "limite": 100}).json()

    assert cuerpo["total"] == 13
    assert all(p["region"] is None for p in cuerpo["elementos"])


def test_paginacion_no_repite_elementos(cliente):
    _cargar_semilla()

    primera = cliente.get(RUTA, params={"limite": 10, "desplazamiento": 0}).json()
    segunda = cliente.get(RUTA, params={"limite": 10, "desplazamiento": 10}).json()

    assert primera["total"] == segunda["total"] == 20
    assert len(primera["elementos"]) == len(segunda["elementos"]) == 10
    nombres_primera = {p["id_proveedor"] for p in primera["elementos"]}
    nombres_segunda = {p["id_proveedor"] for p in segunda["elementos"]}
    assert nombres_primera.isdisjoint(nombres_segunda)


def test_limite_fuera_de_rango_se_rechaza(cliente):
    assert cliente.get(RUTA, params={"limite": 500}).status_code == 422
    assert cliente.get(RUTA, params={"desplazamiento": -1}).status_code == 422


def test_opciones_devuelve_las_regiones_cargadas(cliente):
    _cargar_semilla()

    cuerpo = cliente.get(f"{RUTA}/opciones").json()

    assert "Metropolitana" in cuerpo["regiones"]
    assert "Valparaíso" in cuerpo["regiones"]
    assert cuerpo["hay_sin_region"] is True
    assert "organizador" in cuerpo["tipos"]


def test_el_directorio_es_publico(cliente):
    """Sin token: el directorio se consulta sin iniciar sesión."""
    assert cliente.get(RUTA).status_code == 200
