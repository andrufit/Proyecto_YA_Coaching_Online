from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field, field_validator


class NutritionFoodWrite(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    position: int = Field(ge=1, le=30)
    name: str = Field(min_length=2, max_length=150)
    quantity: str = Field(min_length=1, max_length=100)
    notes: str | None = Field(default=None, max_length=2000)


class NutritionMealWrite(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    position: int = Field(ge=1, le=10)
    name: str = Field(min_length=2, max_length=100)
    notes: str | None = Field(default=None, max_length=2000)
    foods: list[NutritionFoodWrite] = Field(
        min_length=1,
        max_length=30,
    )

    @field_validator("foods")
    @classmethod
    def validate_food_positions(
        cls,
        foods: list[NutritionFoodWrite],
    ) -> list[NutritionFoodWrite]:
        positions = [food.position for food in foods]

        if len(positions) != len(set(positions)):
            raise ValueError(
                "Los alimentos no pueden tener posiciones repetidas."
            )

        return sorted(foods, key=lambda food: food.position)


class NutritionPlanWrite(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    title: str = Field(min_length=2, max_length=150)
    instructions: str | None = Field(
        default=None,
        max_length=5000,
    )
    meals: list[NutritionMealWrite] = Field(
        min_length=1,
        max_length=10,
    )

    @field_validator("meals")
    @classmethod
    def validate_meal_positions(
        cls,
        meals: list[NutritionMealWrite],
    ) -> list[NutritionMealWrite]:
        positions = [meal.position for meal in meals]

        if len(positions) != len(set(positions)):
            raise ValueError(
                "Las comidas no pueden tener posiciones repetidas."
            )

        return sorted(meals, key=lambda meal: meal.position)


class NutritionFoodRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    position: int
    name: str
    quantity: str
    notes: str | None


class NutritionMealRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    position: int
    name: str
    notes: str | None
    foods: list[NutritionFoodRead]


class NutritionPlanRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    client_id: int
    title: str
    instructions: str | None
    created_at: datetime
    updated_at: datetime
    meals: list[NutritionMealRead]

    @field_validator("created_at", "updated_at")
    @classmethod
    def normalize_datetime(cls, value: datetime) -> datetime:
        # Las fechas del proyecto se generan en UTC.
        # SQLite puede devolverlas sin información de zona horaria.
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)

        return value.astimezone(timezone.utc)