from pathlib import Path

from ..merge.deep import deep
from ..yaml.load_data import load_data


def get_defaults(module: str, modules_dir: Path) -> dict:
    defaults = {}

    for file in sorted((modules_dir / module / 'data').glob('*.yaml')):
        defaults = deep(defaults, load_data(file) or {})

    return defaults
