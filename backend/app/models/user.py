from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Integer,
    String,
    text,
    true,
)

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    __table_args__ = (
        CheckConstraint(
            "role IN ('admin', 'coach', 'client')",
            name="ck_users_role",
        ),
    )

    id = Column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True,
    )

    email = Column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )

    hashed_password = Column(
        String(255),
        nullable=False,
    )

    role = Column(
        String(20),
        nullable=False,
        default="client",
        server_default="client",
    )

    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
        server_default=true(),
    )

    auth_version = Column(Integer, nullable=False, default=0, server_default="0")

    created_at = Column(
    DateTime(timezone=True),
    nullable=False,
    default=lambda: datetime.now(timezone.utc),
    server_default=text("CURRENT_TIMESTAMP"),
)