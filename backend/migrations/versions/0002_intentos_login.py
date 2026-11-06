"""Registro de intentos de login para el bloqueo por fuerza bruta

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-05

El criterio de US-04a exige bloquear el login tras cinco intentos fallidos en
quince minutos. El contador no puede vivir en memoria: se pierde al reiniciar
y cada worker de uvicorn tendría el suyo. Esta tabla lo persiste.
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "intento_login",
        sa.Column("id_intento", sa.Uuid(), nullable=False),
        sa.Column("correo", sa.String(length=255), nullable=False),
        sa.Column("ip", sa.String(length=45), nullable=True),
        sa.Column("exitoso", sa.Boolean(), nullable=False),
        sa.Column("creado_en", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id_intento"),
    )
    op.create_index(
        "ix_intento_correo_fecha", "intento_login", ["correo", "creado_en"]
    )


def downgrade() -> None:
    op.drop_index("ix_intento_correo_fecha", table_name="intento_login")
    op.drop_table("intento_login")
