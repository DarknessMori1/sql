from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_sorted_products():
    response = client.get("/products/sort/price")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_invalid_sort_type():
    response = client.get("/products/sort/invalid_sort")
    assert response.status_code == 400

# bash: pytest test.py