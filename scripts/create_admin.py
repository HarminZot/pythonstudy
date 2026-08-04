import getpass

from app import create_app
from app.extensions import db
from app.models import Role, User


def main():
    app = create_app()
    with app.app_context():
        role = Role.query.filter_by(code="admin").first()
        if not role:
            role = Role(code="admin", name="Администратор")
            db.session.add(role)
            db.session.flush()
        email = input("Email: ").strip().lower()
        first_name = input("Имя: ").strip()
        last_name = input("Фамилия: ").strip()
        password = getpass.getpass("Пароль: ")
        if User.query.filter_by(email=email).first():
            raise SystemExit("Пользователь уже существует.")
        user = User(role=role, email=email, first_name=first_name, last_name=last_name)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        print("Администратор создан.")


if __name__ == "__main__":
    main()
