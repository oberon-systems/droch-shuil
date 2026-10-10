from suil.sdk.models import Root

from ..merge.deep import deep
from ..yaml.load_data import load_data


def get_defaults(root: Root, family: str | None = None, release: int | None = None) -> dict:
    files = sorted((root.path / 'data').glob('*.yaml'))

    if family is not None and release is not None:
        files.append(root.path / 'data' / 'os' / str(family) / f'{release}.yaml')

    defaults = {}

    for file in files:
        if file.is_file():
            defaults = deep(defaults, load_data(file) or {})

    return defaults
