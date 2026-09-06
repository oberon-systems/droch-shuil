from copy import deepcopy

from suil.models import Tagged

DELETED = object()


def _dedupe(items: list) -> list:
    seen = []

    for item in items:
        if item not in seen:
            seen.append(item)

    return seen


def _merge_by_name(lower: list, upper: list) -> list:
    merged = [deepcopy(item) for item in lower]
    index = {item.get('name'): position
             for position, item in enumerate(merged)
             if isinstance(item, dict) and 'name' in item}

    for item in upper:
        name = item.get('name') if isinstance(item, dict) else None

        if name is not None and name in index:
            merged[index[name]] = deep_merge(merged[index[name]], item)
        else:
            if name is not None:
                index[name] = len(merged)
            merged.append(deepcopy(item))

    return merged


def _apply(key, current, tagged: Tagged):
    if tagged.strategy == 'delete':
        if tagged.value is None or not isinstance(current, list):
            return DELETED

        drop = tagged.value if isinstance(tagged.value, list) else [tagged.value]
        return [item for item in current if item not in drop]

    if tagged.strategy == 'replace':
        return deepcopy(tagged.value)

    if tagged.strategy == 'merge':
        if not isinstance(current, list) or not isinstance(tagged.value, list):
            return deepcopy(tagged.value)

        return _merge_by_name(current, tagged.value)

    return deep_merge({key: current}, {key: tagged.value})[key]


def deep_merge(lower: dict, upper: dict) -> dict:
    merged = deepcopy(lower)

    for key, value in (upper or {}).items():
        current = merged.get(key)

        if isinstance(value, Tagged):
            result = _apply(key, current, value)

            if result is DELETED:
                merged.pop(key, None)
            else:
                merged[key] = result

            continue

        if isinstance(current, dict) and isinstance(value, dict):
            merged[key] = deep_merge(current, value)
        elif isinstance(current, list) and isinstance(value, list):
            # `modules` is the one list that must never carry a duplicate: it is
            # the run order, and an entry twice is a module applied twice.
            merged[key] = current + deepcopy(value)
            if key == 'modules':
                merged[key] = _dedupe(merged[key])
        else:
            merged[key] = deepcopy(value)

    return merged


def deep_merge_unwrap(data):
    """Drop any strategy tag a bottom layer carried and nothing merged over."""
    if isinstance(data, Tagged):
        return None if data.strategy == 'delete' else deep_merge_unwrap(data.value)

    if isinstance(data, dict):
        return {key: deep_merge_unwrap(value) for key, value in data.items()}

    if isinstance(data, list):
        return [deep_merge_unwrap(item) for item in data]

    return data
