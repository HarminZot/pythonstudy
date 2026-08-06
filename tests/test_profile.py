from io import BytesIO

from app.extensions import db
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


def test_user_deletes_own_avatar_file(client, app):
    login(client, "student@test.local", "Student123!")
    client.post(
        "/student/profile",
        data={"last_name": "Иванов", "first_name": "Иван", "avatar": (BytesIO(b"temporary-avatar"), "temporary.jpg")},
        content_type="multipart/form-data",
    )
    with app.app_context():
        uploaded = UploadedFile.query.filter_by(owner_id=1, category="avatars").one()
        file_id = uploaded.id
    response = client.post(f"/files/{file_id}/delete", follow_redirects=True)
    assert response.status_code == 200
    with app.app_context():
        uploaded = db.session.get(UploadedFile, file_id)
        user = db.session.get(User, 1)
        assert uploaded.is_deleted is True
        assert user.avatar_path is None
