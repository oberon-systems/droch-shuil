import re

SEMVER = re.compile(r'(\d+)\.(\d+)\.(\d+)(?:-([0-9A-Za-z.-]+))?(?:\+[0-9A-Za-z.-]+)?')


def get_version_key(version: str) -> tuple | None:
    """A sort key of a semver version, a pre-release below its release; None when it is not one."""
    if not (found := SEMVER.fullmatch(version)):
        return None

    major, minor, patch, pre = found.groups()
    parts = tuple((0, int(part), '') if part.isdigit() else (1, 0, part) for part in pre.split('.')) if pre else ()

    return int(major), int(minor), int(patch), not pre, parts
