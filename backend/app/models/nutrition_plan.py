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


class NutritionPlan(Base):
    __tablename__ = "nutrition_plans"

    __table_args__ = (
        CheckConstraint(
            "length(trim(title)) >= 2",
            name="ck_nutrition_plans_title",
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

    meals = relationship(
        "NutritionMeal",
        back_populates="plan",
        cascade="all, delete-orphan",
        order_by="NutritionMeal.position",
    )


class NutritionMeal(Base):
    __tablename__ = "nutrition_meals"

    __table_args__ = (
        UniqueConstraint(
            "plan_id",
            "position",
            name="uq_nutrition_meals_plan_position",
        ),
        CheckConstraint(
            "position BETWEEN 1 AND 10",
            name="ck_nutrition_meals_position",
        ),
        CheckConstraint(
            "length(trim(name)) >= 2",
            name="ck_nutrition_meals_name",
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
            "nutrition_plans.id",
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

    notes = Column(
        Text,
        nullable=True,
    )

    plan = relationship(
        "NutritionPlan",
        back_populates="meals",
    )

    foods = relationship(
        "NutritionFood",
        back_populates="meal",
        cascade="all, delete-orphan",
        order_by="NutritionFood.position",
    )


class NutritionFood(Base):
    __tablename__ = "nutrition_foods"

    __table_args__ = (
        UniqueConstraint(
            "meal_id",
            "position",
            name="uq_nutrition_foods_meal_position",
        ),
        CheckConstraint(
            "position BETWEEN 1 AND 30",
            name="ck_nutrition_foods_position",
        ),
        CheckConstraint(
            "length(trim(name)) >= 2",
            name="ck_nutrition_foods_name",
        ),
        CheckConstraint(
            "length(trim(quantity)) >= 1",
            name="ck_nutrition_foods_quantity",
        ),
    )

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    meal_id = Column(
        Integer,
        ForeignKey(
            "nutrition_meals.id",
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

    quantity = Column(
        String(100),
        nullable=False,
    )

    notes = Column(
        Text,
        nullable=True,
    )

    meal = relationship(
        "NutritionMeal",
        back_populates="foods",
    )