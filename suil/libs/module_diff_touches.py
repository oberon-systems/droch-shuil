def module_diff_touches(diff, *path) -> bool:
    """Whether the diff names `path` or anything below it.

    None stands for the whole config, which is what force asks for, and touches everything.
    """
    if diff is None:
        return True

    return any(key[:len(path)] == path for key in diff)
