"""UC-01 Identificarse (Tabla 5, Fig. 12) y gestión de cuenta."""
import pytest
from sqlalchemy import select

from app.core.security import decodificar_token, verificar_password
from app.models import DirectorioItem, RegistroAuditoria, Usuario
from app.models.enums import EstadoUsuario
from app.services.correo import BANDEJA_SIMULADA
from tests.conftest import PASSWORD, crear_usuario, token_de

REGISTRO = {
    "nombre": "Antonia Mapu",
    "email": "Antonia@Ejemplo.cl",
    "password": "MiClave2026",
    "tipo_perfil": "COSPLAYER",
    "region": "AR",
    "acepta_privacidad": True,
}


async def test_registro_inicia_sesion_y_guarda_hash(client, db):
    r = await client.post("/api/auth/registro", json=REGISTRO)
    assert r.status_code == 201, r.text
    cuerpo = r.json()
    # Flujo 3a: tras registrarse queda con sesión (token JWT)
    assert decodificar_token(cuerpo["access_token"])["sub"] == cuerpo["usuario"]["id"]
    assert cuerpo["usuario"]["email"] == "antonia@ejemplo.cl"
    assert cuerpo["usuario"]["perfil"]["perfil_publico"] is False  # opt-in desactivado por defecto

    usuario = (await db.execute(select(Usuario).where(Usuario.email == "antonia@ejemplo.cl"))).scalar_one()
    assert usuario.password_hash != REGISTRO["password"]
    assert usuario.password_hash.startswith("$argon2")  # RNF-07
    assert verificar_password(REGISTRO["password"], usuario.password_hash)
    assert usuario.consentimiento_at is not None  # RNF-11

    # El Observer de auditoría registró el evento en segundo plano
    eventos = (await db.execute(select(RegistroAuditoria.evento))).scalars().all()
    assert "USUARIO_REGISTRADO" in eventos


async def test_registro_exige_consentimiento(client):
    r = await client.post("/api/auth/registro", json={**REGISTRO, "acepta_privacidad": False})
    assert r.status_code == 422
    assert "privacidad" in r.text


@pytest.mark.parametrize("clave", ["corta1", "soloLetrasLargas", "1234567890"])
async def test_registro_rechaza_contrasenas_debiles(client, clave):
    r = await client.post("/api/auth/registro", json={**REGISTRO, "password": clave})
    assert r.status_code == 422


async def test_registro_correo_duplicado(client):
    assert (await client.post("/api/auth/registro", json=REGISTRO)).status_code == 201
    r = await client.post("/api/auth/registro", json={**REGISTRO, "email": "antonia@ejemplo.cl"})
    assert r.status_code == 409


async def test_login_exitoso_devuelve_token_y_perfil(client, usuario):
    r = await client.post("/api/auth/login", json={"email": "CAMILA@test.cl", "password": PASSWORD})
    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo["token_type"] == "bearer"
    assert cuerpo["usuario"]["perfil"]["tipo_perfil"] == "COSPLAYER"
    me = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {cuerpo['access_token']}"})
    assert me.json()["email"] == "camila@test.cl"


@pytest.mark.parametrize(
    "email,password",
    [("camila@test.cl", "ClaveIncorrecta1"), ("noexiste@test.cl", PASSWORD), ("noexiste@test.cl", "x")],
)
async def test_login_fallido_es_401_generico(client, usuario, email, password):
    """Excepción 1: mismo 401 'Datos incorrectos' sin indicar qué campo falló."""
    r = await client.post("/api/auth/login", json={"email": email, "password": password})
    assert r.status_code == 401
    assert r.json() == {"detail": "Datos incorrectos"}


async def test_login_cuenta_suspendida_ofrece_contacto(client, db):
    await crear_usuario(db, "suspendida@test.cl", estado=EstadoUsuario.SUSPENDIDO)
    r = await client.post("/api/auth/login", json={"email": "suspendida@test.cl", "password": PASSWORD})
    assert r.status_code == 403
    detalle = r.json()["detail"]
    assert detalle["codigo"] == "CUENTA_SUSPENDIDA"
    assert "formulario de contacto" in detalle["mensaje"]


async def test_cuenta_suspendida_con_clave_incorrecta_no_revela_estado(client, db):
    await crear_usuario(db, "suspendida@test.cl", estado=EstadoUsuario.SUSPENDIDO)
    r = await client.post("/api/auth/login", json={"email": "suspendida@test.cl", "password": "Otra2026clave"})
    assert r.status_code == 401


