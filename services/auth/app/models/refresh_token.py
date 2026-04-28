"""
RefreshToken ORM model.

Stores the SHA-256 hash of opaque refresh tokens. The raw token is never
persisted — only its hash.  Tokens are revoked individually (logout) or
in bulk (logout-all).  Cascade DELETE ensures tokens are removed when the
parent user is deleted.
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class RefreshToken(Base):
    """Persisted refresh token record (stores SHA-256 hash, not the raw token).

    Use the ``is_expired`` property to check expiry without an extra query.
    """

    __tablename__ = "refresh_tokens"
    __table_args__ = (UniqueConstraint("token", name="uq_refresh_token"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    # SHA-256 hex digest is always 64 characters.
    token: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )

    user: Mapped["User"] = relationship(back_populates="refresh_tokens")  # noqa: F821

    @property
    def is_expired(self) -> bool:
        """Return True if the token's expiry timestamp has passed.

        SQLite returns timezone-naive datetimes; ``expires_at`` is stored as
        timezone-aware in Postgres.  We normalise to UTC-aware for the
        comparison so the property works correctly under both backends.
        """
        expires = self.expires_at
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=UTC)
        return datetime.now(UTC) >= expires

    def __repr__(self) -> str:
        return (
            f"<RefreshToken id={self.id} user_id={self.user_id}"
            f" revoked={self.revoked} expired={self.is_expired}>"
        )
