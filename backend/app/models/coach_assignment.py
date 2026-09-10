from datetime import datetime, timezone

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    text,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class CoachAssignment(Base):
    __tablename__ = "coach_assignments"

    __table_args__ = (
        CheckConstraint(
            "client_id <> coach_id",
            name="ck_coach_assignments_different_users",
        ),
    )

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    client_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    coach_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=text("CURRENT_TIMESTAMP"),
    )

    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        server_default=text("CURRENT_TIMESTAMP"),
    )

    client = relationship(
        "User",
        foreign_keys=[client_id],
    )

    coach = relationship(
        "User",
        foreign_keys=[coach_id],
    )