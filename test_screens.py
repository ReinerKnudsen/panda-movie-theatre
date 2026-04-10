from fastapi.testclient import TestClient

from models.screen import Floor, Screen, ScreenCreate


def create_screen(client: TestClient) -> Screen | None:
    new_screen = ScreenCreate(
        number=1, floor=Floor.GROUND, capacity=180, available=True, turnaround_min=20
    )
    response = client.post("/screens", json=new_screen.model_dump(mode="json"))
    if response:
        return Screen.model_validate(response.json())


def test_get_all_screens(client: TestClient):
    response = client.get("/screens")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_screen_by_id(client: TestClient):
    screen = create_screen(client)
    assert screen is not None
    response = client.get(f"/screens/{screen.id}")
    assert response.status_code == 200
    assert response.json() == screen.model_dump(mode="json")


def test_fail_get_screen_by_id(client: TestClient):
    response = client.get("/screens/87")
    assert response.status_code == 404
    assert response.json()["detail"] == "Screen with id 87 is unknown"


def test_create_new_screen(client: TestClient):
    screen = create_screen(client)
    assert screen is not None


def test_update_screen(client: TestClient):
    screen = create_screen(client)
    assert screen is not None
    response = client.patch(f"/screens/{screen.id}", json={"capacity": 230})
    assert response.status_code == 200
    assert response.json()["capacity"] == 230


def test_fail_update_non_existing_screen(client: TestClient):
    response = client.patch("/screens/87", json={"capacity": 230})
    assert response.status_code == 404
    assert response.json()["detail"] == "Screen with id 87 is unknown"


def test_delete_screen(client: TestClient):
    screen = create_screen(client)
    assert screen is not None
    response = client.delete(f"/screens/{screen.id}")
    assert response.status_code == 200
    assert response.json() == screen.model_dump(mode="json")


def test_fail_delete_non_existing_screen(client: TestClient):
    response = client.delete("/screens/87")
    assert response.status_code == 404
    assert response.json()["detail"] == "Screen with id 87 is unknown"
