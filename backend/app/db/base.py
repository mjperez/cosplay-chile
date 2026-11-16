import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, MetaData, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# Nombres de constraints deterministas para que Alembic genere migraciones estables
NAMING = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING)


class IdMixin:
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


def ahora_utc() -> datetime:
    return datetime.now(timezone.utc)


class CreadoMixin:
    # default en Python además del de servidor: el valor queda disponible tras el flush
    # sin una recarga perezosa (que en modo async no está permitida)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), default=ahora_utc, nullable=False
    )
