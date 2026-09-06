import fnmatch

from suil.models import Lookup


def inventory_lookup(lookup: Lookup, views: dict, node: str | None = None) -> list[str]:
    """One !LOOKUP against the inventory: every matching node's field, rendered.

    Sorted by node key, and that is not cosmetic - the order reaches a rendered
    file, its digest and therefore the diff gate that decides whether a daemon
    is restarted.
    """
    found = []

    for name in sorted(views):
        if lookup.scope == 'exclude' and name == node:
            continue

        if lookup.scope == 'only' and name != node:
            continue

        if not fnmatch.fnmatch(name, lookup.nodes):
            continue

        data = views[name] or {}

        if lookup.role and data.get('role') != lookup.role:
            continue

        for value in _wanted(_dig(data, lookup.field), lookup.ip):
            found.append(lookup.format.format(node=name, value=value, role=data.get('role') or ''))

    return found


def _dig(data, field: str):
    for key in field.split('.'):
        if not isinstance(data, dict):
            return None

        data = data.get(key)

    return data


def _wanted(value, ip: str) -> list[str]:
    if value is None or value == '':
        return []

    values = [str(item) for item in value] if isinstance(value, (list, tuple)) else [str(value)]

    if ip == 'any':
        return values

    # An address is the only thing a family filter can mean, and a colon is
    # what separates the two families.
    return [item for item in values if (':' in item) == (ip == 'v6')]
