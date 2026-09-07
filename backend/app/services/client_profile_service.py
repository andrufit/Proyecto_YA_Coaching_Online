from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.body_assessment import BodyAssessment
from app.models.client_profile import ClientProfile
from app.schemas.body_assessment import BodyAssessmentCreate
from app.schemas.client_profile import (
    ClientProfileCreate,
    ClientProfileUpdate,
)


def get_client_profile_by_user_id(
    db: Session,
    user_id: int,
) -> ClientProfile | None:
    statement = select(ClientProfile).where(
        ClientProfile.user_id == user_id
    )
    return db.scalar(statement)


def create_client_profile(
    db: Session,
    user_id: int,
    profile_data: ClientProfileCreate,
) -> ClientProfile:
    profile = ClientProfile(
        user_id=user_id,
        **profile_data.model_dump(),
    )

    db.add(profile)
    db.commit()
    db.refresh(profile)

    return profile


def update_client_profile(
    db: Session,
    profile: ClientProfile,
    profile_data: ClientProfileUpdate,
) -> ClientProfile:
    update_data = profile_data.model_dump(
        exclude_unset=True,
    )

    for field, value in update_data.items():
        setattr(profile, field, value)

    db.commit()
    db.refresh(profile)

    return profile


def create_body_assessment(
    db: Session,
    client_profile_id: int,
    assessment_data: BodyAssessmentCreate,
) -> BodyAssessment:
    assessment = BodyAssessment(
        client_profile_id=client_profile_id,
        **assessment_data.model_dump(),
    )

    db.add(assessment)
    db.commit()
    db.refresh(assessment)

    return assessment


def get_body_assessments(
    db: Session,
    client_profile_id: int,
) -> list[BodyAssessment]:
    statement = (
        select(BodyAssessment)
        .where(
            BodyAssessment.client_profile_id == client_profile_id
        )
        .order_by(
            BodyAssessment.assessment_date.desc(),
            BodyAssessment.id.desc(),
        )
    )

    return list(db.scalars(statement).all())