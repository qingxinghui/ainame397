"""add naming poll tables

Revision ID: a81c7f29d403
Revises: 5f00301a06ab
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a81c7f29d403"
down_revision: Union[str, None] = "5f00301a06ab"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "naming_poll",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("creator_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["creator_id"], ["user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_naming_poll_creator_id", "naming_poll", ["creator_id"])
    op.create_index("ix_naming_poll_status", "naming_poll", ["status"])
    op.create_table(
        "naming_poll_option",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("poll_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("moral", sa.Text(), nullable=False),
        sa.Column("vote_count", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["poll_id"], ["naming_poll.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_naming_poll_option_poll_id", "naming_poll_option", ["poll_id"])
    op.create_table(
        "naming_poll_vote",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("poll_id", sa.Integer(), nullable=False),
        sa.Column("option_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["option_id"], ["naming_poll_option.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["poll_id"], ["naming_poll.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("poll_id", "user_id", name="uq_poll_user_vote"),
    )
    op.create_index("ix_naming_poll_vote_option_id", "naming_poll_vote", ["option_id"])
    op.create_index("ix_naming_poll_vote_poll_id", "naming_poll_vote", ["poll_id"])
    op.create_index("ix_naming_poll_vote_user_id", "naming_poll_vote", ["user_id"])


def downgrade() -> None:
    op.drop_table("naming_poll_vote")
    op.drop_table("naming_poll_option")
    op.drop_table("naming_poll")
