from sqlmodel import Session

from models.booking import Booking
from models.screen import Screen
from models.screening import Screening
from utils import generate_booking_code


def create_booking(
    session: Session, screening_id: int, seats: int, customer_id: int | None = None
) -> Booking:

    new_booking = Booking(
        screening_id=screening_id,
        customer_id=customer_id,
        seats=seats,
        booking_code=generate_booking_code(),
    )

    screening = session.get(Screening, screening_id)
    if screening is None:
        raise ValueError("Screening not found")

    screen = session.get(Screen, screening.screen_id)
    if screen is None:
        raise ValueError("Screen not found")

    if screen.capacity < screening.bookings + seats:
        raise ValueError("Insufficient capacity for screen")

    session.add(new_booking)
    session.commit()
    session.refresh(new_booking)

    screening.sqlmodel_update({"bookings": screening.bookings + new_booking.seats})
    session.add(screening)
    session.commit()

    return new_booking


def delete_booking(session: Session, booking_id: int):
    booking = session.get(Booking, booking_id)
    if booking is None:
        raise ValueError("Booking is unknown")

    screening = session.get(Screening, booking.screening_id)
    if screening is None:
        raise ValueError("Screening is unknown")

    new_bookings = screening.bookings - booking.seats

    session.delete(booking)
    screening.sqlmodel_update({"bookings": new_bookings})
    session.add(screening)
    session.commit()
    return booking
