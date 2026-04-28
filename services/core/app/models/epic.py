"""
Epic ORM model.

Groups multiple user stories under a named theme. `reporter_id` is a plain
integer resolved against project_members at query time — no cross-DB FK.
"""

from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Epic(Base):
    """Persisted epic record."""

    __tablename__ = "epics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    reporter_id: Mapped[int] = mapped_column(Integer, nullable=False)
    is_deleted: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    # Relationships
    project: Mapped["Project"] = relationship(back_populates="epics")  # noqa: F821
    stories: Mapped[list["UserStory"]] = relationship(  # noqa: F821
        back_populates="epic",
        lazy="noload",
    )

    def __repr__(self) -> str:
        return f"<Epic id={self.id} name={self.name!r}>"
