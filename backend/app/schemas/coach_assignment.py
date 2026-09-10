from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CoachAssignmentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    coach_id: int = Field(gt=0)


class CoachAssignmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    client_id: int
    coach_id: int
    created_at: datetime
    updated_at: datetime