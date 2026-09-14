from pathlib import Path

from suil.errors import DataError
from suil.models import Tagged

from .yaml_load import yaml_load


def _bare_key(value, path):
    if isinstance(value, Tagged):
        return None if value.strategy == 'delete' else _bare_key(value.value, path)

    if isinstance(value, dict):
        items = value.items()
    elif isinstance(value, list):
        items = enumerate(value)
    else:
        return '.'.join(path) if value is None else None

    for key, item in items:
        if (found := _bare_key(item, path + [str(key)])) is not None:
            return found

    return None


def yaml_load_data(file: Path) -> dict | None:
    # A key left with nothing but comments under it loads as None and wipes the
    # layer below it; in authored data that is a broken file, never an intent.
    data = yaml_load(file)

    if data and (path := _bare_key(data, [])) is not None:
        raise DataError(f'{file}: {path} has no value; write {{}}, [] or !delete')

    return data
