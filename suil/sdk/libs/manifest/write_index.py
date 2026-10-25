import hashlib
import tarfile

from pathlib import Path

import yaml

from pydantic import ValidationError

from suil.sdk.errors import ManifestError
from suil.sdk.models import Index, Release

from .get_version_key import get_version_key
from .read_index import read_index


def write_index(out_dir: Path, merge: str | None = None) -> list[str]:
    """Add every archive in out_dir to index.yaml, over the live index of the source `merge` or the one in
    out_dir; the releases added."""
    file = Path(out_dir) / 'index.yaml'
    index = read_index(merge) if merge else _read(file)
    added = []

    for archive in sorted(Path(out_dir).glob('*.tar.gz')):
        name = _name(archive)
        version = archive.name.removeprefix(f'{name}-').removesuffix('.tar.gz')
        digest = hashlib.sha256(archive.read_bytes()).hexdigest()

        if not archive.name.startswith(f'{name}-') or not get_version_key(version):
            raise ManifestError(f'{archive}: holds {name}/, so it must be named {name}-<semver>.tar.gz')

        releases = index.modules.setdefault(name, [])

        if known := next((release for release in releases if release.version == version), None):
            if known.sha256 != digest:
                raise ManifestError(f'{archive}: {name} {version} is already released with another sha256; '
                                    f'bump the version')
            continue

        releases.append(Release(version=version, url=archive.name, sha256=digest))
        added.append(f'{name}-{version}')

    for releases in index.modules.values():
        releases.sort(key=lambda release: get_version_key(release.version) or (-1,), reverse=True)

    file.write_text(yaml.safe_dump(index.model_dump(), sort_keys=False))

    return added


def _read(file: Path) -> Index:
    try:
        return Index(**(yaml.safe_load(file.read_text()) or {})) if file.is_file() else Index()
    except (TypeError, ValidationError, yaml.YAMLError) as error:
        raise ManifestError(f'{file} is not valid:\n{error}') from error


def _name(archive: Path) -> str:
    try:
        with tarfile.open(archive) as tar:
            tops = {member.name.split('/')[0] for member in tar.getmembers()}
    except tarfile.TarError as error:
        raise ManifestError(f'{archive} is not a module archive: {error}') from error

    if len(tops) != 1:
        held = ', '.join(sorted(tops)) or 'nothing'
        raise ManifestError(f'{archive} must hold one module directory, it holds {held}')

    return tops.pop()
