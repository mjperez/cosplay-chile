"""Pruebas del panel de administración (RF de gestión y moderación).

Verifican tres cosas que no se pueden comprobar solo mirando la interfaz:
que **todos** los endpoints nacen protegidos por rol, que las operaciones
escriben de verdad en la base y que las transiciones inválidas se rechazan.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import get_args

import pytest
from sqlalchemy import update

from app.core.database import get_session_manager
from app.models.comunidad import ESTADOS_FORO
from app.models.directorio import PLATAFORMAS, TIPOS_TIENDA
from app.models.usuario import Usuario
from app.schemas.admin import EstadoTemaEntrada, GrupoEntrada, TiendaEntrada

ADMIN = "/api/v1/admin"
CONTENIDO = "/api/v1/contenido"
FORO = "/api/v1/foro/temas"
EVENTOS = "/api/v1/eventos"

GUIA = {
    "tipo": "guia",
    "titulo": "Armadura de goma eva paso a paso",
    "resumen": "Cómo pasar de una plancha a una pieza con volumen",
    "nivel": "intermedio",
    "cuerpo": "<p>Primero se toma la medida del torso.</p>",
    "pasos": ["Trazo", "Corte", "Pintura"],
    "materiales": ["goma eva 10 mm"],
}


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


def _fecha(dias: int) -> str:
    return (datetime.now(timezone.utc) + timedelta(days=dias)).replace(microsecond=0).isoformat()


@pytest.fixture
def usuario(cliente, crear_usuario):
    _, cuerpo = crear_usuario(correo="cosplayer@ejemplo.cl")
    return cuerpo, _login(cliente, cuerpo["correo"], cuerpo["password"])


@pytest.fixture
def admin(cliente, crear_usuario):
    _, cuerpo = crear_usuario(correo="admin@ejemplo.cl")
    _promover_a_admin(cuerpo["correo"])
    return cuerpo, _login(cliente, cuerpo["correo"], cuerpo["password"])


@pytest.fixture
def guia(cliente, usuario) -> str:
    _, token = usuario
    respuesta = cliente.post(CONTENIDO, json=GUIA, headers=_cabecera(token))
    assert respuesta.status_code == 201, respuesta.text
    return respuesta.json()["id_contenido"]


@pytest.fixture
def evento(cliente, admin) -> str:
    _, token = admin
    respuesta = cliente.post(
        f"{ADMIN}/eventos",
        json={
            "nombre": "Convención Cosplay Santiago 2026",
            "tipo": "convencion",
            "fecha_inicio": _fecha(20),
            "lugar": "Estación Mapocho",
            "region": "Metropolitana",
        },
        headers=_cabecera(token),
    )
    assert respuesta.status_code == 201, respuesta.text
    return respuesta.json()["id_evento"]


# --- Contrato y permisos -------------------------------------------------

def test_las_rutas_del_panel_estan_en_openapi(cliente):
    rutas = cliente.get("/openapi.json").json()["paths"]

    for ruta in (
        f"{ADMIN}/resumen",
        f"{ADMIN}/usuarios",
        f"{ADMIN}/usuarios/{{id_usuario}}",
        f"{ADMIN}/contenido",
        f"{ADMIN}/contenido/{{id_contenido}}/publicar",
        f"{ADMIN}/contenido/{{id_contenido}}/rechazar",
        f"{ADMIN}/contenido/{{id_contenido}}/borrador",
        f"{ADMIN}/categorias",
        f"{ADMIN}/eventos",
        f"{ADMIN}/eventos/{{id_evento}}",
        f"{ADMIN}/foro/temas",
        f"{ADMIN}/foro/temas/{{id_tema}}",
        f"{ADMIN}/desafios",
        f"{ADMIN}/desafios/{{id_desafio}}/ganador",
        f"{ADMIN}/tiendas",
        f"{ADMIN}/grupos",
    ):
        assert ruta in rutas, ruta


def test_todos_los_endpoints_nacen_protegidos(cliente, usuario, admin):
    """La dependencia está en el router: ninguna ruta nueva puede quedar abierta."""
    _, token_normal = usuario
    _, token_admin = admin
    id_falso = "00000000-0000-0000-0000-000000000000"

    operaciones = [
        ("get", f"{ADMIN}/resumen", None),
        ("get", f"{ADMIN}/eventos", None),
        ("post", f"{ADMIN}/eventos", {"nombre": "X", "fecha_inicio": _fecha(1), "lugar": "Y"}),
        ("delete", f"{ADMIN}/eventos/{id_falso}", None),
        ("get", f"{ADMIN}/foro/temas", None),
        ("patch", f"{ADMIN}/foro/temas/{id_falso}", {"estado": "oculto"}),
        ("get", f"{ADMIN}/desafios", None),
        ("post", f"{ADMIN}/tiendas", {"nombre": "Tienda X"}),
        ("post", f"{ADMIN}/grupos", {"nombre": "Grupo X"}),
        ("patch", f"{ADMIN}/usuarios/{id_falso}", {"activo": False}),
    ]

    for metodo, ruta, cuerpo in operaciones:
        peticion = getattr(cliente, metodo)
        # httpx no acepta `json` en GET, así que solo se agrega cuando hay body.
        opciones = {"json": cuerpo} if cuerpo is not None else {}
        # Sin token: 401. Con usuario normal: 403. Con admin: nunca 401/403.
        assert peticion(ruta, **opciones).status_code == 401, (metodo, ruta)
        assert peticion(
            ruta, **opciones, headers=_cabecera(token_normal)
        ).status_code == 403, (metodo, ruta)
        respuesta_admin = peticion(
            ruta, **opciones, headers=_cabecera(token_admin)
        )
        assert respuesta_admin.status_code not in (401, 403), (
            metodo,
            ruta,
            respuesta_admin.text,
        )


def test_los_catalogos_del_panel_coinciden_con_los_modelos():
    """Si alguien agrega un valor al modelo y no al schema, el panel lo rechazaría."""

    def valores(modelo, campo):
        return set(get_args(modelo.model_fields[campo].annotation))

    assert valores(EstadoTemaEntrada, "estado") == set(ESTADOS_FORO)
    assert valores(TiendaEntrada, "tipo") == set(TIPOS_TIENDA)
    assert valores(GrupoEntrada, "plataforma") == set(PLATAFORMAS)


# --- Resumen -------------------------------------------------------------

def test_resumen_cuenta_lo_que_hay_en_la_base(cliente, admin, guia, evento):
    _, token = admin
    cliente.post(
        f"{ADMIN}/tiendas", json={"nombre": "Telas del Centro"}, headers=_cabecera(token)
    )

    respuesta = cliente.get(f"{ADMIN}/resumen", headers=_cabecera(token))

    assert respuesta.status_code == 200, respuesta.text
    cuerpo = respuesta.json()
    assert cuerpo["usuarios"] == 2  # el admin y el cosplayer
    assert cuerpo["usuarios_activos"] == 2
    assert cuerpo["contenido_pendiente"] == 1
    assert cuerpo["eventos"] == 1
    assert cuerpo["tiendas"] == 1
    assert cuerpo["temas"] == 0
    assert "generado_en" in cuerpo


# --- Bandeja editorial ---------------------------------------------------

def test_bandeja_ve_borradores_y_permite_publicar_rechazar_y_corregir(
    cliente, admin, guia
):
    _, token = admin
    cabecera = _cabecera(token)

    bandeja = cliente.get(f"{ADMIN}/contenido", headers=cabecera).json()
    assert bandeja["total"] == 1
    assert bandeja["elementos"][0]["estado"] == "pendiente"
    assert cliente.get(CONTENIDO).json()["total"] == 0  # el público no ve borradores

    publicado = cliente.post(
        f"{ADMIN}/contenido/{guia}/publicar", headers=cabecera
    ).json()
    assert publicado["estado"] == "publicado"
    assert publicado["fecha_publicacion"] is not None
    assert cliente.get(CONTENIDO).json()["total"] == 1

    # Un contenido ya publicado no se «rechaza»: primero vuelve a borrador.
    assert (
        cliente.post(f"{ADMIN}/contenido/{guia}/rechazar", headers=cabecera).status_code
        == 409
    )
    borrador = cliente.post(
        f"{ADMIN}/contenido/{guia}/borrador", headers=cabecera
    ).json()
    assert borrador["estado"] == "pendiente"
    assert borrador["fecha_publicacion"] is None

    rechazado = cliente.post(
        f"{ADMIN}/contenido/{guia}/rechazar", headers=cabecera
    ).json()
    assert rechazado["estado"] == "rechazado"


def test_transicion_a_contenido_inexistente_devuelve_404(cliente, admin):
    _, token = admin
    id_falso = "00000000-0000-0000-0000-000000000000"

    respuesta = cliente.post(
        f"{ADMIN}/contenido/{id_falso}/publicar", headers=_cabecera(token)
    )

    assert respuesta.status_code == 404


# --- Usuarios ------------------------------------------------------------

def test_admin_no_puede_desactivarse_a_si_mismo(cliente, admin):
    cuerpo_admin, token = admin
    id_admin = cliente.get("/api/v1/auth/me", headers=_cabecera(token)).json()["id_usuario"]

    respuesta = cliente.patch(
        f"{ADMIN}/usuarios/{id_admin}", json={"activo": False}, headers=_cabecera(token)
    )

    assert respuesta.status_code == 409
    assert "propia cuenta" in respuesta.json()["detail"]


def test_desactivar_un_usuario_le_quita_el_acceso(cliente, admin, usuario):
    cuerpo_usuario, token_usuario = usuario
    _, token_admin = admin
    id_usuario = cliente.get(
        "/api/v1/auth/me", headers=_cabecera(token_usuario)
    ).json()["id_usuario"]

    respuesta = cliente.patch(
        f"{ADMIN}/usuarios/{id_usuario}",
        json={"activo": False},
        headers=_cabecera(token_admin),
    )
    assert respuesta.status_code == 200, respuesta.text
    assert respuesta.json()["activo"] is False

    # El token sigue siendo válido criptográficamente, pero el usuario ya no.
    assert cliente.get("/api/v1/auth/me", headers=_cabecera(token_usuario)).status_code == 401
    intento = cliente.post(
        "/api/v1/auth/login",
        json={
            "correo": cuerpo_usuario["correo"],
            "password": cuerpo_usuario["password"],
        },
    )
    assert intento.status_code in (401, 403)

    reactivado = cliente.patch(
        f"{ADMIN}/usuarios/{id_usuario}",
        json={"activo": True},
        headers=_cabecera(token_admin),
    )
    assert reactivado.json()["activo"] is True


# --- Calendario ----------------------------------------------------------

def test_eliminar_evento_borra_tambien_las_inscripciones(cliente, admin, usuario, evento):
    _, token_admin = admin
    _, token_usuario = usuario

    inscripcion = cliente.post(
        f"{EVENTOS}/{evento}/participar",
        json={"personaje": "Sailor Moon"},
        headers=_cabecera(token_usuario),
    )
    assert inscripcion.status_code == 201

    antes = cliente.get(f"{ADMIN}/resumen", headers=_cabecera(token_admin)).json()
    assert antes["inscripciones"] == 1

    borrado = cliente.delete(f"{ADMIN}/eventos/{evento}", headers=_cabecera(token_admin))
    assert borrado.status_code == 204

    assert cliente.get(f"{EVENTOS}/{evento}").status_code == 404
    despues = cliente.get(f"{ADMIN}/resumen", headers=_cabecera(token_admin)).json()
    assert despues["eventos"] == 0
    assert despues["inscripciones"] == 0
    assert cliente.get(f"{EVENTOS}/mis", headers=_cabecera(token_usuario)).json()["total"] == 0


def test_eliminar_evento_inexistente_devuelve_404(cliente, admin):
    _, token = admin
    id_falso = "00000000-0000-0000-0000-000000000000"

    assert (
        cliente.delete(f"{ADMIN}/eventos/{id_falso}", headers=_cabecera(token)).status_code
        == 404
    )


# --- Moderación del foro -------------------------------------------------

def test_ocultar_un_tema_lo_saca_del_foro_publico_y_se_puede_reabrir(
    cliente, admin, usuario
):
    _, token_admin = admin
    _, token_usuario = usuario
    cabecera_admin = _cabecera(token_admin)

    creado = cliente.post(
        FORO,
        json={"titulo": "Consulta sobre goma eva", "categoria": "Armaduras y props", "contenido": "¿Qué densidad me recomiendan?"},
        headers=_cabecera(token_usuario),
    )
    assert creado.status_code == 201, creado.text
    id_tema = creado.json()["id_tema"]

    oculto = cliente.patch(
        f"{ADMIN}/foro/temas/{id_tema}", json={"estado": "oculto"}, headers=cabecera_admin
    )
    assert oculto.status_code == 200, oculto.text
    assert oculto.json()["estado"] == "oculto"

    assert cliente.get(FORO).json()["total"] == 0
    bandeja = cliente.get(
        f"{ADMIN}/foro/temas", params={"estado": "oculto"}, headers=cabecera_admin
    ).json()
    assert bandeja["total"] == 1
    assert bandeja["elementos"][0]["id_tema"] == id_tema

    reabierto = cliente.patch(
        f"{ADMIN}/foro/temas/{id_tema}", json={"estado": "abierto"}, headers=cabecera_admin
    )
    assert reabierto.json()["estado"] == "abierto"
    assert cliente.get(FORO).json()["total"] == 1


def test_estado_de_tema_fuera_de_catalogo_devuelve_422(cliente, admin):
    _, token = admin
    id_falso = "00000000-0000-0000-0000-000000000000"

    respuesta = cliente.patch(
        f"{ADMIN}/foro/temas/{id_falso}",
        json={"estado": "eliminado"},
        headers=_cabecera(token),
    )

    assert respuesta.status_code == 422


# --- Desafíos ------------------------------------------------------------

def test_crear_desafio_y_elegir_ganador_desde_el_panel(cliente, admin, usuario):
    _, token_admin = admin
    _, token_usuario = usuario
    cabecera = _cabecera(token_admin)
    id_usuario = cliente.get(
        "/api/v1/auth/me", headers=_cabecera(token_usuario)
    ).json()["id_usuario"]

    creado = cliente.post(
        f"{ADMIN}/desafios",
        json={"titulo": "Desafío de noviembre", "mes": "2026-11"},
        headers=cabecera,
    )
    assert creado.status_code == 201, creado.text

    duplicado = cliente.post(
        f"{ADMIN}/desafios",
        json={"titulo": "Otro", "mes": "2026-11"},
        headers=cabecera,
    )
    assert duplicado.status_code == 409

    id_desafio = creado.json()["id_desafio"]
    con_ganador = cliente.post(
        f"{ADMIN}/desafios/{id_desafio}/ganador",
        json={"id_usuario": id_usuario},
        headers=cabecera,
    )
    assert con_ganador.status_code == 200, con_ganador.text
    assert con_ganador.json()["id_ganador"] == id_usuario

    historial = cliente.get(f"{ADMIN}/desafios", headers=cabecera).json()
    assert historial["total"] == 1


# --- Tiendas y grupos ----------------------------------------------------

def test_alta_de_tienda_y_grupo_valida_duplicados_y_urls(cliente, admin):
    _, token = admin
    cabecera = _cabecera(token)

    tienda = cliente.post(
        f"{ADMIN}/tiendas",
        json={"nombre": "Telas Ñuñoa", "tipo": "telas", "enlace_web": "https://ejemplo.cl"},
        headers=cabecera,
    )
    assert tienda.status_code == 201, tienda.text
    assert tienda.json()["envia_a_chile"] is True

    assert (
        cliente.post(
            f"{ADMIN}/tiendas", json={"nombre": "Telas Ñuñoa"}, headers=cabecera
        ).status_code
        == 409
    )
    assert (
        cliente.post(
            f"{ADMIN}/tiendas",
            json={"nombre": "Enlace malo", "enlace_web": "javascript:alert(1)"},
            headers=cabecera,
        ).status_code
        == 422
    )

    grupo = cliente.post(
        f"{ADMIN}/grupos",
        json={"nombre": "Cosplay Valpo", "plataforma": "discord", "region": "Valparaíso"},
        headers=cabecera,
    )
    assert grupo.status_code == 201, grupo.text
    assert grupo.json()["plataforma"] == "discord"
    assert cliente.get("/api/v1/tiendas").json()["total"] == 1
    assert cliente.get("/api/v1/grupos").json()["total"] == 1


def test_crear_categoria_desde_el_panel(cliente, admin):
    _, token = admin
    cabecera = _cabecera(token)

    creada = cliente.post(
        f"{ADMIN}/categorias", json={"nombre": "Pelucas"}, headers=cabecera
    )
    assert creada.status_code == 201, creada.text
    assert cliente.get(f"{ADMIN}/categorias", headers=cabecera).json()[0]["nombre"] == "Pelucas"
    assert (
        cliente.post(
            f"{ADMIN}/categorias", json={"nombre": "Pelucas"}, headers=cabecera
        ).status_code
        == 409
    )
