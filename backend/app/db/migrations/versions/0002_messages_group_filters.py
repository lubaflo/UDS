"""add message grouping and filtering fields

Revision ID: 0002_messages_group_filters
Revises: 0001_init
Create Date: 2026-02-11
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0002_messages_group_filters"
down_revision = "0001_init"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("messages", sa.Column("message_type", sa.String(length=16), nullable=False, server_default="individual"))
    op.add_column("messages", sa.Column("group_name", sa.String(length=100), nullable=False, server_default=""))
    op.add_column("messages", sa.Column("channel", sa.String(length=24), nullable=False, server_default="telegram"))
    op.add_column("messages", sa.Column("delivery_status", sa.String(length=24), nullable=False, server_default="sent"))
    op.add_column("messages", sa.Column("scheduled_for", sa.Integer(), nullable=True))
    op.add_column("messages", sa.Column("subject", sa.String(length=200), nullable=False, server_default=""))
    op.add_column("messages", sa.Column("destination", sa.String(length=255), nullable=False, server_default=""))
    op.add_column("messages", sa.Column("client_tg_id", sa.Integer(), nullable=True))

    op.create_index("ix_messages_salon_tg_created", "messages", ["salon_id", "client_tg_id", "created_at"])
    op.create_index("ix_messages_salon_status_created", "messages", ["salon_id", "delivery_status", "created_at"])
    op.create_index("ix_messages_salon_channel_created", "messages", ["salon_id", "channel", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_messages_salon_channel_created", table_name="messages")
    op.drop_index("ix_messages_salon_status_created", table_name="messages")
    op.drop_index("ix_messages_salon_tg_created", table_name="messages")

    op.drop_column("messages", "client_tg_id")
    op.drop_column("messages", "destination")
    op.drop_column("messages", "subject")
    op.drop_column("messages", "scheduled_for")
    op.drop_column("messages", "delivery_status")
    op.drop_column("messages", "channel")
    op.drop_column("messages", "group_name")
    op.drop_column("messages", "message_type")
