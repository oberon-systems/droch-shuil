from pathlib import Path

from suil.sdk.errors import ManifestError

from .get_version_key import get_version_key


def split_tag(tag: str, modules_dir: Path) -> tuple[str, str]:
    """The module and the version a <module>-<version> tag names, the module a directory of modules_dir."""
    names = sorted(entry.name for entry in Path(modules_dir).iterdir() if entry.is_dir()) \
        if Path(modules_dir).is_dir() else []
    found = [name for name in names if tag.startswith(f'{name}-') and get_version_key(tag.removeprefix(f'{name}-'))]

    if len(found) != 1:
        raise ManifestError(f'{tag} is not <module>-<semver> for a module in {modules_dir}')

    return found[0], tag.removeprefix(f'{found[0]}-')
