def test_index_available(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "PythonStudy" in response.get_data(as_text=True)


def test_course_catalog(client):
    response = client.get("/courses")
    assert response.status_code == 200
    assert "Тестовый курс" in response.get_data(as_text=True)


def test_course_detail(client):
    response = client.get("/courses/test-course")
    assert response.status_code == 200
    assert "Модуль 1" in response.get_data(as_text=True)


def test_help_page(client):
    response = client.get("/help")
    assert response.status_code == 200
    assert "Справка по системе" in response.get_data(as_text=True)


def test_course_catalog_search(client):
    response = client.get("/courses?q=Тестовый")
    assert response.status_code == 200
    assert "Тестовый курс" in response.get_data(as_text=True)

    response = client.get("/courses?q=несуществующий")
    assert "По заданным условиям курсы не найдены" in response.get_data(as_text=True)
