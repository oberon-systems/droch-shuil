from suil.models import Lookup


def config_expand_lookups(data, expand):
    """Replace every !LOOKUP marker with what it found.

    In a list a marker splices, so literals and lookups sit side by side in one
    list; anywhere else it becomes the list of values it matched.
    """
    if isinstance(data, Lookup):
        return expand(data)

    if isinstance(data, dict):
        return {key: config_expand_lookups(value, expand) for key, value in data.items()}

    if isinstance(data, list):
        items = []

        for item in data:
            if isinstance(item, Lookup):
                items += expand(item)
            else:
                items.append(config_expand_lookups(item, expand))

        return items

    return data
