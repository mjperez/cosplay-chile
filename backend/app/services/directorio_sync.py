"""RF-10: si un prestador o tienda activa su perfil público, aparece en el directorio."""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.directorio import DirectorioItem, ProveedorServicio, Tienda
from app.models.enums import PERFIL_A_ESPECIALIDAD, TipoPerfil
from app.models.usuario import Usuario


def aparece_en_directorio(tipo: TipoPerfil) -> bool:
    return tipo in PERFIL_A_ESPECIALIDAD or tipo == TipoPerfil.TIENDA


async def sincronizar_ficha(db: AsyncSession, usuario: Usuario) -> DirectorioItem | None:
    """Crea, actualiza o desactiva la ficha del directorio vinculada al usuario."""
    perfil = usuario.perfil
    ficha = (
        await db.execute(select(DirectorioItem).where(DirectorioItem.usuario_id == usuario.id))
    ).scalar_one_or_none()

    debe_aparecer = bool(perfil and perfil.perfil_publico and aparece_en_directorio(perfil.tipo_perfil))
    if not debe_aparecer:
        if ficha is not None:
            ficha.activo = False
        return ficha

    clase = Tienda if perfil.tipo_perfil == TipoPerfil.TIENDA else ProveedorServicio
    if ficha is not None and not isinstance(ficha, clase):
        # Cambió de prestador a tienda o viceversa: se desactiva la ficha antigua
        ficha.activo = False
        ficha.usuario_id = None
        await db.flush()
        ficha = None

    if ficha is None:
        ficha = clase(
            nombre=usuario.nombre,
            descripcion=perfil.biografia or "",
            region=perfil.region,
            usuario_id=usuario.id,
            activo=True,
        )
        if clase is ProveedorServicio:
            ficha.especialidades = [PERFIL_A_ESPECIALIDAD[perfil.tipo_perfil].value]
            ficha.servicios = []
            ficha.portafolio = list(perfil.portafolio or [])
        else:
            ficha.tipos_producto = []
            ficha.envia_a_chile = True
        db.add(ficha)
    else:
        ficha.activo = True
        ficha.region = perfil.region or ficha.region
        if clase is ProveedorServicio:
            esp = PERFIL_A_ESPECIALIDAD[perfil.tipo_perfil].value
            actuales = list(ficha.especialidades or [])
            if esp not in actuales:
                ficha.especialidades = [esp, *actuales]
            if perfil.portafolio and not ficha.portafolio:
                ficha.portafolio = list(perfil.portafolio)
    return ficha
