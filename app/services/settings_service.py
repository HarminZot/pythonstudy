from ..models import SystemSetting


DEFAULT_SETTINGS = {
    "registration_enabled": "true",
    "code_time_limit": "3",
    "code_memory_limit": "128",
    "notifications_enabled": "true",
}


def get_setting(key, default=None):
    record = SystemSetting.query.filter_by(setting_key=key).first()
    if record:
        return record.setting_value
    return DEFAULT_SETTINGS.get(key, default)


def get_bool_setting(key, default=False):
    value = get_setting(key)
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def get_int_setting(key, default, minimum=None, maximum=None):
    try:
        value = int(get_setting(key, default))
    except (TypeError, ValueError):
        value = default
    if minimum is not None:
        value = max(minimum, value)
    if maximum is not None:
        value = min(maximum, value)
    return value
