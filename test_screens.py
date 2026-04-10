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
    new_screen = create_screen(client)
    assert new_screen is not None
    response = client.get("/screens/1")
    assert response.status_code == 200
    assert response.json() == new_screen.model_dump(mode="json")


def test_fail_get_screen_by_id(client: TestClient):
    response = client.get("/screens/17")
    assert response.status_code == 404


def test_create_new_screen(client: TestClient):
    another_screen = ScreenCreate(
        number=2, floor=Floor.FIRST, capacity=200, available=True, turnaround_min=10
    )
    result_screen = Screen(
        id=1,
        number=2,
        floor=Floor.FIRST,
        capacity=200,
        available=True,
        turnaround_min=10,
    )
    response = client.post("/screens", json=another_screen.model_dump(mode="json"))
    assert response.status_code == 201
    assert response.json() == result_screen.model_dump(mode="json")


def test_update_screen(client: TestClient):
    new_screen = create_screen(client)
    assert new_screen is not None
    response = client.patch("/screens/1", json={"capacity": 230})
    assert response.status_code == 200
    assert response.json()["capacity"] == 230
