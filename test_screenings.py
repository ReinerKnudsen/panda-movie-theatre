from datetime import datetime

from fastapi.testclient import TestClient
from sqlmodel import Session

from models.director import Director
from models.movie import Genre, Movie
from models.screen import Floor, Screen
from models.screening import Screening, ScreeningCreate


def create_screening(client: TestClient, session: Session, this_bookings: int = 0):
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
        number=1, floor=Floor.GROUND, capacity=230, available=True, turnaround_min=20
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
        bookings=this_bookings,
    )
    response = client.post("/screenings", json=new_screening.model_dump(mode="json"))
    if response:
        return Screening.model_validate(response.json())


def test_get_screenings(client: TestClient):
    response = client.get("/screenings")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_screening_by_id(client: TestClient, session: Session):
    new_screening = create_screening(client, session)
    assert new_screening is not None
    response = client.get(f"/screenings/{new_screening.id}")
    assert response.status_code == 200
    assert response.json() == new_screening.model_dump(mode="json")


def test_fail_get_non_existing_screening(client: TestClient):
    response = client.get("/screenings/87")
    assert response.status_code == 404
    assert response.json()["detail"] == "Screening with id 87 is unknown"


def test_create_screening(client: TestClient, session: Session):
    new_screening = create_screening(client, session)
    assert isinstance(new_screening, Screening)


def test_update_screening(client: TestClient, session: Session):
    new_screening = create_screening(client, session)
    assert new_screening is not None
    response = client.patch(f"/screenings/{new_screening.id}", json={"bookings": 22})
    assert response.status_code == 200
    assert response.json()["bookings"] == 22


def test_fail_update_non_existing_screening(client: TestClient):
    response = client.patch("/screenings/87", json={"bookings": 22})
    assert response.status_code == 404
    assert response.json()["detail"] == "Screening with id 87 is unknown"


def test_delete_screening(client: TestClient, session: Session):
    del_screening = create_screening(client, session)
    assert del_screening is not None
    response = client.delete(f"/screenings/{del_screening.id}")
    assert response.status_code == 200
    assert response.json() == del_screening.model_dump(mode="json")


def test_fail_delete_non_existing_screening(client: TestClient):
    response = client.delete("/screenings/87")
    assert response.status_code == 404
    assert response.json()["detail"] == "Screening with id 87 is unknown"


def test_delete_screening_with_bookings_fails(client: TestClient, session: Session):
    new_screening = create_screening(client, session, this_bookings=30)
    assert new_screening is not None
    assert new_screening.bookings == 30
    response = client.delete(f"/screenings/{new_screening.id}")
    assert response.status_code == 400
    assert (
        response.json()["detail"]
        == f"There are still 30 bookings for screening {new_screening.id}. \nYou must cancel the bookings before you can delete the screening."
    )
