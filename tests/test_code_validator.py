import pytest

from app.services.code_validator import ValidationError, validate_code


def test_accepts_basic_python():
    validate_code("value = int(input())\nprint(value * 2)")


def test_rejects_os_import():
    with pytest.raises(ValidationError):
        validate_code("import os")


def test_rejects_open_call():
    with pytest.raises(ValidationError):
        validate_code("open('secret.txt')")


def test_rejects_dunder_introspection():
    with pytest.raises(ValidationError):
        validate_code("print(int.__subclasses__())")
