"""Esquema inicial: usuarios, contenidos, directorio, eventos y comunidad

Revision ID: 0001
Revises:
Create Date: 2026-11-05

Traduce a tablas el modelo entidad-relación del informe (figuras 9 y 10) y la
jerarquía de contenidos del diagrama de clases. Los tipos son portables
(Uuid, JSON, Enum sin tipo nativo) para que la misma migración corra en
PostgreSQL y en SQLite, y para no atar el esquema a una extensión de Neon.
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _marcas_de_tiempo() -> list[sa.Column]:
    return [
        sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("actualizado_en", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    ]


def upgrade() -> None:
    # --- Usuarios -------------------------------------------------------
    op.create_table(
        "usuario",
        sa.Column("id_usuario", sa.Uuid(), nullable=False),
        sa.Column("nombre", sa.String(length=120), nullable=False),
        sa.Column("correo", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column(
            "rol",
            sa.Enum(
                "visitante",
                "cosplayer",
                "cosmaker",
                "sastre",
                "tienda",
                "fotografo",
                "organizador",
                "administrador",
                name="rol_usuario",
                native_enum=False,
            ),
            nullable=False,
        ),
        sa.Column("region", sa.String(length=80), nullable=False),
        sa.Column("activo", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("consentimiento_fecha", sa.DateTime(timezone=True), nullable=True),
        sa.Column("consentimiento_version", sa.String(length=20), nullable=True),
        *_marcas_de_tiempo(),
        sa.PrimaryKeyConstraint("id_usuario"),
    )
    op.create_index("ix_usuario_correo", "usuario", ["correo"], unique=True)

    op.create_table(
        "perfil_cosplayer",
        sa.Column("id_perfil", sa.Uuid(), nullable=False),
        sa.Column("id_usuario", sa.Uuid(), nullable=False),
        sa.Column("especialidad", sa.String(length=120), nullable=True),
        sa.Column("portafolio_url", sa.String(length=500), nullable=True),
        sa.Column("biografia", sa.Text(), nullable=True),
        sa.Column("region", sa.String(length=80), nullable=True),
        sa.ForeignKeyConstraint(["id_usuario"], ["usuario.id_usuario"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id_perfil"),
        sa.UniqueConstraint("id_usuario", name="uq_perfil_usuario"),
    )

    # --- Contenidos -----------------------------------------------------
    op.create_table(
        "categoria_contenido",
        sa.Column("id_categoria", sa.Uuid(), nullable=False),
        sa.Column("nombre", sa.String(length=80), nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id_categoria"),
        sa.UniqueConstraint("nombre", name="uq_categoria_nombre"),
    )

    op.create_table(
        "contenido",
        sa.Column("id_contenido", sa.Uuid(), nullable=False),
        sa.Column("id_autor", sa.Uuid(), nullable=False),
        sa.Column("id_categoria", sa.Uuid(), nullable=True),
        sa.Column("titulo", sa.String(length=200), nullable=False),
        sa.Column("resumen", sa.Text(), nullable=True),
        sa.Column(
            "nivel",
            sa.Enum(
                "basico", "intermedio", "avanzado",
                name="nivel_dificultad", native_enum=False,
            ),
            nullable=False,
        ),
        sa.Column(
            "estado",
            sa.Enum(
                "pendiente", "publicado", "rechazado",
                name="estado_contenido", native_enum=False,
            ),
            nullable=False,
        ),
        sa.Column("fecha_publicacion", sa.DateTime(timezone=True), nullable=True),
        sa.Column("tipo", sa.String(length=20), nullable=False),
        *_marcas_de_tiempo(),
        sa.ForeignKeyConstraint(["id_autor"], ["usuario.id_usuario"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["id_categoria"], ["categoria_contenido.id_categoria"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id_contenido"),
    )
    op.create_index("ix_contenido_autor", "contenido", ["id_autor"])
    op.create_index("ix_contenido_estado", "contenido", ["estado"])

    op.create_table(
        "guia_tutorial",
        sa.Column("id_contenido", sa.Uuid(), nullable=False),
        sa.Column("pasos", sa.JSON(), nullable=True),
        sa.Column("materiales", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(["id_contenido"], ["contenido.id_contenido"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id_contenido"),
    )

    op.create_table(
        "entrevista",
        sa.Column("id_contenido", sa.Uuid(), nullable=False),
        sa.Column("preguntas", sa.JSON(), nullable=True),
        sa.Column("respuestas", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(["id_contenido"], ["contenido.id_contenido"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id_contenido"),
    )

    op.create_table(
        "articulo",
        sa.Column("id_contenido", sa.Uuid(), nullable=False),
        sa.Column("enlaces", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(["id_contenido"], ["contenido.id_contenido"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id_contenido"),
    )

    # --- Eventos --------------------------------------------------------
    op.create_table(
        "evento_cosplay",
        sa.Column("id_evento", sa.Uuid(), nullable=False),
        sa.Column("nombre", sa.String(length=200), nullable=False),
        sa.Column(
            "tipo",
            sa.Enum(
                "convencion", "concurso", "feria", "taller", "otro",
                name="tipo_evento", native_enum=False,
            ),
            nullable=False,
        ),
        sa.Column("fecha_inicio", sa.DateTime(timezone=True), nullable=False),
        sa.Column("fecha_fin", sa.DateTime(timezone=True), nullable=True),
        sa.Column("lugar", sa.String(length=200), nullable=False),
        sa.Column("region", sa.String(length=80), nullable=True),
        sa.Column("enlace_oficial", sa.String(length=500), nullable=True),
        *_marcas_de_tiempo(),
        sa.PrimaryKeyConstraint("id_evento"),
    )
    op.create_index("ix_evento_fecha", "evento_cosplay", ["fecha_inicio"])

    op.create_table(
        "participacion_evento",
        sa.Column("id_participacion", sa.Uuid(), nullable=False),
        sa.Column("id_usuario", sa.Uuid(), nullable=False),
        sa.Column("id_evento", sa.Uuid(), nullable=False),
        sa.Column("personaje", sa.String(length=120), nullable=True),
        sa.ForeignKeyConstraint(["id_usuario"], ["usuario.id_usuario"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["id_evento"], ["evento_cosplay.id_evento"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id_participacion"),
        sa.UniqueConstraint("id_usuario", "id_evento", name="uq_participacion_usuario_evento"),
    )

    # --- Directorio -----------------------------------------------------
    op.create_table(
        "proveedor",
        sa.Column("id_proveedor", sa.Uuid(), nullable=False),
        sa.Column("nombre", sa.String(length=160), nullable=False),
        sa.Column(
            "tipo",
            sa.Enum(
                "cosmaker", "sastre", "fotografo", "tienda", "otro",
                name="tipo_proveedor", native_enum=False,
            ),
            nullable=False,
        ),
        sa.Column("region", sa.String(length=80), nullable=False),
        sa.Column("sitio_web", sa.String(length=500), nullable=True),
        sa.Column("contacto", sa.String(length=200), nullable=True),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.Column("activo", sa.Boolean(), server_default=sa.true(), nullable=False),
        *_marcas_de_tiempo(),
        sa.PrimaryKeyConstraint("id_proveedor"),
    )
    op.create_index("ix_proveedor_nombre", "proveedor", ["nombre"])
    op.create_index("ix_proveedor_region", "proveedor", ["region"])

    op.create_table(
        "donde_comprar",
        sa.Column("id_tienda", sa.Uuid(), nullable=False),
        sa.Column("nombre", sa.String(length=160), nullable=False),
        sa.Column(
            "tipo",
            sa.Enum(
                "telas", "insumos", "pelucas", "impresion_3d", "otro",
                name="tipo_tienda", native_enum=False,
            ),
            nullable=False,
        ),
        sa.Column("envia_a_chile", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("enlace_web", sa.String(length=500), nullable=True),
        sa.Column("region", sa.String(length=80), nullable=True),
        *_marcas_de_tiempo(),
        sa.PrimaryKeyConstraint("id_tienda"),
    )
    op.create_index("ix_donde_comprar_nombre", "donde_comprar", ["nombre"])

    op.create_table(
        "comunidad_grupo",
        sa.Column("id_comunidad", sa.Uuid(), nullable=False),
        sa.Column("nombre", sa.String(length=160), nullable=False),
        sa.Column("region", sa.String(length=80), nullable=True),
        sa.Column(
            "plataforma",
            sa.Enum(
                "facebook", "discord", "instagram", "whatsapp", "foro", "otro",
                name="plataforma_comunidad", native_enum=False,
            ),
            nullable=False,
        ),
        sa.Column("enlace", sa.String(length=500), nullable=True),
        *_marcas_de_tiempo(),
        sa.PrimaryKeyConstraint("id_comunidad"),
    )
    op.create_index("ix_comunidad_region", "comunidad_grupo", ["region"])

    # --- Comunidad y foro -----------------------------------------------
    op.create_table(
        "foro_tema",
        sa.Column("id_tema", sa.Uuid(), nullable=False),
        sa.Column("id_creador", sa.Uuid(), nullable=False),
        sa.Column("titulo", sa.String(length=200), nullable=False),
        sa.Column("categoria", sa.String(length=80), nullable=False),
        sa.Column("contenido", sa.Text(), nullable=True),
        sa.Column(
            "estado",
            sa.Enum("abierto", "cerrado", "oculto", name="estado_foro", native_enum=False),
            nullable=False,
        ),
        *_marcas_de_tiempo(),
        sa.ForeignKeyConstraint(["id_creador"], ["usuario.id_usuario"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id_tema"),
    )
    op.create_index("ix_foro_tema_creador", "foro_tema", ["id_creador"])
    op.create_index("ix_foro_tema_categoria", "foro_tema", ["categoria"])

    op.create_table(
        "foro_respuesta",
        sa.Column("id_respuesta", sa.Uuid(), nullable=False),
        sa.Column("id_tema", sa.Uuid(), nullable=False),
        sa.Column("id_usuario", sa.Uuid(), nullable=False),
        sa.Column("contenido", sa.Text(), nullable=False),
        *_marcas_de_tiempo(),
        sa.ForeignKeyConstraint(["id_tema"], ["foro_tema.id_tema"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["id_usuario"], ["usuario.id_usuario"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id_respuesta"),
    )
    op.create_index("ix_foro_respuesta_tema", "foro_respuesta", ["id_tema"])

    op.create_table(
        "desafio_mensual",
        sa.Column("id_desafio", sa.Uuid(), nullable=False),
        sa.Column("id_ganador", sa.Uuid(), nullable=True),
        sa.Column("titulo", sa.String(length=200), nullable=False),
        sa.Column("mes", sa.String(length=7), nullable=False),
        *_marcas_de_tiempo(),
        sa.ForeignKeyConstraint(["id_ganador"], ["usuario.id_usuario"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id_desafio"),
    )
    op.create_index("ix_desafio_mes", "desafio_mensual", ["mes"])


def downgrade() -> None:
    op.drop_index("ix_desafio_mes", table_name="desafio_mensual")
    op.drop_table("desafio_mensual")
    op.drop_index("ix_foro_respuesta_tema", table_name="foro_respuesta")
    op.drop_table("foro_respuesta")
    op.drop_index("ix_foro_tema_categoria", table_name="foro_tema")
    op.drop_index("ix_foro_tema_creador", table_name="foro_tema")
    op.drop_table("foro_tema")
    op.drop_index("ix_comunidad_region", table_name="comunidad_grupo")
    op.drop_table("comunidad_grupo")
    op.drop_index("ix_donde_comprar_nombre", table_name="donde_comprar")
    op.drop_table("donde_comprar")
    op.drop_index("ix_proveedor_region", table_name="proveedor")
    op.drop_index("ix_proveedor_nombre", table_name="proveedor")
    op.drop_table("proveedor")
    op.drop_table("participacion_evento")
    op.drop_index("ix_evento_fecha", table_name="evento_cosplay")
    op.drop_table("evento_cosplay")
    op.drop_table("articulo")
    op.drop_table("entrevista")
    op.drop_table("guia_tutorial")
    op.drop_index("ix_contenido_estado", table_name="contenido")
    op.drop_index("ix_contenido_autor", table_name="contenido")
    op.drop_table("contenido")
    op.drop_table("categoria_contenido")
    op.drop_table("perfil_cosplayer")
    op.drop_index("ix_usuario_correo", table_name="usuario")
    op.drop_table("usuario")
