# Развертывание на PythonAnywhere

Проект подготовлен для классического WSGI-приложения PythonAnywhere с Python 3.12 и SQLite.

## 1. Клонирование и окружение

В Bash-консоли PythonAnywhere:

```bash
cd ~
git clone https://github.com/HarminZot/pythonstudy.git
cd pythonstudy
python3.12 -m venv ~/.virtualenvs/pythonstudy
source ~/.virtualenvs/pythonstudy/bin/activate
pip install -r requirements-pythonanywhere.txt
```

## 2. Конфигурация

```bash
cp .env.pythonanywhere.example .env
```

В `.env` замените `USERNAME` на имя аккаунта PythonAnywhere и обязательно задайте случайный `SECRET_KEY`.

```bash
python scripts/bootstrap_pythonanywhere.py
flask --app run.py db upgrade
```

Bootstrap не перезаписывает существующую рабочую базу. При первом запуске он копирует готовую тестовую базу из `data/pythonstudy.db` в `/home/USERNAME/pythonstudy-data`.

## 3. Настройка Web

В разделе **Web**:

1. Создайте приложение через **Manual configuration**.
2. Выберите Python 3.12.
3. Укажите source code и working directory: `/home/USERNAME/pythonstudy`.
4. Укажите virtualenv: `/home/USERNAME/.virtualenvs/pythonstudy`.
5. Скопируйте содержимое `deploy/pythonanywhere_wsgi.py` в системный WSGI-файл из раздела Web.
6. Добавьте static mapping: `/static/` → `/home/USERNAME/pythonstudy/app/static`.
7. Нажмите **Reload**.

Проверка доступности: `https://USERNAME.pythonanywhere.com/health` должна вернуть `{"status":"ok"}`.

## 4. Тестовые учетные записи

| Роль | Логин | Пароль |
|---|---|---|
| Администратор | `admin` | `admin` |
| Преподаватель | `teacher` | `teacher` |
| Студент | `student` | `student` |

Эти пароли предназначены только для демонстрации. Перед реальной публикацией измените их через панель администратора.

## 5. Обновление проекта

```bash
cd ~/pythonstudy
git pull
source ~/.virtualenvs/pythonstudy/bin/activate
pip install -r requirements-pythonanywhere.txt
flask --app run.py db upgrade
```

После обновления нажмите **Reload** в разделе Web. Рабочая база и загрузки находятся вне Git-репозитория и не перезаписываются.

## Выполнение пользовательского кода

Редактор работает синхронно с коротким тайм-аутом. Если тариф или ограничения PythonAnywhere не позволяют запускать subprocess, задайте `CODE_EXECUTION_ENABLED=false`; интерфейс останется доступен, а API вернет понятное сообщение о временном отключении проверки.
