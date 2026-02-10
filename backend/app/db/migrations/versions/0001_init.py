"""init schema

Revision ID: 0001_init
Revises:
Create Date: 2026-02-06
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0001_init"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "salons",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("timezone", sa.String(length=64), nullable=False, server_default="Europe/Moscow"),
        sa.Column("locale", sa.String(length=16), nullable=False, server_default="ru"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="active"),
    )

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("salon_id", sa.Integer(), sa.ForeignKey("salons.id", ondelete="CASCADE"), nullable=False),
        sa.Column("tg_id", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False, server_default="admin"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("display_name", sa.String(length=200), nullable=False, server_default=""),
        sa.UniqueConstraint("tg_id", name="uq_users_tg_id"),
    )

    op.create_table(
        "clients",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("salon_id", sa.Integer(), sa.ForeignKey("salons.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False, server_default=""),
        sa.Column("phone", sa.String(length=32), nullable=False, server_default=""),
        sa.Column("tg_id", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="active"),
        sa.Column("notes", sa.String(length=2000), nullable=False, server_default=""),
        sa.Column("tags_csv", sa.String(length=1000), nullable=False, server_default=""),
        sa.Column("visits_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_spent_rub", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_visit_at", sa.String(length=32), nullable=False, server_default=""),
    )
    op.create_index("ix_clients_salon_phone", "clients", ["salon_id", "phone"])
    op.create_index("ix_clients_salon_name", "clients", ["salon_id", "name"])

    op.create_table(
        "messages",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("salon_id", sa.Integer(), sa.ForeignKey("salons.id", ondelete="CASCADE"), nullable=False),
        sa.Column("client_id", sa.Integer(), sa.ForeignKey("clients.id", ondelete="CASCADE"), nullable=False),
        sa.Column("direction", sa.String(length=16), nullable=False),
        sa.Column("text", sa.String(length=4000), nullable=False, server_default=""),
        sa.Column("created_at", sa.Integer(), nullable=False),
    )
    op.create_index("ix_messages_salon_client_created", "messages", ["salon_id", "client_id", "created_at"])

    op.create_table(
        "audit_log",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("salon_id", sa.Integer(), sa.ForeignKey("salons.id", ondelete="CASCADE"), nullable=False),
        sa.Column("actor_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("action", sa.String(length=64), nullable=False),
        sa.Column("entity", sa.String(length=64), nullable=False),
        sa.Column("entity_id", sa.String(length=64), nullable=False, server_default=""),
        sa.Column("meta_json", sa.String(length=2000), nullable=False, server_default=""),
        sa.Column("created_at", sa.Integer(), nullable=False),
    )
    op.create_index("ix_audit_salon_created", "audit_log", ["salon_id", "created_at"])
    op.create_index("ix_audit_salon_actor_created", "audit_log", ["salon_id", "actor_user_id", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_audit_salon_actor_created", table_name="audit_log")
    op.drop_index("ix_audit_salon_created", table_name="audit_log")
    op.drop_table("audit_log")

    op.drop_index("ix_messages_salon_client_created", table_name="messages")
    op.drop_table("messages")

    op.drop_index("ix_clients_salon_name", table_name="clients")
    op.drop_index("ix_clients_salon_phone", table_name="clients")
    op.drop_table("clients")

    op.drop_table("users")
    op.drop_table("salons")