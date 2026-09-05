from pathlib import Path

from .deep_merge import deep_merge
from .yaml_load import yaml_load


def module_get_defaults(module: str, modules_dir: Path) -> dict:
    defaults = {}

    for file in sorted((modules_dir / module / 'data').glob('*.yaml')):
        defaults = deep_merge(defaults, yaml_load(file) or {})

    return defaults
