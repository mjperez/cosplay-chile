from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()


class Proveedor(BaseModel):
    nombre: str
    especialidad: str
    region: str
    anios_experiencia: int = 0
    contacto: str | None = None


@app.get("/")
def raiz():
    return {"mensaje": "funciona"}


@app.post("/proveedores")
def crear_proveedor(proveedor: Proveedor):
    return {"recibido": proveedor, "campos": len(proveedor.model_dump())}
