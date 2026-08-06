import hashlib
import uuid
from pathlib import Path

from flask import current_app
from werkzeug.utils import secure_filename

from ..constants import ALLOWED_UPLOAD_EXTENSIONS
from ..extensions import db
from ..models import UploadedFile


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_UPLOAD_EXTENSIONS


def save_upload(file_storage, owner_id, category):
    if not file_storage or not file_storage.filename:
        return None
    if not allowed_file(file_storage.filename):
        raise ValueError("Недопустимое расширение файла.")
    original = secure_filename(file_storage.filename) or "file"
    extension = original.rsplit(".", 1)[1].lower()
    stored = f"{uuid.uuid4().hex}.{extension}"
    category_dir = Path(current_app.config["UPLOAD_ROOT"]) / category
    category_dir.mkdir(parents=True, exist_ok=True)
    path = category_dir / stored
    file_storage.save(path)
    data = path.read_bytes()
    record = UploadedFile(
        owner_id=owner_id,
        original_name=original,
        stored_name=stored,
        storage_path=str(path),
        mime_type=file_storage.mimetype or "application/octet-stream",
        size_bytes=len(data),
        checksum=hashlib.sha256(data).hexdigest(),
        category=category,
    )
    db.session.add(record)
    return record


def remove_upload(record):
    """Помечает загрузку удаленной и удаляет только файл внутри каталога загрузок."""
    upload_root = Path(current_app.config["UPLOAD_ROOT"]).resolve()
    stored_path = Path(record.storage_path).resolve()
    if stored_path.is_relative_to(upload_root) and stored_path.is_file():
        stored_path.unlink()
    record.is_deleted = True
    return record
