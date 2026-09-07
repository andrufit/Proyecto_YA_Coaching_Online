from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


SexType = Literal[
    "female",
    "male",
    "other",
    "prefer_not_to_say",
]

GoalType = Literal[
    "fat_loss",
    "muscle_gain",
    "maintenance",
    "performance",
]

TrainingLevelType = Literal[
    "beginner",
    "intermediate",
    "advanced",
]


class ClientProfileCreate(BaseModel):
    full_name: str = Field(
        min_length=2,
        max_length=150,
    )
    birth_date: date
    sex: SexType
    height_cm: Decimal = Field(
        gt=0,
        le=300,
        max_digits=5,
        decimal_places=2,
    )
    goal: GoalType
    training_level: TrainingLevelType
    medical_restrictions: str | None = Field(
        default=None,
        max_length=2000,
    )

    @field_validator("full_name", mode="before")
    @classmethod
    def clean_full_name(cls, value: object) -> object:
        if isinstance(value, str):
            return " ".join(value.split())
        return value

    @field_validator("birth_date")
    @classmethod
    def validate_birth_date(cls, value: date) -> date:
        if value >= date.today():
            raise ValueError(
                "La fecha de nacimiento debe ser anterior a hoy"
            )
        return value


class ClientProfileUpdate(BaseModel):
    full_name: str | None = Field(
        default=None,
        min_length=2,
        max_length=150,
    )
    birth_date: date | None = None
    sex: SexType | None = None
    height_cm: Decimal | None = Field(
        default=None,
        gt=0,
        le=300,
        max_digits=5,
        decimal_places=2,
    )
    goal: GoalType | None = None
    training_level: TrainingLevelType | None = None
    medical_restrictions: str | None = Field(
        default=None,
        max_length=2000,
    )

    @field_validator(
        "full_name",
        "birth_date",
        "sex",
        "height_cm",
        "goal",
        "training_level",
        mode="before",
    )
    @classmethod
    def reject_null_required_fields(cls, value: object) -> object:
        if value is None:
            raise ValueError("Este campo no puede ser null")
        return value

    @field_validator("full_name", mode="before")
    @classmethod
    def clean_full_name(cls, value: object) -> object:
        if isinstance(value, str):
            return " ".join(value.split())
        return value

    @field_validator("birth_date")
    @classmethod
    def validate_birth_date(
        cls,
        value: date | None,
    ) -> date | None:
        if value is not None and value >= date.today():
            raise ValueError(
                "La fecha de nacimiento debe ser anterior a hoy"
            )
        return value


class ClientProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    full_name: str
    birth_date: date
    sex: SexType
    height_cm: Decimal
    goal: GoalType
    training_level: TrainingLevelType
    medical_restrictions: str | None
    created_at: datetime
    updated_at: datetime