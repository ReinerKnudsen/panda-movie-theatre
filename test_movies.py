from fastapi.testclient import TestClient
from models.director import DirectorCreate
from models.movie import Genre, Movie, MovieCreate, MoviePatch


def create_new_movie(client: TestClient) -> Movie | None:

    new_movie = MovieCreate(
        title="The arrow that flew too far",
        director_id=1,
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


def test_get_movie_by_id(client: TestClient):
    new_movie = create_new_movie(client)
    assert new_movie is not None
    response = client.get("/movies/1")
    assert response.status_code == 200
    assert response.json() == new_movie.model_dump(mode="json")


another_movie = MovieCreate(
    title="Slow Motion Life Suport",
    director_id=2,
    genre=Genre.ROMANCE,
    release_year=2003,
    duration_min=129,
)

result_movie = Movie(
    id=1,
    title="Slow Motion Life Suport",
    director_id=2,
    genre=Genre.ROMANCE,
    release_year=2003,
    duration_min=129,
)


def test_create_movie(client: TestClient):
    response = client.post("/movies", json=another_movie.model_dump(mode="json"))
    assert response.status_code == 201
    assert response.json() == result_movie.model_dump(mode="json")


update_director = DirectorCreate(
    first_name="Ralph", last_name="Overbarley", birth_year=1963
)

update_movie = MoviePatch(
    title="The arrow that flew too far", genre=Genre.COMEDY, duration_min=190
)


def test_update_movie(client: TestClient):
    current_movie = create_new_movie(client)
    assert current_movie is not None
    response = client.put("/movies/1", json=update_movie.model_dump(mode="json"))
    assert response.status_code == 200
    assert response.json()["genre"] == "comedy"
    assert response.json()["duration_min"] == 190


def test_delete_movie(client: TestClient):
    current_movie = create_new_movie(client)
    assert current_movie is not None
    response = client.delete("/movies/1")
    assert response.status_code == 200
    assert response.json() == current_movie.model_dump(mode="json")
