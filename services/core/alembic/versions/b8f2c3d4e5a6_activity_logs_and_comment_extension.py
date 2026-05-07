"""activity_logs_and_comment_extension

Revision ID: b8f2c3d4e5a6
Revises: a630cfe2a238
Create Date: 2025-07-25 10:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b8f2c3d4e5a6"
down_revision: str | None = "a630cfe2a238"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ── Create enum types via raw SQL (avoids SQLAlchemy double-creation) ──
    op.execute("CREATE TYPE activity_entity_type AS ENUM ('story', 'task', 'subtask', 'epic')")
    op.execute(
        "CREATE TYPE activity_action AS ENUM "
        "('created', 'deleted', 'restored', 'status_changed', "
        "'assigned', 'completed', 'field_updated')"
    )

    # ── Create activity_logs table ────────────────────────────────────────
    # Use sa.Text() for enum columns to avoid SQLAlchemy trying to CREATE TYPE
    # again during create_table; we ALTER to the real enum type immediately after.
    op.create_table(
        "activity_logs",
        sa.Column("id", UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", UUID(as_uuid=True), nullable=False),
        sa.Column("story_id", UUID(as_uuid=True), nullable=True),
        sa.Column("task_id", UUID(as_uuid=True), nullable=True),
        sa.Column("epic_id", UUID(as_uuid=True), nullable=True),
        sa.Column("entity_type", sa.Text(), nullable=False),
        sa.Column("action", sa.Text(), nullable=False),
        sa.Column("field_name", sa.String(length=50), nullable=True),
        sa.Column("old_value", sa.String(), nullable=True),
        sa.Column("new_value", sa.String(), nullable=True),
        sa.Column("actor_id", UUID(as_uuid=True), nullable=False),
        sa.Column("actor_name", sa.String(length=200), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["story_id"], ["user_stories.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["epic_id"], ["epics.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    # Now cast columns to the real enum types
    op.execute(
        "ALTER TABLE activity_logs "
        "ALTER COLUMN entity_type TYPE activity_entity_type "
        "USING entity_type::activity_entity_type"
    )
    op.execute(
        "ALTER TABLE activity_logs "
        "ALTER COLUMN action TYPE activity_action "
        "USING action::activity_action"
    )
    op.create_index("ix_activity_project_created", "activity_logs", ["project_id", "created_at"])
    op.create_index("ix_activity_story_created", "activity_logs", ["story_id", "created_at"])
    op.create_index("ix_activity_task_created", "activity_logs", ["task_id", "created_at"])
    op.create_index("ix_activity_epic_created", "activity_logs", ["epic_id", "created_at"])

    # ── Extend comments table ─────────────────────────────────────────────
    # 1) Make user_story_id nullable and change FK ondelete
    #    Drop old FK, alter column, re-add FK with SET NULL
    op.drop_constraint("comments_user_story_id_fkey", "comments", type_="foreignkey")
    op.alter_column("comments", "user_story_id", existing_type=UUID(as_uuid=True), nullable=True)
    op.create_foreign_key(
        "comments_user_story_id_fkey",
        "comments",
        "user_stories",
        ["user_story_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # 2) Add task_id and epic_id columns
    op.add_column("comments", sa.Column("task_id", UUID(as_uuid=True), nullable=True))
    op.add_column("comments", sa.Column("epic_id", UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        "comments_task_id_fkey", "comments", "tasks", ["task_id"], ["id"], ondelete="SET NULL"
    )
    op.create_foreign_key(
        "comments_epic_id_fkey", "comments", "epics", ["epic_id"], ["id"], ondelete="SET NULL"
    )

    # 3) Add indexes for new columns
    op.create_index("ix_comments_task_deleted", "comments", ["task_id", "is_deleted"])
    op.create_index("ix_comments_epic_deleted", "comments", ["epic_id", "is_deleted"])

    # 4) Add CHECK constraint: exactly one FK must be non-null
    op.create_check_constraint(
        "ck_comments_one_owner",
        "comments",
        "(CASE WHEN user_story_id IS NOT NULL THEN 1 ELSE 0 END"
        " + CASE WHEN task_id IS NOT NULL THEN 1 ELSE 0 END"
        " + CASE WHEN epic_id IS NOT NULL THEN 1 ELSE 0 END) = 1",
    )


def downgrade() -> None:
    # ── Revert comments table ─────────────────────────────────────────────
    op.drop_constraint("ck_comments_one_owner", "comments", type_="check")
    op.drop_index("ix_comments_epic_deleted", table_name="comments")
    op.drop_index("ix_comments_task_deleted", table_name="comments")
    op.drop_constraint("comments_epic_id_fkey", "comments", type_="foreignkey")
    op.drop_constraint("comments_task_id_fkey", "comments", type_="foreignkey")
    op.drop_column("comments", "epic_id")
    op.drop_column("comments", "task_id")

    # Revert user_story_id back to NOT NULL with CASCADE
    op.drop_constraint("comments_user_story_id_fkey", "comments", type_="foreignkey")
    op.alter_column("comments", "user_story_id", existing_type=UUID(as_uuid=True), nullable=False)
    op.create_foreign_key(
        "comments_user_story_id_fkey",
        "comments",
        "user_stories",
        ["user_story_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # ── Drop activity_logs table ──────────────────────────────────────────
    op.drop_index("ix_activity_epic_created", table_name="activity_logs")
    op.drop_index("ix_activity_task_created", table_name="activity_logs")
    op.drop_index("ix_activity_story_created", table_name="activity_logs")
    op.drop_index("ix_activity_project_created", table_name="activity_logs")
    op.drop_table("activity_logs")

    # ── Drop enum types ───────────────────────────────────────────────────
    op.execute("DROP TYPE IF EXISTS activity_action")
    op.execute("DROP TYPE IF EXISTS activity_entity_type")
