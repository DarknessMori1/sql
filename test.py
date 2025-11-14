import requests

BASE_URL = "http://localhost:8000"

def test_sorted_products():
    """Тест для эндпоинта сортировки"""
    try:
        response = requests.get(f"{BASE_URL}/products/sort/price")
        assert response.status_code == 200, f"Ожидался статус 200, получен {response.status_code}"
        data = response.json()
        assert isinstance(data, list), "Ответ должен быть списком"
        print("✓ test_sorted_products passed")
        return True
    except Exception as e:
        print(f"✗ test_sorted_products failed: {e}")
        return False

def test_invalid_sort_type():
    """Тест на невалидный тип сортировки"""
    try:
        response = requests.get(f"{BASE_URL}/products/sort/invalid_sort")
        assert response.status_code == 400, f"Ожидался статус 400, получен {response.status_code}"
        print("✓ test_invalid_sort_type passed")
        return True
    except Exception as e:
        print(f"✗ test_invalid_sort_type failed: {e}")
        return False

if __name__ == "__main__":
    print("Запуск тестов...")
    
    results = []
    results.append(test_sorted_products())
    results.append(test_invalid_sort_type())
    
    print()
    if all(results):
        print("🎉 Все тесты прошли успешно!")
    else:
        print("❌ Некоторые тесты не прошли")
        