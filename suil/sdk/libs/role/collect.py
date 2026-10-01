from os.path import splitext
from pathlib import Path


def collect(roles_dir: Path) -> set[str]:
    roles = set()

    for file in roles_dir.rglob('*.yaml'):
        roles.add(splitext(Path(file).name)[0])

    return roles
