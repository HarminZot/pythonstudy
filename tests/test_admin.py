from app.models import SystemSetting, User
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
