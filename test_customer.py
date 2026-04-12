from fastapi.testclient import TestClient

from models.customer import Customer, CustomerCreate


def create_customer(client: TestClient):
    new_customer = CustomerCreate(first_name="Roman", last_name="Fresenius")
    response = client.post("/customers", json=new_customer.model_dump(mode="json"))
    if response:
        return Customer.model_validate(response.json())


def test_create_customer(client: TestClient):
    customer = create_customer(client)
    assert customer is not None


def test_get_customers(client: TestClient):
    response = client.get("/customers")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_customer(client: TestClient):
    customer = create_customer(client)
    assert customer is not None
    response = client.get(f"/customers/{customer.id}")
    assert response.status_code == 200
    assert response.json() == customer.model_dump(mode="json")


def test_fail_get_non_existing_customer(client: TestClient):
    response = client.get("/customers/87")
    assert response.status_code == 404
    assert response.json()["detail"] == "Customer with id 87 is unknown"


def test_update_customer(client: TestClient):
    customer = create_customer(client)
    assert customer is not None
    response = client.patch(f"/customers/{customer.id}", json={"last_name": "Changer"})
    assert response.status_code == 200
    assert response.json()["last_name"] == "Changer"


def test_fail_update_non_existing_customer(client: TestClient):
    response = client.patch("/customers/87", json={"last_name": "NonChanger"})
    assert response.status_code == 404
    assert response.json()["detail"] == "Customer with id 87 is unknown"


def test_delete_customer(client: TestClient):
    customer = create_customer(client)
    assert customer is not None
    response = client.delete(f"/customers/{customer.id}")
    assert response.status_code == 200
    assert response.json() == customer.model_dump(mode="json")


def test_fail_delete_non_existing_customer(client: TestClient):
    response = client.delete("/customers/87")
    assert response.status_code == 404
    assert response.json()["detail"] == "Customer with id 87 is unknown"
