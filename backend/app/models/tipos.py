from sqlalchemy import Enum as SAEnum


def enum_col(enum_cls, length: int = 30) -> SAEnum:
    """Enum guardado como VARCHAR + CHECK (más fácil de migrar que un ENUM nativo)."""
    return SAEnum(
        enum_cls,
        native_enum=False,
        length=length,
        validate_strings=True,
        values_callable=lambda e: [m.value for m in e],
        create_constraint=True,
    )
