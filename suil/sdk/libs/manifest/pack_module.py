import gzip
import tarfile

from pathlib import Path

from suil.sdk.errors import ManifestError

from .get_version_key import get_version_key


def pack_module(tag: str, modules_dir: Path, out_dir: Path) -> Path:
    """The archive of the module a <module>-<version> tag names, the same bytes on every build."""
    names = sorted(entry.name for entry in Path(modules_dir).iterdir() if entry.is_dir()) \
        if Path(modules_dir).is_dir() else []
    found = [name for name in names if tag.startswith(f'{name}-') and get_version_key(tag.removeprefix(f'{name}-'))]

    if len(found) != 1:
        raise ManifestError(f'{tag} is not <module>-<semver> for a module in {modules_dir}')

    archive = Path(out_dir) / f'{tag}.tar.gz'
    archive.parent.mkdir(parents=True, exist_ok=True)

    with archive.open('wb') as raw, gzip.GzipFile(filename='', mode='wb', fileobj=raw, mtime=0) as zipped, \
            tarfile.open(fileobj=zipped, mode='w', format=tarfile.GNU_FORMAT) as tar:
        tar.add(Path(modules_dir) / found[0], arcname=found[0], filter=_normal)

    return archive


def _normal(info: tarfile.TarInfo) -> tarfile.TarInfo | None:
    if '__pycache__' in info.name.split('/') or info.name.endswith('.pyc'):
        return None

    info.mtime, info.uid, info.gid, info.uname, info.gname = 0, 0, 0, '', ''
    info.mode = 0o755 if info.isdir() or info.mode & 0o111 else 0o644

    return info
