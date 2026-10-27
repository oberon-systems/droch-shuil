import hashlib
import shutil

from pathlib import Path

from suil.sdk.errors import ManifestError

from .get_module_version import get_module_version
from .load_index import load_index
from .pack_module import pack_module
from .split_tag import split_tag


def pack_release(tag: str, base_dir: Path) -> Path:
    """The archive of the release a tag names in base_dir/dist, beside index.yaml, as index.yaml records it."""
    modules_dir, file, dist = Path(base_dir) / 'modules', Path(base_dir) / 'index.yaml', Path(base_dir) / 'dist'
    name, version = split_tag(tag, modules_dir)

    if (current := get_module_version(modules_dir / name)) != version:
        raise ManifestError(f'{tag}: modules/{name}/.cz.yaml is at {current}, not {version}')

    known = next((release for release in load_index(file).modules.get(name, []) if release.version == version), None)

    if known is None:
        raise ManifestError(f'{tag} is not in index.yaml; release it with cz bump in modules/{name}')

    archive = pack_module(tag, modules_dir, dist)

    if hashlib.sha256(archive.read_bytes()).hexdigest() != known.sha256:
        archive.unlink()
        raise ManifestError(f'{tag}: modules/{name} differs from what index.yaml records; bump it again')

    shutil.copyfile(file, dist / 'index.yaml')

    return archive
