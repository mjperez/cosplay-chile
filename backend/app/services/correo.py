"""Envío de correo SIMULADO: en el prototipo se escribe en el log del backend.

En producción se reemplazaría por un adaptador hacia una API de correo (Adapter).
"""
import logging

logger = logging.getLogger("cosplaychile.correo")

# Últimos correos "enviados" (útil para pruebas y para la demo)
BANDEJA_SIMULADA: list[dict] = []


def enviar_correo_simulado(para: str, asunto: str, cuerpo: str) -> None:
    BANDEJA_SIMULADA.append({"para": para, "asunto": asunto, "cuerpo": cuerpo})
    del BANDEJA_SIMULADA[:-50]
    logger.warning("[CORREO SIMULADO] Para: %s | Asunto: %s\n%s", para, asunto, cuerpo)
