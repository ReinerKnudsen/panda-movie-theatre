from fastapi.testclient import TestClient

from models.director import Director


def create_director(client: TestClient) -> Director | None:
    response = client.post(
        "/directors",
        json={"first_name": "Raymond", "last_name": "Bullinger", "birth_year": 1954},
    )
    if response:
        return Director.model_validate(response.json())


def test_get_all_directors(client: TestClient):
    response = client.get("/directors")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_director_by_id(client: TestClient):
    director = create_director(client)
    assert director is not None
    response = client.get(f"/directors/{director.id}")
    assert response.status_code == 200
    assert response.json()["last_name"] == "Bullinger"


def test_try_get_director_with_wrong_id(client: TestClient):
    response = client.get("/directors/87")
    assert response.status_code == 404
    assert response.json()["detail"] == "Director with id 87 is unknown"


def test_create_director(client: TestClient):
    new_director = create_director(client)
    assert new_director is not None


def test_delete_director(client: TestClient):
    director = create_director(client)
    assert director is not None
    response = client.delete(f"/directors/{director.id}")
    assert response.status_code == 200
    assert response.json()["last_name"] == "Bullinger"


def test_try_delete_director_with_wrong_id(client: TestClient):
    response = client.delete("/directors/87")
    assert response.status_code == 404
    assert response.json()["detail"] == "Director with id 87 is unknown"


def test_update_existing_director(client: TestClient):
    new_director = create_director(client)
    assert new_director is not None
    response = client.patch(f"/directors/{new_director.id}", json={"birth_year": 1967})
    assert response.status_code == 200
    assert response.json()["birth_year"] == 1967


def test_try_update_director_with_wrong_id(client: TestClient):
    response = client.patch("/directors/87", json={"birth_year": 2024})
    assert response.status_code == 404
    assert response.json()["detail"] == "Director with id 87 is unknown"
