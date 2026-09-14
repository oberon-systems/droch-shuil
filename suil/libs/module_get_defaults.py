from pathlib import Path

from .deep_merge import deep_merge
from .yaml_load_data import yaml_load_data


def module_get_defaults(module: str, modules_dir: Path) -> dict:
    defaults = {}

    for file in sorted((modules_dir / module / 'data').glob('*.yaml')):
        defaults = deep_merge(defaults, yaml_load_data(file) or {})

    return defaults
