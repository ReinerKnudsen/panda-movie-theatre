from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, func, select

from database import get_session
from models.booking import Booking, BookingCreate
from models.screen import Screen
from models.screening import Screening

router = APIRouter(prefix="/bookings", tags=["bookings"])


def generate_error_message(id: int):
    return f"Booking with id {id} is unknown"


def generate_booking_code(session):
    today = date.today()
    count = session.exec(
        select(func.count()).where(
            Booking.booking_code.startswith(f"PMT-{today.strftime('%Y%m%d')}")
        )
    ).one()
    code = f"PMT-{today.strftime('%Y%m%d')}-{count + 1:04d}"
    return code


@router.get("", status_code=200)
async def get_bookings(session: Session = Depends(get_session)):
    statement = select(Booking)
    bookings = session.exec(statement).all()
    return bookings


@router.get("{id}", status_code=200)
async def get_booking(id: int, session: Session = Depends(get_session)):
    booking = session.get(Booking, id)
    if booking is not None:
        return booking
    else:
        raise HTTPException(status_code=404, detail=generate_error_message(id))


@router.post("", status_code=201)
async def create_booking(
    booking: BookingCreate, session: Session = Depends(get_session)
):
    # Sind noch ausreichend Sitzplaetze vorhanden
    screening = session.get(Screening, booking.screening_id)
    if screening is None:
        raise HTTPException(
            status_code=404,
            detail=f"The screening with id {booking.screening_id} is unknown",
        )

    screen = session.get(Screen, screening.screen_id)
    if screen is None:
        raise HTTPException(
            status_code=404,
            detail=f"Screening with id {booking.screening_id} refers to an unknown screen",
        )

    if screen.capacity < screening.bookings + booking.seats:
        raise HTTPException(
            status_code=400,
            detail=f"Requested number of seats ({booking.seats}) is not available)",
        )

    # Booking Code einbauen
    booking_data = booking.model_dump()
    booking_data["booking_code"] = generate_booking_code(session)
    new_booking = Booking(**booking_data)

    session.add(new_booking)
    session.commit()
    session.refresh(new_booking)

    # Buchungsanzahl im Screening erhöhen
    screening.sqlmodel_update({"bookings": screening.bookings + booking.seats})
    session.add(screening)
    session.commit()
    session.refresh(new_booking)
    return new_booking
