from app.extensions import db
from app.models import SystemSetting, User
from .conftest import login


def test_login_success(client):
    response = login(client, "student@test.local", "Student123!")
    assert response.status_code == 200
    assert "Здравствуйте" in response.get_data(as_text=True)


def test_login_accepts_username(client, app):
    with app.app_context():
        user = User.query.filter_by(email="admin@test.local").one()
        user.username = "admin"
        db.session.commit()
    response = login(client, "admin", "Admin123!")
    assert response.status_code == 200
    assert "PythonStudy" in response.get_data(as_text=True)


def test_login_rejects_bad_password(client):
    response = login(client, "student@test.local", "wrong-password")
    assert "Неверная" in response.get_data(as_text=True)


def test_registration(client, app):
    response = client.post("/auth/register", data={
        "last_name": "Сидоров",
        "first_name": "Петр",
        "middle_name": "",
        "email": "new@example.com",
        "password": "Password123!",
        "password_repeat": "Password123!",
    }, follow_redirects=True)
    assert response.status_code == 200
    with app.app_context():
        assert User.query.filter_by(email="new@example.com").first() is not None


def test_blocked_user_cannot_login(client, app):
    with app.app_context():
        user = User.query.filter_by(email="student@test.local").first()
        user.status = "blocked"
        from app.extensions import db
        db.session.commit()
    response = login(client, "student@test.local", "Student123!")
    assert "заблокирована" in response.get_data(as_text=True)


def test_login_rejects_external_next_redirect(client):
    response = client.post(
        "/auth/login?next=https://example.com/phishing",
        data={"email": "student@test.local", "password": "Student123!"},
    )
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/student/dashboard")


def test_registration_can_be_disabled(client, app):
    with app.app_context():
        db.session.add(SystemSetting(setting_key="registration_enabled", setting_value="false", value_type="boolean", group_name="registration"))
        db.session.commit()
    response = client.get("/auth/register")
    assert response.status_code == 403
    assert "приостановлена" in response.get_data(as_text=True)
