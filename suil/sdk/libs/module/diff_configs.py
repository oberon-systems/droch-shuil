def diff_configs(expected, facts, path: tuple = ()) -> dict:
    """Recursive diff of what the config asks for against what the host reports.

    Only keys `expected` names are compared: a fact the module reports beyond
    them is extra information, not drift. The key is the path as a tuple, so a
    collection entry whose name contains a dot stays one segment.
    """
    diff: dict[tuple, dict] = {}

    if isinstance(expected, dict):
        # Absent is not a type mismatch: recurse so the diff names every leaf,
        # or a module with no facts yet would be told nothing differs.
        if facts is None:
            facts = {}

        if not isinstance(facts, dict):
            return {path or ('.',): {'expected': expected, 'actual': facts}}

        for key, value in expected.items():
            diff |= diff_configs(value, facts.get(key), path + (key,))

        return diff

    if expected != facts:
        return {path or ('.',): {'expected': expected, 'actual': facts}}

    return diff
