from suil.sdk.models import Root

from ..merge.deep import deep
from ..yaml.load_data import load_data


def get_defaults(root: Root) -> dict:
    defaults = {}

    for file in sorted((root.path / 'data').glob('*.yaml')):
        defaults = deep(defaults, load_data(file) or {})

    return defaults
