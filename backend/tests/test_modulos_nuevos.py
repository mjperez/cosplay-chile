"""Pruebas de los módulos que cerraron la plataforma: eventos, foro,
desafíos, perfiles y complementos del directorio.

Siguen las mismas reglas que el resto de la suite: base SQLite temporal con el
esquema real de Alembic, sin servicios externos y sin tocar la base de datos
de desarrollo.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import update

from app.core.database import get_session_manager
from app.models.usuario import Usuario

EVENTOS = "/api/v1/eventos"
FORO = "/api/v1/foro/temas"
DESAFIOS = "/api/v1/desafios"
PERFILES = "/api/v1/perfiles"
TIENDAS = "/api/v1/tiendas"
GRUPOS = "/api/v1/grupos"


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
    _, cuerpo = crear_usuario()
    return cuerpo, _login(cliente, cuerpo["correo"], cuerpo["password"])


@pytest.fixture
def admin(cliente, crear_usuario):
    _, cuerpo = crear_usuario(correo="admin@ejemplo.cl")
    _promover_a_admin(cuerpo["correo"])
    return cuerpo, _login(cliente, cuerpo["correo"], cuerpo["password"])


@pytest.fixture
def evento(cliente, admin) -> str:
    _, token = admin
    respuesta = cliente.post(
        EVENTOS,
        json={
            "nombre": "Convención Cosplay Santiago 2026",
            "tipo": "convencion",
            "fecha_inicio": _fecha(20),
            "fecha_fin": _fecha(21),
            "lugar": "Estación Mapocho",
            "region": "Metropolitana",
            "enlace_oficial": "https://ejemplo.cl/evento",
        },
        headers=_cabecera(token),
    )
    assert respuesta.status_code == 201, respuesta.text
    return respuesta.json()["id_evento"]


# --- Contrato HTTP -------------------------------------------------------

def test_las_rutas_nuevas_estan_en_openapi(cliente):
    rutas = cliente.get("/openapi.json").json()["paths"]

    for ruta in (
        EVENTOS,
        FORO,
        DESAFIOS,
        f"{PERFILES}/mio",
        f"{PERFILES}/{{id_usuario}}",
        TIENDAS,
        GRUPOS,
    ):
        assert ruta in rutas


# --- Eventos -------------------------------------------------------------

def test_listado_de_eventos_vacio(cliente):
    cuerpo = cliente.get(EVENTOS).json()

    assert cuerpo["total"] == 0
    assert cuerpo["elementos"] == []


def test_crear_evento_exige_administrador(cliente, usuario):
    _, token = usuario
    datos = {
        "nombre": "Taller de goma eva",
        "tipo": "taller",
        "fecha_inicio": _fecha(10),
        "lugar": "Valparaíso",
    }

    assert cliente.post(EVENTOS, json=datos).status_code == 401
    assert cliente.post(EVENTOS, json=datos, headers=_cabecera(token)).status_code == 403


def test_admin_crea_evento_y_el_listado_lo_muestra(cliente, admin):
    _, token = admin
    datos = {
        "nombre": "Concurso de Cosplay Invierno",
        "tipo": "concurso",
        "fecha_inicio": _fecha(30),
        "lugar": "Teatro Caupolicán",
        "region": "Metropolitana",
    }

    creado = cliente.post(EVENTOS, json=datos, headers=_cabecera(token))
    assert creado.status_code == 201, creado.text
    assert creado.json()["total_participantes"] == 0

    listado = cliente.get(EVENTOS).json()
    assert listado["total"] == 1
    assert listado["elementos"][0]["nombre"] == datos["nombre"]

    detalle = cliente.get(f"{EVENTOS}/{creado.json()['id_evento']}")
    assert detalle.status_code == 200
    assert detalle.json()["lugar"] == "Teatro Caupolicán"


def test_fecha_de_termino_anterior_al_inicio_se_rechaza(cliente, admin):
    _, token = admin
    respuesta = cliente.post(
        EVENTOS,
        json={
            "nombre": "Evento con fechas imposibles",
            "fecha_inicio": _fecha(30),
            "fecha_fin": _fecha(1),
            "lugar": "Santiago",
        },
        headers=_cabecera(token),
    )

    assert respuesta.status_code == 422


def test_filtros_de_eventos(cliente, admin):
    _, token = admin
    for nombre, tipo, region in (
        ("Feria Norte", "feria", "Antofagasta"),
        ("Taller Sur", "taller", "Valparaíso"),
    ):
        respuesta = cliente.post(
            EVENTOS,
            json={
                "nombre": nombre,
                "tipo": tipo,
                "region": region,
                "fecha_inicio": _fecha(15),
                "lugar": "Sede local",
            },
            headers=_cabecera(token),
        )
        assert respuesta.status_code == 201, respuesta.text

    assert cliente.get(EVENTOS, params={"tipo": "feria"}).json()["total"] == 1
    assert cliente.get(EVENTOS, params={"region": "valparaíso"}).json()["total"] == 1
    assert cliente.get(EVENTOS, params={"q": "Norte"}).json()["total"] == 1


def test_ciclo_completo_de_inscripcion(cliente, usuario, evento):
    cuerpo, token = usuario
    cabecera = _cabecera(token)

    inscripcion = cliente.post(
        f"{EVENTOS}/{evento}/participar",
        json={"personaje": "Sailor Moon"},
        headers=cabecera,
    )
    assert inscripcion.status_code == 201, inscripcion.text
    assert inscripcion.json()["nombre_usuario"] == cuerpo["nombre"]

    repetida = cliente.post(
        f"{EVENTOS}/{evento}/participar", json={}, headers=cabecera
    )
    assert repetida.status_code == 409

    participantes = cliente.get(f"{EVENTOS}/{evento}/participaciones").json()
    assert participantes["total"] == 1
    assert participantes["elementos"][0]["personaje"] == "Sailor Moon"

    assert cliente.get(f"{EVENTOS}/mis", headers=cabecera).json()["total"] == 1
    assert cliente.get(f"{EVENTOS}/{evento}").json()["total_participantes"] == 1

    cancelada = cliente.delete(f"{EVENTOS}/{evento}/participar", headers=cabecera)
    assert cancelada.status_code == 204
    assert cliente.get(f"{EVENTOS}/mis", headers=cabecera).json()["total"] == 0


def test_inscribirse_en_evento_inexistente_da_404(cliente, usuario):
    _, token = usuario
    import uuid

    respuesta = cliente.post(
        f"{EVENTOS}/{uuid.uuid4()}/participar", json={}, headers=_cabecera(token)
    )

    assert respuesta.status_code == 404


# --- Foro ----------------------------------------------------------------

def test_foro_es_publico_y_arranca_vacio(cliente):
    assert cliente.get(FORO).status_code == 200
    assert cliente.get(FORO).json()["total"] == 0


def test_crear_tema_responder_y_ver_detalle(cliente, usuario, crear_usuario):
    _, token = usuario
    _, otro = crear_usuario(correo="otro@ejemplo.cl")
    token_otro = _login(cliente, otro["correo"], otro["password"])

    creado = cliente.post(
        FORO,
        json={
            "titulo": "¿Qué sellador usan para la goma eva?",
            "categoria": "Armaduras y props",
            "contenido": "Estoy probando con cola fría pero se me levanta la pintura.",
        },
        headers=_cabecera(token),
    )
    assert creado.status_code == 201, creado.text
    id_tema = creado.json()["id_tema"]
    assert creado.json()["total_respuestas"] == 0

    respuesta = cliente.post(
        f"{FORO}/{id_tema}/respuestas",
        json={"contenido": "Prueba con imprimación acrílica, dos capas delgadas."},
        headers=_cabecera(token_otro),
    )
    assert respuesta.status_code == 201, respuesta.text
    assert respuesta.json()["nombre_autor"] == otro["nombre"]

    detalle = cliente.get(f"{FORO}/{id_tema}").json()
    assert detalle["total_respuestas"] == 1
    assert len(detalle["respuestas"]) == 1
    assert "imprimación" in detalle["respuestas"][0]["contenido"]


def test_crear_tema_sin_sesion_da_401(cliente):
    respuesta = cliente.post(
        FORO,
        json={"titulo": "Tema sin sesión", "categoria": "Costura", "contenido": "Hola"},
    )

    assert respuesta.status_code == 401


def test_tema_cerrado_no_admite_respuestas_y_solo_el_autor_lo_cierra(
    cliente, usuario, crear_usuario
):
    _, token = usuario
    _, otro = crear_usuario(correo="tercero@ejemplo.cl")
    token_otro = _login(cliente, otro["correo"], otro["password"])

    id_tema = cliente.post(
        FORO,
        json={
            "titulo": "Consulta cerrada",
            "categoria": "Costura",
            "contenido": "Consulta de prueba para el cierre del tema.",
        },
        headers=_cabecera(token),
    ).json()["id_tema"]

    ajeno = cliente.post(
        f"{FORO}/{id_tema}/cerrar", headers=_cabecera(token_otro)
    )
    assert ajeno.status_code == 403

    cerrado = cliente.post(f"{FORO}/{id_tema}/cerrar", headers=_cabecera(token))
    assert cerrado.status_code == 200
    assert cerrado.json()["estado"] == "cerrado"

    respuesta = cliente.post(
        f"{FORO}/{id_tema}/respuestas",
        json={"contenido": "Tarde pero aquí voy"},
        headers=_cabecera(token_otro),
    )
    assert respuesta.status_code == 409


def test_filtros_del_foro(cliente, usuario):
    _, token = usuario
    for titulo, categoria in (
        ("Duda de peluca", "Pelucas y maquillaje"),
        ("Presupuesto de armadura", "Presupuesto y compras"),
    ):
        assert cliente.post(
            FORO,
            json={"titulo": titulo, "categoria": categoria, "contenido": "Consulta de prueba"},
            headers=_cabecera(token),
        ).status_code == 201

    assert cliente.get(FORO, params={"categoria": "Pelucas y maquillaje"}).json()["total"] == 1
    assert cliente.get(FORO, params={"q": "armadura"}).json()["total"] == 1


# --- Desafíos ------------------------------------------------------------

def test_desafio_vigente_y_historial(cliente, admin, usuario):
    _, token_admin = admin
    cuerpo_usuario, _ = usuario
    mes = datetime.now(timezone.utc).strftime("%Y-%m")

    assert cliente.get(f"{DESAFIOS}/vigente").json() is None

    creado = cliente.post(
        DESAFIOS,
        json={"titulo": "Desafío de noviembre: personaje de anime clásico", "mes": mes},
        headers=_cabecera(token_admin),
    )
    assert creado.status_code == 201, creado.text
    id_desafio = creado.json()["id_desafio"]

    duplicado = cliente.post(
        DESAFIOS,
        json={"titulo": "Otro desafío del mismo mes", "mes": mes},
        headers=_cabecera(token_admin),
    )
    assert duplicado.status_code == 409

    vigente = cliente.get(f"{DESAFIOS}/vigente").json()
    assert vigente["id_desafio"] == id_desafio
    assert cliente.get(DESAFIOS).json()["total"] == 1

    id_usuario = cliente.get("/api/v1/auth/me", headers=_cabecera(_login(
        cliente, cuerpo_usuario["correo"], cuerpo_usuario["password"]
    ))).json()["id_usuario"]

    ganador = cliente.post(
        f"{DESAFIOS}/{id_desafio}/ganador",
        json={"id_usuario": id_usuario},
        headers=_cabecera(token_admin),
    )
    assert ganador.status_code == 200, ganador.text
    assert ganador.json()["nombre_ganador"] == cuerpo_usuario["nombre"]


def test_crear_desafio_exige_admin(cliente, usuario, admin):
    _, token = usuario
    _, token_admin = admin
    mes = datetime.now(timezone.utc).strftime("%Y-%m")

    assert cliente.post(DESAFIOS, json={"titulo": "Desafío", "mes": mes}).status_code == 401
    assert cliente.post(
        DESAFIOS, json={"titulo": "Desafío", "mes": mes}, headers=_cabecera(token)
    ).status_code == 403
    # La validación del cuerpo se comprueba con un token válido: la dependencia
    # de rol se evalúa antes y un 403 no diría nada sobre el formato del mes.
    assert cliente.post(
        DESAFIOS, json={"titulo": "Desafío", "mes": "mal-formato"}, headers=_cabecera(token_admin)
    ).status_code == 422


def test_ganador_inexistente_da_404(cliente, admin):
    import uuid

    _, token_admin = admin
    mes = datetime.now(timezone.utc).strftime("%Y-%m")
    id_desafio = cliente.post(
        DESAFIOS, json={"titulo": "Desafío", "mes": mes}, headers=_cabecera(token_admin)
    ).json()["id_desafio"]

    respuesta = cliente.post(
        f"{DESAFIOS}/{id_desafio}/ganador",
        json={"id_usuario": str(uuid.uuid4())},
        headers=_cabecera(token_admin),
    )
    assert respuesta.status_code == 404


# --- Perfiles ------------------------------------------------------------

def test_perfil_se_actualiza_y_se_ve_sin_sesion(cliente, usuario):
    cuerpo, token = usuario
    cabecera = _cabecera(token)

    assert cliente.get(f"{PERFILES}/mio").status_code == 401

    actualizado = cliente.put(
        f"{PERFILES}/mio",
        json={
            "especialidad": "Armaduras y props",
            "portafolio_url": "https://ejemplo.cl/portafolio",
            "biografia": "Cosplayer desde 2019, especializada en goma eva.",
            "region": "Biobío",
        },
        headers=cabecera,
    )
    assert actualizado.status_code == 200, actualizado.text
    assert actualizado.json()["region"] == "Biobío"

    id_usuario = cliente.get("/api/v1/auth/me", headers=cabecera).json()["id_usuario"]
    publico = cliente.get(f"{PERFILES}/{id_usuario}")
    assert publico.status_code == 200
    assert publico.json()["especialidad"] == "Armaduras y props"
    assert "correo" not in publico.json()

    # Segunda escritura: actualiza, no duplica.
    assert cliente.put(
        f"{PERFILES}/mio", json={"biografia": "Texto corregido"}, headers=cabecera
    ).status_code == 200
    assert cliente.get(f"{PERFILES}/{id_usuario}").json()["biografia"] == "Texto corregido"


# --- Complementos del directorio ----------------------------------------

def test_tiendas_y_grupos_estan_disponibles_y_vacios(cliente):
    tiendas = cliente.get(TIENDAS)
    grupos = cliente.get(GRUPOS)

    assert tiendas.status_code == 200
    assert grupos.status_code == 200
    assert tiendas.json() == {"total": 0, "elementos": []}
    assert grupos.json() == {"total": 0, "elementos": []}
