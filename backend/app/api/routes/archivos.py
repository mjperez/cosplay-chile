"""Subida de imágenes a través del patrón Adapter (RF-18, RF-27, RF-08).

El endpoint habla con `IAlmacenamientoArchivos`, nunca con Cloudinary ni con
el disco. Cambiar de proveedor no modifica este archivo.
"""

from __future__ import annotations

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Request,
    Response,
    UploadFile,
    status,
)

from app.adapters.almacenamiento import (
    ArchivoNoEncontrado,
    IAlmacenamientoArchivos,
)
from app.api.deps import get_almacenamiento, get_usuario_actual
from app.models.usuario import Usuario
from app.schemas.archivo import ArchivoPublico
from app.services import archivos as servicio

router = APIRouter(prefix="/archivos", tags=["archivos"])


@router.post(
    "",
    response_model=ArchivoPublico,
    status_code=status.HTTP_201_CREATED,
    summary="Subir una imagen PNG, JPEG o WebP (máximo 5 MB)",
)
def subir_archivo(
    peticion: Request,
    archivo: UploadFile = File(..., description="Imagen a publicar"),
    usuario: Usuario = Depends(get_usuario_actual),
    almacenamiento: IAlmacenamientoArchivos = Depends(get_almacenamiento),
) -> ArchivoPublico:
    contenido = archivo.file.read()
    tipo_mime = (archivo.content_type or "").split(";")[0].strip().lower()
    try:
        resultado = servicio.guardar(
            almacenamiento, contenido, tipo_mime, usuario.id_usuario
        )
    except servicio.TipoNoPermitido as error:
        raise HTTPException(415, f"formato no admitido: {error.tipo_mime}")
    except servicio.ContenidoNoCoincide:
        raise HTTPException(415, "el contenido no corresponde a una imagen válida")
    except servicio.ArchivoVacio:
        raise HTTPException(400, "el archivo está vacío")
    except servicio.ArchivoDemasiadoGrande:
        raise HTTPException(413, "el archivo supera los 5 MB")

    # `ContenidoEntrada.imagenes` exige HttpUrl. El adaptador local devuelve
    # una ruta relativa, así que el endpoint la vuelve absoluta con el host de
    # la API (que en producción es distinto del host del frontend).
    if resultado.enlace.startswith("/"):
        return resultado.model_copy(
            update={"enlace": str(peticion.base_url).rstrip("/") + resultado.enlace}
        )
    return resultado


@router.delete(
    "/{identificador:path}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar una imagen propia (o cualquier imagen, si es administrador)",
)
def eliminar_archivo(
    identificador: str,
    usuario: Usuario = Depends(get_usuario_actual),
    almacenamiento: IAlmacenamientoArchivos = Depends(get_almacenamiento),
) -> Response:
    # El dueño va en el prefijo del identificador, generado por el servidor.
    # Sin esa comprobación cualquiera podría borrar la imagen de otro usuario.
    if (
        not identificador.startswith(f"{usuario.id_usuario}/")
        and usuario.rol != "administrador"
    ):
        raise HTTPException(403, "no puedes eliminar archivos de otra cuenta")
    try:
        servicio.eliminar(almacenamiento, identificador)
    except ArchivoNoEncontrado:
        raise HTTPException(404, "archivo no encontrado")
    except ValueError:
        raise HTTPException(400, "identificador no válido")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
