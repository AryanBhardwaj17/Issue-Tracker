"""initial_schema

Revision ID: f3a9c2d8b1e7
Revises:
Create Date: 2026-05-04 00:00:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "f3a9c2d8b1e7"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enum type — use DO block to skip if already exists
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE delivery_status AS ENUM ('pending', 'sent', 'failed');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS email_deliveries (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            event_type VARCHAR(50) NOT NULL,
            recipient_email VARCHAR(255) NOT NULL,
            payload JSON NOT NULL,
            status delivery_status NOT NULL DEFAULT 'pending',
            error_message TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            sent_at TIMESTAMPTZ
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_email_deliveries_event_status ON email_deliveries (event_type, status)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_email_deliveries_created_at ON email_deliveries (created_at)")

    op.execute("""
        CREATE TABLE IF NOT EXISTS notifications (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL,
            event_type VARCHAR(50) NOT NULL,
            title VARCHAR(200) NOT NULL,
            body TEXT NOT NULL,
            link VARCHAR(500),
            is_read BOOLEAN NOT NULL DEFAULT false,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_notifications_user_read_created ON notifications (user_id, is_read, created_at)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_notifications_user_read_created")
    op.execute("DROP TABLE IF EXISTS notifications")
    op.execute("DROP INDEX IF EXISTS ix_email_deliveries_created_at")
    op.execute("DROP INDEX IF EXISTS ix_email_deliveries_event_status")
    op.execute("DROP TABLE IF EXISTS email_deliveries")
    op.execute("DROP TYPE IF EXISTS delivery_status")
