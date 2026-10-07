from suil.sdk.errors import DataError
from suil.sdk.models import Root

from ..yaml.load_data import load_data


def get_requires(root: Root) -> list[str]:
    data = load_data(root.path / 'requires.yaml') or {}
    requires = data.get('requires', [])

    if not isinstance(requires, list):
        raise DataError(f"modules/{root.name}/requires.yaml: 'requires' must be a list")

    return list(requires)
