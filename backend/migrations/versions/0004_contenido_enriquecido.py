"""Cuerpo enriquecido y campos propios de la guía

Revision ID: 0004
Revises: 0003
Create Date: 2026-11-05

Los criterios de US-08 piden dos cosas que el esquema de la migración 0001 no
contemplaba:

1. Todo contenido admite un cuerpo enriquecido, imágenes y una URL de video.
2. La guía admite además personaje, medidas, técnicas, presupuesto y seguridad.

Se agregan como columnas nuevas y no se reemplaza nada: `pasos` y `materiales`
siguen siendo útiles para una guía paso a paso.
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("contenido") as lote:
        lote.add_column(sa.Column("cuerpo", sa.Text(), nullable=True))
        lote.add_column(sa.Column("imagenes", sa.JSON(), nullable=True))
        lote.add_column(sa.Column("video_url", sa.String(length=500), nullable=True))

    with op.batch_alter_table("guia_tutorial") as lote:
        lote.add_column(sa.Column("personaje", sa.String(length=120), nullable=True))
        lote.add_column(sa.Column("medidas", sa.JSON(), nullable=True))
        lote.add_column(sa.Column("tecnicas", sa.JSON(), nullable=True))
        lote.add_column(sa.Column("presupuesto", sa.String(length=200), nullable=True))
        lote.add_column(sa.Column("seguridad", sa.Text(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("guia_tutorial") as lote:
        lote.drop_column("seguridad")
        lote.drop_column("presupuesto")
        lote.drop_column("tecnicas")
        lote.drop_column("medidas")
        lote.drop_column("personaje")

    with op.batch_alter_table("contenido") as lote:
        lote.drop_column("video_url")
        lote.drop_column("imagenes")
        lote.drop_column("cuerpo")
