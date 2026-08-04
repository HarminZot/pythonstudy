import ast
import re
from pathlib import Path

from jinja2 import Environment

ROOT = Path(__file__).resolve().parents[1]


def verify_python():
    count = 0
    for path in ROOT.rglob("*.py"):
        if ".venv" in path.parts:
            continue
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        count += 1
    return count


def verify_templates():
    environment = Environment()
    count = 0
    for path in (ROOT / "app" / "templates").rglob("*.html"):
        environment.parse(path.read_text(encoding="utf-8"))
        count += 1
    return count


def collect_endpoints():
    endpoints = {"static"}
    for blueprint in ("auth", "public", "student", "teacher", "admin", "api"):
        path = ROOT / "app" / blueprint / "routes.py"
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in tree.body:
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            has_route = any(
                isinstance(decorator, ast.Call)
                and isinstance(decorator.func, ast.Attribute)
                and decorator.func.attr == "route"
                for decorator in node.decorator_list
            )
            if has_route:
                endpoints.add(f"{blueprint}.{node.name}")
    return endpoints


def verify_template_endpoints(endpoints):
    pattern = re.compile(r"url_for\(['\"]([^'\"]+)")
    missing = set()
    for path in (ROOT / "app" / "templates").rglob("*.html"):
        for endpoint in pattern.findall(path.read_text(encoding="utf-8")):
            if endpoint not in endpoints:
                missing.add(endpoint)
    if missing:
        raise RuntimeError(f"Не найдены endpoint: {sorted(missing)}")


def count_tables():
    tables = []
    for path in (ROOT / "app" / "models").glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in tree.body:
            if not isinstance(node, ast.ClassDef):
                continue
            for statement in node.body:
                if isinstance(statement, ast.Assign) and any(
                    isinstance(target, ast.Name) and target.id == "__tablename__"
                    for target in statement.targets
                ):
                    tables.append(ast.literal_eval(statement.value))
    return tables


def logical_lines():
    total = 0
    for path in ROOT.rglob("*"):
        if path.suffix not in {".py", ".html", ".css", ".js"} or not path.is_file():
            continue
        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            stripped = line.strip()
            if stripped and not stripped.startswith(("#", "//", "<!--")):
                total += 1
    return total


def main():
    python_files = verify_python()
    templates = verify_templates()
    endpoints = collect_endpoints()
    verify_template_endpoints(endpoints)
    tables = count_tables()
    lines = logical_lines()
    assert len(tables) == 26, f"Ожидалось 26 таблиц, найдено {len(tables)}"
    assert len(endpoints) >= 50, f"Слишком мало маршрутов: {len(endpoints)}"
    assert templates >= 10, f"Слишком мало шаблонов: {templates}"
    assert lines >= 2000, f"Недостаточный объем кода: {lines}"
    print(f"Python-файлов: {python_files}")
    print(f"HTML-шаблонов: {templates}")
    print(f"Маршрутов: {len(endpoints)}")
    print(f"Таблиц: {len(tables)}")
    print(f"Логических строк: {lines}")
    print("Статическая проверка завершена успешно.")


if __name__ == "__main__":
    main()
