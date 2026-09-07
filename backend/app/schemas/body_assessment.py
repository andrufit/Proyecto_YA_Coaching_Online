from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class BodyAssessmentCreate(BaseModel):
    assessment_date: date = Field(
        default_factory=date.today,
    )
    weight_kg: Decimal = Field(
        gt=0,
        le=500,
        max_digits=5,
        decimal_places=2,
    )
    body_fat_percentage: Decimal | None = Field(
        default=None,
        ge=0,
        le=100,
        max_digits=5,
        decimal_places=2,
    )
    waist_cm: Decimal | None = Field(
        default=None,
        gt=0,
        le=500,
        max_digits=5,
        decimal_places=2,
    )
    hip_cm: Decimal | None = Field(
        default=None,
        gt=0,
        le=500,
        max_digits=5,
        decimal_places=2,
    )
    chest_cm: Decimal | None = Field(
        default=None,
        gt=0,
        le=500,
        max_digits=5,
        decimal_places=2,
    )
    notes: str | None = Field(
        default=None,
        max_length=2000,
    )

    @field_validator("assessment_date")
    @classmethod
    def validate_assessment_date(cls, value: date) -> date:
        if value > date.today():
            raise ValueError(
                "La fecha de valoración no puede estar en el futuro"
            )
        return value


class BodyAssessmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    client_profile_id: int
    assessment_date: date
    weight_kg: Decimal
    body_fat_percentage: Decimal | None
    waist_cm: Decimal | None
    hip_cm: Decimal | None
    chest_cm: Decimal | None
    notes: str | None
    created_at: datetime