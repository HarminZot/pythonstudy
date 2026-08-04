import ast


BLOCKED_IMPORTS = {
    "os", "sys", "subprocess", "socket", "pathlib", "shutil", "ctypes", "multiprocessing",
    "resource", "signal", "importlib", "builtins", "inspect", "pickle", "marshal", "webbrowser",
}
BLOCKED_CALLS = {
    "eval", "exec", "compile", "open", "__import__", "globals", "locals", "vars", "dir",
    "getattr", "setattr", "delattr", "breakpoint", "help", "exit", "quit", "input_file",
}
BLOCKED_ATTRIBUTES = {
    "__class__", "__bases__", "__subclasses__", "__globals__", "__code__", "__closure__",
    "__dict__", "__mro__", "__getattribute__",
}


class ValidationError(ValueError):
    pass


def validate_code(code, allowed_imports=None):
    if not code or not code.strip():
        raise ValidationError("Код не может быть пустым.")
    if len(code) > 30000:
        raise ValidationError("Код превышает допустимый размер.")
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        raise ValidationError(f"Синтаксическая ошибка: строка {exc.lineno}: {exc.msg}") from exc

    allowed = set(allowed_imports or [])
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                if root in BLOCKED_IMPORTS or root not in allowed:
                    raise ValidationError(f"Импорт модуля '{root}' не разрешен.")
        elif isinstance(node, ast.ImportFrom):
            root = (node.module or "").split(".")[0]
            if root in BLOCKED_IMPORTS or root not in allowed:
                raise ValidationError(f"Импорт модуля '{root}' не разрешен.")
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in BLOCKED_CALLS:
                raise ValidationError(f"Вызов '{node.func.id}' запрещен.")
        elif isinstance(node, ast.Attribute) and node.attr in BLOCKED_ATTRIBUTES:
            raise ValidationError(f"Доступ к атрибуту '{node.attr}' запрещен.")
    return tree
