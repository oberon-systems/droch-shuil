from suil.sdk.errors import DataError
from suil.sdk.models import Lookup

from ..inventory.lookup import lookup


def expand_lookups(data, views: dict, node: str):
    """Replace every !LOOKUP marker with what it found among the nodes of the run.

    In a list a marker splices, so literals and lookups sit side by side in one
    list; anywhere else it becomes the list of values it matched.
    """
    if isinstance(data, Lookup):
        return _found(data, views, node)

    if isinstance(data, dict):
        return {key: expand_lookups(value, views, node) for key, value in data.items()}

    if isinstance(data, list):
        items = []

        for item in data:
            if isinstance(item, Lookup):
                items += _found(item, views, node)
            else:
                items.append(expand_lookups(item, views, node))

        return items

    return data


def _found(marker: Lookup, views: dict, node: str) -> list[str]:
    found = lookup(marker, views, node)

    if not found:
        raise DataError(f'{node}: !LOOKUP {marker.field} found nothing in this run')

    return found
