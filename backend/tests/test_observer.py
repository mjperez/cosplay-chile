"""Patrón Observer: GestorEventos y sus observers concretos."""
import asyncio

from fastapi import BackgroundTasks
from sqlalchemy import select

from app.models import Notificacion, RegistroAuditoria
from app.patterns.observer import (
    CorreoModeradorObserver,
    EventoDominio,
    Eventos,
    GestorEventos,
    NotificacionInternaObserver,
    Observer,
    RegistroAuditoriaObserver,
    crear_gestor_eventos,
)
from app.services.correo import BANDEJA_SIMULADA
from tests.conftest import crear_usuario


class Espia(Observer):
    def __init__(self, demora=0.0):
        self.recibidos: list[EventoDominio] = []
        self.demora = demora

    async def actualizar(self, evento):
        await asyncio.sleep(self.demora)
        self.recibidos.append(evento)


class Roto(Observer):
    async def actualizar(self, evento):
        raise RuntimeError("falla simulada")


async def test_suscribir_notificar_y_desuscribir():
    gestor, a, b = GestorEventos(), Espia(), Espia()
    gestor.suscribir(a)
    gestor.suscribir(b)
    gestor.suscribir(a)  # no se duplica
    await gestor.notificar("PRUEBA", {"x": 1})
    assert [e.nombre for e in a.recibidos] == ["PRUEBA"]
    assert b.recibidos[0].datos == {"x": 1}
    gestor.desuscribir(a)
    await gestor.notificar("OTRO", {})
    assert len(a.recibidos) == 1 and len(b.recibidos) == 2


async def test_un_observer_que_falla_no_afecta_a_los_demas():
    gestor, sano = GestorEventos(), Espia()
    gestor.suscribir(Roto())
    gestor.suscribir(sano)
    await gestor.notificar("PRUEBA", {})  # no lanza excepción
    assert len(sano.recibidos) == 1


async def test_los_observers_corren_en_paralelo():
    """Fork/Join de la Fig. 15: el tiempo total es el del más lento, no la suma."""
    gestor = GestorEventos()
    for _ in range(3):
        gestor.suscribir(Espia(demora=0.2))
    t0 = asyncio.get_running_loop().time()
    await gestor.notificar("PRUEBA", {})
    assert asyncio.get_running_loop().time() - t0 < 0.5


async def test_notificar_en_segundo_plano_usa_background_tasks():
    gestor, espia = GestorEventos(), Espia()
    gestor.suscribir(espia)
    tareas = BackgroundTasks()
    gestor.notificar_en_segundo_plano(tareas, "PRUEBA", {"a": 1})
    assert espia.recibidos == []  # aún no corre: se ejecuta después de la respuesta
    await tareas()
    assert espia.recibidos[0].nombre == "PRUEBA"


def test_gestor_por_defecto_tiene_los_tres_observers_del_informe():
    tipos = {type(o) for o in crear_gestor_eventos().observers}
    assert tipos == {NotificacionInternaObserver, CorreoModeradorObserver, RegistroAuditoriaObserver}


async def test_observers_concretos_notifican_auditan_y_envian_correo(db, usuario, admin):
    BANDEJA_SIMULADA.clear()
    await crear_gestor_eventos().notificar(
        Eventos.NUEVO_TUTORIAL, {"contenido_id": "c1", "titulo": "Peluca", "autor_id": usuario.id}, actor_id=usuario.id
    )
    notifs = (await db.execute(select(Notificacion))).scalars().all()
    por_usuario = {n.usuario_id: n.mensaje for n in notifs}
    assert "en revisión" in por_usuario[usuario.id]
    assert "pendiente" in por_usuario[admin.id]
    auditoria = (await db.execute(select(RegistroAuditoria))).scalar_one()
    assert auditoria.evento == "NUEVO_TUTORIAL" and auditoria.actor_id == usuario.id
    assert BANDEJA_SIMULADA[-1]["asunto"].endswith("Nuevo tutorial pendiente de revisión")


async def test_publicacion_notifica_a_toda_la_comunidad_activa(db, usuario, admin):
    from app.models.enums import EstadoUsuario
    otra = await crear_usuario(db, "otra@test.cl")
    suspendida = await crear_usuario(db, "susp@test.cl", estado=EstadoUsuario.SUSPENDIDO)
    await NotificacionInternaObserver().actualizar(EventoDominio(
        Eventos.EVENTO_PUBLICADO, {"evento_id": "e1", "nombre": "Meetup", "autor_id": None}))
    destinatarios = set((await db.execute(select(Notificacion.usuario_id))).scalars().all())
    assert destinatarios == {usuario.id, admin.id, otra.id}
    assert suspendida.id not in destinatarios
