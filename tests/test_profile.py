from io import BytesIO

from app.models import UploadedFile, User

from .conftest import login


def test_user_uploads_and_opens_avatar(client, app):
    login(client, "student@test.local", "Student123!")
    response = client.post(
        "/student/profile",
        data={"last_name": "Иванов", "first_name": "Иван", "avatar": (BytesIO(b"avatar-image"), "portrait.png")},
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    assert response.status_code == 200
    with app.app_context():
        user = User.query.filter_by(email="student@test.local").one()
        assert user.avatar_path
        assert UploadedFile.query.filter_by(owner_id=user.id, category="avatars").count() == 1
        user_id = user.id
    response = client.get(f"/student/users/{user_id}/avatar")
    assert response.status_code == 200
    assert response.data == b"avatar-image"
