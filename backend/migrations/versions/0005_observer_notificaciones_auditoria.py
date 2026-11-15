"""Notificaciones y bitácora de auditoría para el patrón Observer.

Revision ID: 0005
Revises: 0004
Create Date: 2026-11-15

Migración puramente aditiva: crea dos tablas nuevas y no modifica ninguna
existente. Por eso la versión anterior del código puede seguir leyendo la base
aunque estas tablas estén presentes, lo que mantiene viable el rollback
documentado en GUIA_DEMO.md.
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "notificacion",
        sa.Column("id_notificacion", sa.Uuid(), nullable=False),
        sa.Column("id_usuario", sa.Uuid(), nullable=False),
        sa.Column("tipo", sa.String(length=40), nullable=False),
        sa.Column("titulo", sa.String(length=160), nullable=False),
        sa.Column("mensaje", sa.Text(), nullable=False),
        sa.Column("id_recurso", sa.Uuid(), nullable=True),
        sa.Column("leida", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column(
            "creado_en",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["id_usuario"], ["usuario.id_usuario"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id_notificacion"),
    )
    op.create_index(
        op.f("ix_notificacion_id_usuario"), "notificacion", ["id_usuario"], unique=False
    )

    op.create_table(
        "bitacora_auditoria",
        sa.Column("id_registro", sa.Uuid(), nullable=False),
        sa.Column(
            "ocurrido_en",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("categoria", sa.String(length=40), nullable=False),
        sa.Column("tipo_evento", sa.String(length=60), nullable=False),
        sa.Column("id_actor", sa.Uuid(), nullable=True),
        sa.Column("correo_actor", sa.String(length=255), nullable=True),
        sa.Column("id_recurso", sa.Uuid(), nullable=True),
        sa.Column("detalle", sa.JSON(), nullable=True),
        sa.Column("ip_origen", sa.String(length=45), nullable=True),
        sa.PrimaryKeyConstraint("id_registro"),
    )
    op.create_index(
        op.f("ix_bitacora_auditoria_ocurrido_en"),
        "bitacora_auditoria",
        ["ocurrido_en"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_bitacora_auditoria_ocurrido_en"), table_name="bitacora_auditoria"
    )
    op.drop_table("bitacora_auditoria")
    op.drop_index(op.f("ix_notificacion_id_usuario"), table_name="notificacion")
    op.drop_table("notificacion")
