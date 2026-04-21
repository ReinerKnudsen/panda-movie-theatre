from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, func, select

from database import get_session
from models.booking import Booking, BookingCreate, BookingPatch
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


def get_screening(session, id):
    screening = session.get(Screening, id)
    if screening is None:
        raise HTTPException(
            status_code=404,
            detail=f"The screening with id {id} is unknown",
        )
    return screening


def get_available_seats(session, screening_id) -> int:
    screening = session.get(Screening, screening_id)
    if screening is not None:
        screen = session.get(Screen, screening.screen_id)
        if screen is not None:
            avail_seats = screen.capa - screening.bookings
            return avail_seats
        else:
            return 0
    else:
        return 0


@router.get("", status_code=200)
async def get_bookings(session: Session = Depends(get_session)):
    statement = select(Booking)
    bookings = session.exec(statement).all()
    return bookings


@router.get("/{id}", status_code=200)
async def get_booking(id: int, session: Session = Depends(get_session)) -> Booking:
    booking = session.get(Booking, id)
    if booking is not None:
        return booking
    else:
        raise HTTPException(status_code=404, detail=generate_error_message(id))


@router.post("", status_code=201)
async def create_booking(
    booking: BookingCreate, session: Session = Depends(get_session)
) -> Booking:
    # Sind noch ausreichend Sitzplaetze vorhanden
    screening = get_screening(session, booking.screening_id)
    if screening is not None:
        screen = session.get(Screen, screening.screen_id)
        if screen is not None:
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
    return new_booking


@router.patch("/{id}", status_code=200)
async def update_booking(
    id: int, b_patch: BookingPatch, session: Session = Depends(get_session)
) -> Booking:
    booking = session.get(Booking, id)
    if booking is None:
        raise HTTPException(status_code=404, detail=f"Booking with id {id} is unknown")
    screening = get_screening(session, booking.screening_id)
    if screening is None:
        raise HTTPException(
            status_code=404,
            detail=f"Screening with id {booking.screening_id} is unknown",
        )
    screen = session.get(Screen, screening.screen_id)
    if screen is None:
        raise HTTPException(
            status_code=404, detail=f"Screen with id {screening.screen_id} is unknown"
        )
    new_bookings = screening.bookings - booking.seats + b_patch.seats
    if screen.capacity < new_bookings:
        raise HTTPException(
            status_code=400,
            detail=f"Requested number of seats ({b_patch.seats}) is not available",
        )
    screening.sqlmodel_update({"bookings": new_bookings})
    session.add(screening)
    booking_data = b_patch.model_dump(exclude_unset=True)
    booking.sqlmodel_update(booking_data)
    session.add(booking)
    session.commit()
    session.refresh(booking)
    return booking


@router.delete("/{id}", status_code=200)
async def delete_booking(id: int, session: Session = Depends(get_session)) -> Booking:
    booking = session.get(Booking, id)
    if booking is None:
        raise HTTPException(status_code=404, detail=f"Booking with id {id} is unknown")
    screening = session.get(Screening, booking.screening_id)
    if screening is None:
        raise HTTPException(
            status_code=404,
            detail=f"Screening with id {booking.screening_id} is unknown",
        )
    new_bookings = screening.bookings - booking.seats
    screening.sqlmodel_update({"bookings": new_bookings})
    session.add(screening)
    session.delete(booking)
    session.commit()
    return booking
