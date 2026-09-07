from datetime import date, datetime, timezone

from sqlalchemy import (
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    Text,
    text,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class BodyAssessment(Base):
    __tablename__ = "body_assessments"

    __table_args__ = (
        CheckConstraint(
            "weight_kg > 0",
            name="ck_body_assessments_weight_positive",
        ),
        CheckConstraint(
            "body_fat_percentage IS NULL "
            "OR (body_fat_percentage >= 0 AND body_fat_percentage <= 100)",
            name="ck_body_assessments_body_fat_range",
        ),
        CheckConstraint(
            "waist_cm IS NULL OR waist_cm > 0",
            name="ck_body_assessments_waist_positive",
        ),
        CheckConstraint(
            "hip_cm IS NULL OR hip_cm > 0",
            name="ck_body_assessments_hip_positive",
        ),
        CheckConstraint(
            "chest_cm IS NULL OR chest_cm > 0",
            name="ck_body_assessments_chest_positive",
        ),
    )

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    client_profile_id = Column(
        Integer,
        ForeignKey("client_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    assessment_date = Column(
        Date,
        nullable=False,
        default=date.today,
        server_default=text("CURRENT_DATE"),
    )

    weight_kg = Column(
        Numeric(5, 2),
        nullable=False,
    )

    body_fat_percentage = Column(
        Numeric(5, 2),
        nullable=True,
    )

    waist_cm = Column(
        Numeric(5, 2),
        nullable=True,
    )

    hip_cm = Column(
        Numeric(5, 2),
        nullable=True,
    )

    chest_cm = Column(
        Numeric(5, 2),
        nullable=True,
    )

    notes = Column(
        Text,
        nullable=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=text("CURRENT_TIMESTAMP"),
    )

    client_profile = relationship(
        "ClientProfile",
        back_populates="assessments",
    )