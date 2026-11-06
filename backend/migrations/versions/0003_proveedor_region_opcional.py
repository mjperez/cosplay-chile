"""Region opcional y tipo organizador en proveedor

Revision ID: 0003
Revises: 0002
Create Date: 2026-11-05

Dos cambios que salen de los datos reales de la toma de requerimientos:

1. `region` pasa a ser opcional. De las cuentas identificadas en el
   levantamiento, solo una parte declara su región en el perfil público.
   Inventarla para completar el campo sería falsear el dato, y el directorio
   tiene que poder mostrar «región no declarada».
2. `tipo` admite `organizador`. El enum original no lo contemplaba y hay
   productoras de eventos con actividad comercial en el directorio.

Ninguno de los dos cambia filas existentes: la tabla está vacía al aplicar
esta migración.
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TIPOS_ANTERIORES = ("cosmaker", "sastre", "fotografo", "tienda", "otro")
TIPOS_NUEVOS = ("cosmaker", "sastre", "fotografo", "tienda", "organizador", "otro")


def upgrade() -> None:
    with op.batch_alter_table("proveedor") as lote:
        lote.alter_column(
            "region",
            existing_type=sa.String(length=80),
            nullable=True,
        )
        lote.alter_column(
            "tipo",
            existing_type=sa.String(length=9),
            type_=sa.String(length=12),
            existing_nullable=False,
        )


def downgrade() -> None:
    # Antes de volver a exigir region hay que darle un valor a las filas que
    # quedaron nulas. Se usa una cadena explícita, no una región inventada.
    op.execute("UPDATE proveedor SET region = 'sin determinar' WHERE region IS NULL")
    with op.batch_alter_table("proveedor") as lote:
        lote.alter_column(
            "region",
            existing_type=sa.String(length=80),
            nullable=False,
        )
        lote.alter_column(
            "tipo",
            existing_type=sa.String(length=12),
            type_=sa.String(length=9),
            existing_nullable=False,
        )
