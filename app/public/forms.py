from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField
from wtforms import SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, Length


class FeedbackForm(FlaskForm):
    email = StringField("Электронная почта", validators=[DataRequired(), Email(), Length(max=255)])
    category = SelectField("Категория", choices=[
        ("technical_problem", "Техническая проблема"),
        ("task_error", "Ошибка в задании"),
        ("course_question", "Вопрос по курсу"),
        ("suggestion", "Предложение"),
        ("other", "Другое"),
    ])
    subject = StringField("Тема", validators=[DataRequired(), Length(max=255)])
    message = TextAreaField("Сообщение", validators=[DataRequired(), Length(min=10, max=5000)])
    attachment = FileField("Вложение", validators=[FileAllowed(["pdf", "docx", "xlsx", "txt", "png", "jpg", "jpeg", "zip"])])
    submit = SubmitField("Отправить")
