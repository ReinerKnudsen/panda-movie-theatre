from datetime import datetime

from fastapi.testclient import TestClient
from sqlmodel import Session

from models.booking import Booking, BookingCreate
from models.director import Director
from models.movie import Genre, Movie
from models.screen import Floor, Screen
from models.screening import Screening, ScreeningCreate


def create_screening(
    client: TestClient, session: Session, bookings: int = 0, capacity: int = 100
):
    director: Director = Director(
        first_name="Francis", last_name="Forgiveme", birth_year=1967
    )
    session.add(director)
    session.flush()
    assert director.id is not None

    movie = Movie(
        title="On good terms with defaults",
        genre=Genre.ROMANCE,
        duration_min=192,
        director_id=director.id,
        description="As long as it is default, his life is easy. But then comes Polly",
        release_year=1999,
    )
    screen: Screen = Screen(
        number=1,
        floor=Floor.GROUND,
        capacity=capacity,
        available=True,
        turnaround_min=20,
    )
    session.add(movie)
    session.add(screen)
    session.flush()
    assert movie.id is not None
    assert screen.id is not None
    session.commit()

    new_screening = ScreeningCreate(
        movie_id=movie.id,
        screen_id=screen.id,
        screen_time=datetime(2026, 7, 30, 18, 00),
        bookings=bookings,
    )
    response = client.post("/screenings", json=new_screening.model_dump(mode="json"))
    if response:
        return Screening.model_validate(response.json())


def create_booking(
    client: TestClient,
    session: Session,
    screening_ident: int | None = None,
    c_id=None,
    seats: int = 2,
):
    if screening_ident is None:
        screening = create_screening(client, session)
        assert screening is not None
        screening_ident = screening.id
    if screening_ident is not None:
        booking = BookingCreate(
            screening_id=screening_ident, customer_id=c_id, seats=seats
        )
        response = client.post("/bookings", json=booking.model_dump(mode="json"))
        assert response is not None
        return Booking.model_validate(response.json())


def test_get_bookings(client: TestClient):
    response = client.get("/bookings")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_booking(client: TestClient, session: Session):
    booking = create_booking(client, session)
    assert booking is not None
    response = client.get(f"/bookings/{booking.id}")
    assert response.status_code == 200
    assert response.json() == booking.model_dump(mode="json")


def test_fail_get_non_existing_booking(client: TestClient):
    response = client.get("/bookings/87")
    assert response.status_code == 404
    assert response.json()["detail"] == "Booking with id 87 is unknown"


def test_create_booking(client: TestClient, session: Session):
    booking = create_booking(client, session)
    assert booking is not None


def test_fail_create_booking_with_too_few_seats(client: TestClient, session: Session):
    screening = create_screening(client, session, capacity=20)
    assert screening is not None

    booking = BookingCreate(screening_id=screening.id, customer_id=None, seats=30)
    response = client.post("/bookings", json=booking.model_dump(mode="json"))
    assert response.status_code == 400
    assert (
        response.json()["detail"] == "Requested number of seats (30) is not available)"
    )


def test_fail_create_booking_with_wrong_screening(client: TestClient):
    booking = BookingCreate(screening_id=87, customer_id=None, seats=30)
    response = client.post("/bookings", json=booking.model_dump())
    assert response.status_code == 404
    assert response.json()["detail"] == "The screening with id 87 is unknown"


def test_update_booking(client: TestClient, session: Session):
    booking = create_booking(client, session)
    assert booking is not None
    response = client.patch(f"/bookings/{booking.id}", json={"seats": 5})
    assert response.status_code == 200
    assert response.json()["seats"] == 5
    # Did the screening update correctly?
    screening = session.get(Screening, booking.screening_id)
    assert screening is not None
    assert screening.model_dump(mode="json")["bookings"] == 5


def test_fail_update_booking_with_too_many_seats(client: TestClient, session: Session):
    screening = create_screening(client, session, bookings=96, capacity=100)
    assert screening is not None
    booking = create_booking(client, session, screening_ident=screening.id, seats=2)
    assert booking is not None

    response = client.patch(f"/bookings/{booking.id}", json={"seats": 10})
    assert response.status_code == 400
    assert (
        response.json()["detail"] == "Requested number of seats (10) is not available"
    )


def test_delete_booking(client: TestClient, session: Session):
    booking = create_booking(client, session)
    assert booking is not None

    response = client.delete(f"/bookings/{booking.id}")
    assert response.status_code == 200
    assert response.json() == booking.model_dump(mode="json")


def test_fail_delete_non_existing_booking(client: TestClient):
    response = client.delete("/bookings/87")
    assert response.status_code == 404
    assert response.json()["detail"] == "Booking with id 87 is unknown"
