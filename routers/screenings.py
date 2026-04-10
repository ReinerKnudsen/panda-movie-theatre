from datetime import datetime

from database import get_session
from models.screening import Screening, ScreeningCreate, ScreeningPatch
from sqlmodel import Session, select

from fastapi import APIRouter, Depends, HTTPException

router = APIRouter(prefix="/screenings", tags=["screenings"])


def create_error_message(id: int):
    return f"Screening with id {id} is unknown"


@router.get("", status_code=200)
async def get_all_screenings(session: Session = Depends(get_session)):
    statement = select(Screening)
    screenings = session.exec(statement).all()
    return screenings


@router.get("/{id}", status_code=200)
async def get_screening_by_id(
    id: int, session: Session = Depends(get_session)
) -> Screening:
    screening = session.get(Screening, id)
    if screening is not None:
        return screening
    else:
        raise HTTPException(status_code=404, detail=create_error_message(id))


@router.post("", status_code=201)
async def create_screening(
    screening: ScreeningCreate, session: Session = Depends(get_session)
) -> Screening:
    new_screening = Screening.model_validate(screening)
    session.add(new_screening)
    session.commit()
    session.refresh(new_screening)
    return new_screening


@router.patch("/{id}", status_code=200)
async def update_screening(
    id: int, screening: ScreeningPatch, session: Session = Depends(get_session)
) -> Screening:
    existing_screening = session.get(Screening, id)
    if existing_screening is not None:
        screening_data = screening.model_dump(exclude_unset=True)
        existing_screening.sqlmodel_update(screening_data)
        session.add(existing_screening)
        session.commit()
        session.refresh(existing_screening)
        return existing_screening
    else:
        raise HTTPException(status_code=404, detail=create_error_message(id))


@router.delete("/{id}", status_code=200)
async def delete_screening(
    id: int, session: Session = Depends(get_session)
) -> Screening:
    screening = session.get(Screening, id)
    if screening is not None:
        if screening.bookings > 0 and screening.screen_time > datetime.now():
            raise HTTPException(
                status_code=400,
                detail=f"There are still {screening.bookings} bookings for screening {id}. \nYou must cancel the bookings before you can delete the screening.",
            )
        else:
            session.delete(screening)
            session.commit()
            return screening
    else:
        raise HTTPException(status_code=404, detail=create_error_message(id))
