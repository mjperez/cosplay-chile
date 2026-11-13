"""La semilla de demostración deja la plataforma lista para exponer en clases.

Verifica que cargue todos los módulos, que sea idempotente y que no se pueda
ejecutar por accidente contra la base de producción.
"""

from __future__ import annotations

import pytest

from app.core.database import get_session_manager
from app.repositories import usuario as repo_usuarios
from app.seed import demo

RUTA_EVENTOS = "/api/v1/eventos"
RUTA_FORO = "/api/v1/foro/temas"
RUTA_CONTENIDO = "/api/v1/contenido"


def _cargar() -> None:
    with get_session_manager().session() as sesion:
        demo.cargar(sesion)


def _total(cliente, ruta: str, **params) -> int:
    return cliente.get(ruta, params=params).json()["total"]


def test_la_semilla_deja_todos_los_modulos_con_datos(cliente):
    _cargar()

    assert _total(cliente, "/api/v1/proveedores", limite=100) == 20
    assert len(cliente.get(f"{RUTA_CONTENIDO}/categorias").json()) == 5
    assert _total(cliente, RUTA_EVENTOS, limite=100) == 6
    assert _total(cliente, RUTA_FORO, limite=100) == 5
    assert _total(cliente, "/api/v1/tiendas") == 6
    assert _total(cliente, "/api/v1/grupos") == 5
    assert _total(cliente, "/api/v1/desafios") == 2
    assert _total(cliente, RUTA_CONTENIDO, limite=100) == 3


def test_el_contenido_de_demo_queda_publicado(cliente):
    _cargar()

    cuerpo = cliente.get(RUTA_CONTENIDO, params={"limite": 100}).json()
    assert cuerpo["total"] == 3
    assert all(item["estado"] == "publicado" for item in cuerpo["elementos"])
    assert {"guia", "entrevista", "articulo"} == {item["tipo"] for item in cuerpo["elementos"]}


def test_las_cuentas_demo_permiten_entrar(cliente):
    _cargar()

    respuesta = cliente.post(
        "/api/v1/auth/login",
        json={"correo": "demo@cosplay.cl", "password": demo.PASSWORD_DEMO},
    )
    assert respuesta.status_code == 200, respuesta.text
    assert respuesta.json()["usuario"]["rol"] == "administrador"

    respuesta_cosplayer = cliente.post(
        "/api/v1/auth/login",
        json={"correo": "cosplayer@cosplay.cl", "password": demo.PASSWORD_DEMO},
    )
    assert respuesta_cosplayer.status_code == 200


def test_las_cuentas_demo_se_llaman_segun_su_rol(cliente):
    """El nombre visible debe decir el permiso, no sonar a persona inventada."""
    _cargar()

    etiquetas = {
        "administrador": "Usuario Administrador",
        "cosplayer": "Usuario Cosplayer",
        "organizador": "Usuario Organizador",
    }
    for dato in demo.USUARIOS_DEMO:
        assert dato["nombre"] == etiquetas[dato["rol"]]

    respuesta = cliente.post(
        "/api/v1/auth/login",
        json={"correo": "demo@cosplay.cl", "password": demo.PASSWORD_DEMO},
    )
    assert respuesta.status_code == 200, respuesta.text
    assert respuesta.json()["usuario"]["nombre"] == "Usuario Administrador"


def test_recargar_la_semilla_corrige_nombres_de_cuentas_ya_creadas(cliente):
    """Una base creada con la versión anterior debe adoptar las etiquetas nuevas."""
    _cargar()

    with get_session_manager().session() as sesion:
        cuenta = repo_usuarios.obtener_por_correo(sesion, "demo@cosplay.cl")
        repo_usuarios.actualizar_nombre(sesion, cuenta, nombre="Camila Rojas")

    _cargar()

    with get_session_manager().session() as sesion:
        cuenta = repo_usuarios.obtener_por_correo(sesion, "demo@cosplay.cl")
        assert cuenta.nombre == "Usuario Administrador"
        assert cuenta.rol == "administrador"
        assert repo_usuarios.contar(sesion) == 3  # no se duplicó la cuenta

    respuesta = cliente.post(
        "/api/v1/auth/login",
        json={"correo": "demo@cosplay.cl", "password": demo.PASSWORD_DEMO},
    )
    assert respuesta.status_code == 200, respuesta.text
    assert respuesta.json()["usuario"]["nombre"] == "Usuario Administrador"


def test_el_detalle_de_un_evento_muestra_participantes(cliente):
    _cargar()

    eventos = cliente.get(RUTA_EVENTOS, params={"limite": 100}).json()["elementos"]
    assert sum(evento["total_participantes"] for evento in eventos) >= 3


def test_la_semilla_es_idempotente(cliente):
    _cargar()
    _cargar()

    assert _total(cliente, RUTA_EVENTOS, limite=100) == 6
    assert _total(cliente, RUTA_FORO, limite=100) == 5
    assert _total(cliente, RUTA_CONTENIDO, limite=100) == 3
    assert _total(cliente, "/api/v1/tiendas") == 6
    assert _total(cliente, "/api/v1/grupos") == 5
    assert _total(cliente, "/api/v1/desafios") == 2


def test_el_perfil_de_ejemplo_es_publico(cliente):
    _cargar()

    respuesta = cliente.post(
        "/api/v1/auth/login",
        json={"correo": "cosplayer@cosplay.cl", "password": demo.PASSWORD_DEMO},
    )
    id_usuario = respuesta.json()["usuario"]["id_usuario"]

    perfil = cliente.get(f"/api/v1/perfiles/{id_usuario}").json()
    assert perfil["especialidad"] == "Armaduras y props con goma eva"
    assert "correo" not in perfil


def test_la_semilla_se_rechaza_en_produccion(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.delenv("DEMO_SEED", raising=False)

    with pytest.raises(SystemExit, match="rechazado en producción"):
        demo.main()
