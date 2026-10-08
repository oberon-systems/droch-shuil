def diff_names(diff, collection: str) -> set[str] | None:
    """The entries of `collection` the diff names. None means every entry.

    Tuple paths are what make this exact: a package called python3.12-devel is
    one segment, where a dotted key could not say where the name ended.
    """
    if diff is None:
        return None

    return {path[1] for path in diff if len(path) > 1 and path[0] == collection}
