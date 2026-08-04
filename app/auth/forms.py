from flask_wtf import FlaskForm
from wtforms import BooleanField, PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length


class LoginForm(FlaskForm):
    email = StringField("Электронная почта", validators=[DataRequired(), Email()])
    password = PasswordField("Пароль", validators=[DataRequired()])
    remember = BooleanField("Запомнить меня")
    submit = SubmitField("Войти")


class RegisterForm(FlaskForm):
    last_name = StringField("Фамилия", validators=[DataRequired(), Length(max=100)])
    first_name = StringField("Имя", validators=[DataRequired(), Length(max=100)])
    middle_name = StringField("Отчество", validators=[Length(max=100)])
    email = StringField("Электронная почта", validators=[DataRequired(), Email(), Length(max=255)])
    password = PasswordField("Пароль", validators=[DataRequired(), Length(min=8, max=128)])
    password_repeat = PasswordField("Повторите пароль", validators=[DataRequired(), EqualTo("password")])
    submit = SubmitField("Зарегистрироваться")


class ForgotPasswordForm(FlaskForm):
    email = StringField("Электронная почта", validators=[DataRequired(), Email()])
    submit = SubmitField("Получить ссылку")


class ResetPasswordForm(FlaskForm):
    password = PasswordField("Новый пароль", validators=[DataRequired(), Length(min=8, max=128)])
    password_repeat = PasswordField("Повторите пароль", validators=[DataRequired(), EqualTo("password")])
    submit = SubmitField("Сохранить пароль")