async def test_rutas_protegidas_exigen_token(client):
    assert (await client.get("/api/auth/me")).status_code == 401
    r = await client.get("/api/auth/me", headers={"Authorization": "Bearer token-falso"})
    assert r.status_code == 401
    assert "sesión" in r.json()["detail"]


async def test_usuario_suspendido_pierde_acceso_con_token_vigente(client, db, usuario, auth_usuario):
    usuario.estado = EstadoUsuario.SUSPENDIDO
    await db.commit()
    r = await client.get("/api/auth/me", headers=auth_usuario)
    assert r.status_code == 403


async def test_recuperar_y_restablecer_contrasena(client, usuario):
    BANDEJA_SIMULADA.clear()
    r = await client.post("/api/auth/recuperar", json={"email": "camila@test.cl"})
    assert r.status_code == 202
    assert len(BANDEJA_SIMULADA) == 1
    enlace = BANDEJA_SIMULADA[0]["cuerpo"].split("restablecer?token=")[1].split()[0]

    r = await client.post("/api/auth/restablecer", json={"token": enlace, "password": "NuevaClave99"})
    assert r.status_code == 200
    assert (await client.post("/api/auth/login",
                              json={"email": "camila@test.cl", "password": "NuevaClave99"})).status_code == 200
    # El token es de un solo uso
    r = await client.post("/api/auth/restablecer", json={"token": enlace, "password": "OtraClave99"})
    assert r.status_code == 400


async def test_recuperar_no_revela_si_el_correo_existe(client, usuario):
    BANDEJA_SIMULADA.clear()
    existe = await client.post("/api/auth/recuperar", json={"email": "camila@test.cl"})
    no_existe = await client.post("/api/auth/recuperar", json={"email": "nadie@test.cl"})
    assert existe.status_code == no_existe.status_code == 202
    assert existe.json() == no_existe.json()
    assert len(BANDEJA_SIMULADA) == 1


async def test_perfil_publico_opt_in_crea_ficha_en_directorio(client, db):
    """RF-10: un prestador que activa su perfil público aparece en el directorio."""
    datos = {**REGISTRO, "email": "sastre@test.cl", "tipo_perfil": "SASTRE", "perfil_publico": True}
    r = await client.post("/api/auth/registro", json=datos)
    assert r.status_code == 201
    ficha = (await db.execute(select(DirectorioItem))).scalar_one()
    assert ficha.activo and ficha.especialidades == ["SASTRERIA"] and ficha.region.value == "AR"

    headers = {"Authorization": f"Bearer {r.json()['access_token']}"}
    r = await client.put("/api/perfil", json={"perfil_publico": False}, headers=headers)
    assert r.status_code == 200
    await db.refresh(ficha)
    assert ficha.activo is False


async def test_actualizar_perfil_valida_enlaces(client, auth_usuario):
    r = await client.put("/api/perfil", headers=auth_usuario, json={
        "biografia": "Hago cosplay adaptado a mi silla de ruedas.",
        "redes_sociales": [{"red": "Instagram", "url": "javascript:alert(1)"}],
    })
    assert r.status_code == 422
    r = await client.put("/api/perfil", headers=auth_usuario, json={
        "biografia": "Hago cosplay adaptado a mi silla de ruedas.",
        "redes_sociales": [{"red": "Instagram", "url": "https://instagram.com/camila"}],
        "portafolio": [{"url": "/media/subidas/foto.png", "alt": "Camila como guerrera con armadura de EVA"}],
    })
    assert r.status_code == 200
    assert r.json()["perfil"]["redes_sociales"][0]["red"] == "Instagram"


async def test_eliminar_cuenta_anonimiza(client, db, usuario, auth_usuario):
    r = await client.delete("/api/perfil", headers=auth_usuario)
    assert r.status_code == 200
    await db.refresh(usuario)
    assert usuario.estado == EstadoUsuario.ELIMINADO
    assert usuario.nombre == "Usuario eliminado"
    assert "camila" not in usuario.email
    r = await client.post("/api/auth/login", json={"email": "camila@test.cl", "password": PASSWORD})
    assert r.status_code == 401


async def test_token_de_admin_incluye_rol(client, admin):
    headers = await token_de(client, admin.email)
    token = headers["Authorization"].split()[1]
    assert decodificar_token(token)["rol"] == "ADMIN"
