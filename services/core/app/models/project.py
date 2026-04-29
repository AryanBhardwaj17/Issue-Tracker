"""
Project ORM model.

Represents a project workspace. `owner_id` is a plain integer referencing
a user in auth_db — no cross-DB foreign key is declared.
`key` is a short uppercase slug (e.g. SHOP) auto-generated in the service layer.
"""

from datetime import UTC, datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Project(Base):
    """Persisted project record."""

    __tablename__ = "projects"
    __table_args__ = (
        UniqueConstraint("key", name="uq_projects_key"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    key: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    owner_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    next_story_seq: Mapped[int] = mapped_column(
        BigInteger, nullable=False, default=0, server_default="0"
    )
    is_deleted: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false", index=True
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
    members: Mapped[list["ProjectMember"]] = relationship(  # noqa: F821
        back_populates="project",
        cascade="all, delete-orphan",
        lazy="noload",
    )
    epics: Mapped[list["Epic"]] = relationship(  # noqa: F821
        back_populates="project",
        lazy="noload",
    )
    stories: Mapped[list["UserStory"]] = relationship(  # noqa: F821
        back_populates="project",
        lazy="noload",
    )

    def __repr__(self) -> str:
        return f"<Project id={self.id} key={self.key!r}>"
