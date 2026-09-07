from datetime import datetime, timezone

from sqlalchemy import (
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    text,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class ClientProfile(Base):
    __tablename__ = "client_profiles"

    __table_args__ = (
        CheckConstraint(
            "height_cm > 0",
            name="ck_client_profiles_height_positive",
        ),
        CheckConstraint(
            "sex IN ('female', 'male', 'other', 'prefer_not_to_say')",
            name="ck_client_profiles_sex",
        ),
        CheckConstraint(
            "goal IN ('fat_loss', 'muscle_gain', 'maintenance', 'performance')",
            name="ck_client_profiles_goal",
        ),
        CheckConstraint(
            "training_level IN ('beginner', 'intermediate', 'advanced')",
            name="ck_client_profiles_training_level",
        ),
    )

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )

    full_name = Column(
        String(150),
        nullable=False,
    )

    birth_date = Column(
        Date,
        nullable=False,
    )

    sex = Column(
        String(20),
        nullable=False,
    )

    height_cm = Column(
        Numeric(5, 2),
        nullable=False,
    )

    goal = Column(
        String(30),
        nullable=False,
    )

    training_level = Column(
        String(20),
        nullable=False,
    )

    medical_restrictions = Column(
        Text,
        nullable=True,
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

    user = relationship("User")

    assessments = relationship(
        "BodyAssessment",
        back_populates="client_profile",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )