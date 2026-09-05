from copy import deepcopy


def deep_merge(lower: dict, upper: dict) -> dict:
    merged = deepcopy(lower)

    for key, value in (upper or {}).items():
        current = merged.get(key)

        if isinstance(current, dict) and isinstance(value, dict):
            merged[key] = deep_merge(current, value)
        elif isinstance(current, list) and isinstance(value, list):
            merged[key] = current + deepcopy(value)
        else:
            merged[key] = deepcopy(value)

    return merged
