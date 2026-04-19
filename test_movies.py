from fastapi.testclient import TestClient
from sqlmodel import Session

from models.director import Director
from models.movie import Genre, Movie, MovieCreate


def create_movie(client: TestClient, session: Session) -> Movie | None:
    director = Director(first_name="Willem", last_name="Vanderwusel")
    session.add(director)
    session.commit()
    session.refresh(director)
    assert director.id is not None
    new_movie = MovieCreate(
        title="The arrow that flew too far",
        director_id=director.id,
        genre=Genre.DRAMA,
        duration_min=176,
        release_year=2024,
    )
    response = client.post("/movies", json=new_movie.model_dump(mode="json"))
    if response:
        return Movie.model_validate(response.json())


def test_get_all_movies(client: TestClient):
    response = client.get("/movies")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_movie_by_id(client: TestClient, session: Session):
    movie = create_movie(client, session)
    assert movie is not None
    response = client.get("/movies/1")
    assert response.status_code == 200
    assert response.json() == movie.model_dump(mode="json")


def test_try_get_non_existing_movie(client: TestClient):
    response = client.get("/movies/87")
    assert response.status_code == 404
    assert response.json()["detail"] == "Movie with id 87 is unknown."


def test_create_movie(client: TestClient, session: Session):
    movie = create_movie(client, session)
    assert movie is not None


def test_update_movie(client: TestClient, session: Session):
    current_movie = create_movie(client, session)
    assert current_movie is not None
    response = client.patch(f"/movies/{current_movie.id}", json={"duration_min": 190})
    assert response.status_code == 200
    assert response.json()["duration_min"] == 190


def test_try_update_non_existing_movie(client: TestClient):
    response = client.patch("/movies/87", json={"duration_min": 190})
    assert response.status_code == 404
    assert response.json()["detail"] == "Movie with id 87 is unknown."


def test_delete_movie(client: TestClient, session: Session):
    current_movie = create_movie(client, session)
    assert current_movie is not None
    response = client.delete("/movies/1")
    assert response.status_code == 200
    assert response.json() == current_movie.model_dump(mode="json")


def test_try_delete_non_existing_movie(client: TestClient):
    response = client.delete("/movies/87")
    assert response.status_code == 404
    assert response.json()["detail"] == "Movie with id 87 is unknown."
