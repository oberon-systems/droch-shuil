from pathlib import Path

from suil.errors import DataError

from .yaml_load import yaml_load


def module_get_requires(module: str, modules_dir: Path) -> list[str]:
    data = yaml_load(Path(modules_dir) / module / 'requires.yaml') or {}
    requires = data.get('requires', [])

    if not isinstance(requires, list):
        raise DataError(f"modules/{module}/requires.yaml: 'requires' must be a list")

    return list(requires)
