"""Pruebas del patrón Observer comprometido en el informe ES2.

No basta con que exista una clase `GestorEventos`: el informe dice que al
enviar un tutorial o publicar un evento se notifica al usuario, se avisa a
moderación y se escribe en la bitácora, en segundo plano y sin acoplar el
controlador. Estas pruebas verifican ese efecto observable extremo a extremo.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import func, select, update

from app.core.database import get_session_manager
from app.events.gestor import EventoDominio, Observador, gestor_eventos
from app.models.notificacion import BitacoraAuditoria
from app.models.usuario import Usuario

CONTENIDO = "/api/v1/contenido"
ADMIN = "/api/v1/admin"
NOTIFICACIONES = "/api/v1/notificaciones"

GUIA = {
    "tipo": "guia",
    "titulo": "Cómo moldear goma eva sin burbujas",
    "resumen": "Técnica de termoformado con calor controlado",
    "nivel": "basico",
    "cuerpo": "<p>Se calienta de forma pareja.</p>",
    "pasos": ["Calentar", "Moldear", "Enfriar"],
    "materiales": ["goma eva 5 mm"],
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


def _tipos(cliente, token: str) -> list[str]:
    respuesta = cliente.get(NOTIFICACIONES, headers=_cabecera(token))
    assert respuesta.status_code == 200, respuesta.text
    return [fila["tipo"] for fila in respuesta.json()["elementos"]]


@pytest.fixture
def actores(cliente, crear_usuario):
    """Un cosplayer autor y un administrador, ambos con token válido."""
    _, autor = crear_usuario(correo="autor.observer@ejemplo.cl")
    _, admin = crear_usuario(correo="admin.observer@ejemplo.cl")
    _promover_a_admin(admin["correo"])
    return (
        _login(cliente, autor["correo"], autor["password"]),
        _login(cliente, admin["correo"], admin["password"]),
    )


def test_el_gestor_registra_los_tres_observadores_del_informe(cliente):
    nombres = {type(o).__name__ for o in gestor_eventos.observadores()}
    assert nombres == {
        "NotificacionInternaObserver",
        "CorreoModeradorObserver",
        "RegistroAuditoriaObserver",
    }


def test_configurar_observadores_es_idempotente(cliente):
    from app.events.gestor import configurar_observadores

    configurar_observadores()
    configurar_observadores()
    assert len(gestor_eventos.observadores()) == 3


def test_enviar_un_tutorial_dispara_los_tres_observadores(cliente, actores):
    token_autor, token_admin = actores
    respuesta = cliente.post(CONTENIDO, json=GUIA, headers=_cabecera(token_autor))
    assert respuesta.status_code == 201, respuesta.text

    # 1. NotificacionInternaObserver: el autor recibe confirmación...
    assert "contenido_enviado_revision" in _tipos(cliente, token_autor)
    # ...y moderación recibe la tarea pendiente.
    assert "contenido_enviado_revision" in _tipos(cliente, token_admin)

    # 2. CorreoModeradorObserver deja la bandeja de salida.
    # 3. RegistroAuditoriaObserver escribe el evento de dominio.
    with get_session_manager().session() as sesion:
        categorias = list(sesion.scalars(select(BitacoraAuditoria.categoria)).all())
    assert "correo_moderacion" in categorias
    assert "evento_dominio" in categorias


def test_la_bitacora_registra_actor_recurso_y_detalle(cliente, actores):
    token_autor, _ = actores
    id_contenido = cliente.post(
        CONTENIDO, json=GUIA, headers=_cabecera(token_autor)
    ).json()["id_contenido"]

    with get_session_manager().session() as sesion:
        fila = sesion.scalar(
            select(BitacoraAuditoria).where(
                BitacoraAuditoria.categoria == "evento_dominio"
            )
        )
        assert fila is not None
        assert fila.tipo_evento == "contenido_enviado_revision"
        assert str(fila.id_recurso) == id_contenido
        assert fila.detalle["titulo"] == GUIA["titulo"]
        assert fila.correo_actor.endswith("@ejemplo.cl")


def test_publicar_un_contenido_avisa_al_autor(cliente, actores):
    token_autor, token_admin = actores
    id_contenido = cliente.post(
        CONTENIDO, json=GUIA, headers=_cabecera(token_autor)
    ).json()["id_contenido"]

    respuesta = cliente.post(
        f"{CONTENIDO}/{id_contenido}/publicar", headers=_cabecera(token_admin)
    )
    assert respuesta.status_code == 200, respuesta.text
    assert "contenido_publicado" in _tipos(cliente, token_autor)


def test_crear_evento_avisa_a_la_comunidad_pero_no_al_actor(cliente, actores):
    token_autor, token_admin = actores
    respuesta = cliente.post(
        f"{ADMIN}/eventos",
        json={
            "nombre": "Convención Cosplay 2027",
            "tipo": "convencion",
            "fecha_inicio": _fecha(30),
            "lugar": "Santiago",
            "region": "Metropolitana",
        },
        headers=_cabecera(token_admin),
    )
    assert respuesta.status_code == 201, respuesta.text
    assert "evento_creado" in _tipos(cliente, token_autor)
    assert "evento_creado" not in _tipos(cliente, token_admin)


def test_crear_desafio_dispara_notificacion_y_bitacora(cliente, actores):
    token_autor, token_admin = actores
    respuesta = cliente.post(
        f"{ADMIN}/desafios",
        json={"titulo": "Desafío de armaduras", "mes": "2027-05"},
        headers=_cabecera(token_admin),
    )
    assert respuesta.status_code == 201, respuesta.text
    assert "desafio_creado" in _tipos(cliente, token_autor)

    with get_session_manager().session() as sesion:
        tipos = list(sesion.scalars(select(BitacoraAuditoria.tipo_evento)).all())
    assert "desafio_creado" in tipos


def test_marcar_como_leida_no_permite_avisos_ajenos(cliente, crear_usuario):
    _, autor = crear_usuario(correo="autor.lectura@ejemplo.cl")
    _, otro = crear_usuario(correo="otro.lectura@ejemplo.cl")
    token_autor = _login(cliente, autor["correo"], autor["password"])
    token_otro = _login(cliente, otro["correo"], otro["password"])

    cliente.post(CONTENIDO, json=GUIA, headers=_cabecera(token_autor))
    respuesta = cliente.get(NOTIFICACIONES, headers=_cabecera(token_autor))
    id_notificacion = respuesta.json()["elementos"][0]["id_notificacion"]
    assert respuesta.json()["sin_leer"] == 1

    ajeno = cliente.patch(
        f"{NOTIFICACIONES}/{id_notificacion}/leer", headers=_cabecera(token_otro)
    )
    assert ajeno.status_code == 404

    propia = cliente.patch(
        f"{NOTIFICACIONES}/{id_notificacion}/leer", headers=_cabecera(token_autor)
    )
    assert propia.status_code == 200
    assert propia.json()["leida"] is True
    assert cliente.get(NOTIFICACIONES, headers=_cabecera(token_autor)).json()["sin_leer"] == 0


def test_los_endpoints_de_notificaciones_exigen_sesion(cliente):
    assert cliente.get(NOTIFICACIONES).status_code == 401
    assert cliente.get(f"{NOTIFICACIONES}/sin-leer").status_code == 401


def test_la_bitacora_solo_la_lee_un_administrador(cliente, actores):
    token_autor, token_admin = actores
    cliente.post(CONTENIDO, json=GUIA, headers=_cabecera(token_autor))

    assert cliente.get(f"{ADMIN}/auditoria").status_code == 401
    assert cliente.get(f"{ADMIN}/auditoria", headers=_cabecera(token_autor)).status_code == 403
    permitido = cliente.get(f"{ADMIN}/auditoria", headers=_cabecera(token_admin))
    assert permitido.status_code == 200
    assert permitido.json()["total"] >= 2


def test_la_bitacora_no_tiene_clave_foranea_hacia_usuario():
    """Un log de auditoría debe sobrevivir a la baja de la cuenta."""
    assert BitacoraAuditoria.__table__.foreign_keys == set()


def test_un_observador_caido_no_impide_a_los_demas(cliente):
    class ObservadorRoto(Observador):
        def actualizar(self, evento: EventoDominio) -> None:
            raise RuntimeError("canal de aviso caído")

    roto = ObservadorRoto()
    gestor_eventos.suscribir(roto)
    try:
        gestor_eventos.notificar(
            EventoDominio(tipo="evento_creado", detalle={"titulo": "Evento de prueba"})
        )
        with get_session_manager().session() as sesion:
            total = sesion.scalar(
                select(func.count()).select_from(BitacoraAuditoria)
            )
        assert total >= 1
    finally:
        gestor_eventos.desuscribir(roto)


def test_un_tipo_de_evento_fuera_del_catalogo_se_rechaza():
    with pytest.raises(ValueError, match="no registrado"):
        EventoDominio(tipo="inventado_por_ahí")
