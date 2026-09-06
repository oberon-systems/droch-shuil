def module_diff_configs(expected, facts, path: str = '') -> dict:
    """Recursive diff of what the config asks for against what the host reports.

    Only keys `expected` names are compared: a fact the module reports beyond
    them is extra information, not drift.
    """
    diff: dict[str, dict] = {}

    if isinstance(expected, dict):
        if not isinstance(facts, dict):
            return {path or '.': {'expected': expected, 'actual': facts}}

        for key, value in expected.items():
            diff |= module_diff_configs(value, facts.get(key), f'{path}.{key}' if path else key)

        return diff

    if expected != facts:
        return {path or '.': {'expected': expected, 'actual': facts}}

    return diff
