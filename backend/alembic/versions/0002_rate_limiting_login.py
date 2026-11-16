"""Añade columnas de rate limiting a usuario (OWASP A07).

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-16 15:00:00
"""
from alembic import op
import sqlalchemy as sa

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.add_column("usuario", sa.Column("intentos_fallidos", sa.Integer(), server_default="0", nullable=False))
    op.add_column("usuario", sa.Column("bloqueado_hasta", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("usuario", "bloqueado_hasta")
    op.drop_column("usuario", "intentos_fallidos")
