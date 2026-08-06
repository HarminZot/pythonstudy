from app.extensions import db
from app.models import Course, SystemSetting, User
from .conftest import login


def test_admin_dashboard(client):
    login(client, "admin@test.local", "Admin123!")
    response = client.get("/admin/")
    assert response.status_code == 200
    assert "Управление PythonStudy" in response.get_data(as_text=True)


def test_admin_blocks_user(client, app):
    login(client, "admin@test.local", "Admin123!")
    response = client.post("/admin/users/1", data={
        "last_name": "Иванов",
        "first_name": "Иван",
        "role_code": "student",
        "status": "blocked",
    }, follow_redirects=True)
    assert response.status_code == 200
    with app.app_context():
        assert User.query.get(1).status == "blocked"


def test_admin_initializes_settings(client, app):
    login(client, "admin@test.local", "Admin123!")
    response = client.get("/admin/settings")
    assert response.status_code == 200
    with app.app_context():
        assert SystemSetting.query.count() >= 5


def test_admin_creates_user(client, app):
    login(client, "admin@test.local", "Admin123!")
    response = client.post(
        "/admin/users/create",
        data={"email": "new.student@test.local", "first_name": "Новый", "last_name": "Студент", "role_code": "student", "status": "active", "password": "Temporary123!"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    with app.app_context():
        user = User.query.filter_by(email="new.student@test.local").one()
        assert user.has_role("student")
        assert user.check_password("Temporary123!")


def test_admin_changes_course_status(client, app):
    login(client, "admin@test.local", "Admin123!")
    response = client.post("/admin/courses/1/status", data={"status": "archived"}, follow_redirects=True)
    assert response.status_code == 200
    with app.app_context():
        assert db.session.get(Course, 1).status == "archived"
