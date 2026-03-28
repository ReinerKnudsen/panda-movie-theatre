from fastapi.testclient import TestClient
from models.director import DirectorCreate

new_director = DirectorCreate(
    first_name="Raymond", last_name="Bullinger", birth_year=1954
)


def create_director(client: TestClient):
    response = client.post("/directors", json=new_director.model_dump(mode="json"))
    if response.status_code == 201:
        return True
    else:
        return False


def test_get_all_directors(client: TestClient):
    if create_director(client) is not None:
        response = client.get("/directors")
        assert response.status_code == 200
        assert isinstance(response.json(), list)


def test_get_director_by_id(client: TestClient):
    assert create_director(client)
    response = client.get("/directors/1")
    assert response.status_code == 200
    assert response.json()["id"] == 1
    assert response.json()["last_name"] == "Bullinger"


def test_try_get_director_with_wrong_id(client: TestClient):
    response = client.get("/directors/188")
    assert response.status_code == 404
    assert response.json()["detail"] == "Director with id 188 is unknown"


def test_create_director(client: TestClient):
    response = client.post("/directors", json=new_director.model_dump(mode="json"))
    assert response.status_code == 201
    assert response.json()["first_name"] == "Raymond"
    assert response.json()["id"] is not None


def test_delete_director(client: TestClient):
    assert create_director(client)
    response = client.delete("/directors/1")
    assert response.status_code == 200
    assert response.json()["id"] == 1
    assert response.json()["last_name"] == "Bullinger"


def test_try_delete_director_with_wrong_id(client: TestClient):
    response = client.delete("/directors/188")
    assert response.status_code == 404
    assert response.json()["detail"] == "Director with id 188 is unknown"


def test_update_existing_director(client: TestClient):
    assert create_director(client)
    response = client.patch("/directors/1", json={"birth_year": 1967})
    assert response.status_code == 200
    assert response.json()["birth_year"] == 1967


def test_try_update_director_with_wrong_id(client: TestClient):
    response = client.patch("/directors/188", json={"birth_year": 2024})
    assert response.status_code == 404
    assert response.json()["detail"] == "Director with id 188 is unknown"
