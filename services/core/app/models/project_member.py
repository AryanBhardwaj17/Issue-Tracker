"""
ProjectMember ORM model.

Links a user (from auth_db) to a project with a role of OWNER or MEMBER.
`username` is denormalized from auth_db at join time so member lists can be
served without a cross-service call.
"""

import enum
from datetime import UTC, datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class MemberRole(str, enum.Enum):
    OWNER = "owner"
    MEMBER = "member"


class ProjectMember(Base):
    """Project membership record with a denormalized username."""

    __tablename__ = "project_members"
    __table_args__ = (
        UniqueConstraint("project_id", "user_id", name="uq_project_members_project_user"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    username: Mapped[str] = mapped_column(String(50), nullable=False)
    role: Mapped[MemberRole] = mapped_column(
        Enum(MemberRole, name="member_role"),
        nullable=False,
    )
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )

    # Relationships
    project: Mapped["Project"] = relationship(back_populates="members")  # noqa: F821

    def __repr__(self) -> str:
        return f"<ProjectMember project_id={self.project_id} user_id={self.user_id} role={self.role}>"
