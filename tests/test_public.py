def test_index_available(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "PythonStudy" in response.get_data(as_text=True)


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


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


def test_course_catalog_filters(client):
    response = client.get("/courses?difficulty=beginner&teacher=2&sort=popular")
    assert response.status_code == 200
    assert "Тестовый курс" in response.get_data(as_text=True)

    response = client.get("/courses?difficulty=advanced")
    assert "По заданным условиям курсы не найдены" in response.get_data(as_text=True)


def test_course_cover_is_served(client, app, tmp_path):
    cover = tmp_path / "cover.png"
    cover.write_bytes(b"course-cover")
    with app.app_context():
        course = Course.query.filter_by(slug="test-course").first()
        course.cover_path = str(cover)
        db.session.commit()
        course_id = course.id

    response = client.get(f"/courses/{course_id}/cover")
    assert response.status_code == 200
    assert response.data == b"course-cover"
from app.extensions import db
from app.models import Course, FeedbackRequest
from .conftest import login


def test_user_sees_only_own_feedback_history(client, app):
    with app.app_context():
        db.session.add_all([
            FeedbackRequest(user_id=1, email="student@test.local", category="technical", subject="Мой вопрос", message="Нужна помощь"),
            FeedbackRequest(user_id=2, email="teacher@test.local", category="other", subject="Чужой вопрос", message="Другой текст"),
        ])
        db.session.commit()
    login(client, "student@test.local", "Student123!")
    response = client.get("/feedback/history")
    body = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "Мой вопрос" in body
    assert "Чужой вопрос" not in body
