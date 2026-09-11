from datetime import datetime, timezone

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class TrainingPlan(Base):
    __tablename__ = "training_plans"

    __table_args__ = (
        CheckConstraint(
            "length(trim(title)) >= 2",
            name="ck_training_plans_title",
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

    title = Column(
        String(150),
        nullable=False,
    )

    instructions = Column(
        Text,
        nullable=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    client = relationship(
        "User",
        foreign_keys=[client_id],
    )

    days = relationship(
        "TrainingDay",
        back_populates="plan",
        cascade="all, delete-orphan",
        order_by="TrainingDay.position",
    )


class TrainingDay(Base):
    __tablename__ = "training_days"

    __table_args__ = (
        UniqueConstraint(
            "plan_id",
            "position",
            name="uq_training_days_plan_position",
        ),
        CheckConstraint(
            "position BETWEEN 1 AND 7",
            name="ck_training_days_position",
        ),
        CheckConstraint(
            "length(trim(name)) >= 2",
            name="ck_training_days_name",
        ),
    )

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    plan_id = Column(
        Integer,
        ForeignKey(
            "training_plans.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    position = Column(
        Integer,
        nullable=False,
    )

    name = Column(
        String(100),
        nullable=False,
    )

    plan = relationship(
        "TrainingPlan",
        back_populates="days",
    )

    exercises = relationship(
        "TrainingExercise",
        back_populates="day",
        cascade="all, delete-orphan",
        order_by="TrainingExercise.position",
    )


class TrainingExercise(Base):
    __tablename__ = "training_exercises"

    __table_args__ = (
        UniqueConstraint(
            "day_id",
            "position",
            name="uq_training_exercises_day_position",
        ),
        CheckConstraint(
            "position BETWEEN 1 AND 30",
            name="ck_training_exercises_position",
        ),
        CheckConstraint(
            "sets BETWEEN 1 AND 20",
            name="ck_training_exercises_sets",
        ),
        CheckConstraint(
            "rest_seconds BETWEEN 0 AND 1800",
            name="ck_training_exercises_rest",
        ),
        CheckConstraint(
            "length(trim(name)) >= 2",
            name="ck_training_exercises_name",
        ),
        CheckConstraint(
            "length(trim(repetitions)) >= 1",
            name="ck_training_exercises_repetitions",
        ),
    )

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    day_id = Column(
        Integer,
        ForeignKey(
            "training_days.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    position = Column(
        Integer,
        nullable=False,
    )

    name = Column(
        String(150),
        nullable=False,
    )

    sets = Column(
        Integer,
        nullable=False,
    )

    repetitions = Column(
        String(50),
        nullable=False,
    )

    rest_seconds = Column(
        Integer,
        nullable=False,
    )

    notes = Column(
        Text,
        nullable=True,
    )

    day = relationship(
        "TrainingDay",
        back_populates="exercises",
    )