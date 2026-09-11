from datetime import datetime, timezone

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)


class TrainingExerciseWrite(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    position: int = Field(ge=1, le=30)
    name: str = Field(min_length=2, max_length=150)
    sets: int = Field(ge=1, le=20)
    repetitions: str = Field(min_length=1, max_length=50)
    rest_seconds: int = Field(ge=0, le=1800)
    notes: str | None = Field(
        default=None,
        max_length=2000,
    )


class TrainingDayWrite(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    position: int = Field(ge=1, le=7)
    name: str = Field(min_length=2, max_length=100)

    exercises: list[TrainingExerciseWrite] = Field(
        min_length=1,
        max_length=30,
    )

    @field_validator("exercises")
    @classmethod
    def validate_exercise_positions(
        cls,
        exercises: list[TrainingExerciseWrite],
    ) -> list[TrainingExerciseWrite]:
        positions = [
            exercise.position
            for exercise in exercises
        ]

        if len(positions) != len(set(positions)):
            raise ValueError(
                "No puede haber ejercicios con la misma "
                "posición dentro de un día."
            )

        return sorted(
            exercises,
            key=lambda exercise: exercise.position,
        )


class TrainingPlanWrite(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    title: str = Field(min_length=2, max_length=150)

    instructions: str | None = Field(
        default=None,
        max_length=5000,
    )

    days: list[TrainingDayWrite] = Field(
        min_length=1,
        max_length=7,
    )

    @field_validator("days")
    @classmethod
    def validate_day_positions(
        cls,
        days: list[TrainingDayWrite],
    ) -> list[TrainingDayWrite]:
        positions = [
            day.position
            for day in days
        ]

        if len(positions) != len(set(positions)):
            raise ValueError(
                "No puede haber días con la misma "
                "posición dentro del plan."
            )

        return sorted(
            days,
            key=lambda day: day.position,
        )


class TrainingExerciseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    position: int
    name: str
    sets: int
    repetitions: str
    rest_seconds: int
    notes: str | None


class TrainingDayRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    position: int
    name: str
    exercises: list[TrainingExerciseRead]


class TrainingPlanRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    client_id: int
    title: str
    instructions: str | None
    created_at: datetime
    updated_at: datetime
    days: list[TrainingDayRead]

    @field_validator("created_at", "updated_at")
    @classmethod
    def normalize_datetime(cls, value: datetime) -> datetime:
        # Las fechas del modelo se generan en UTC.
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)

        return value.astimezone(timezone.utc)