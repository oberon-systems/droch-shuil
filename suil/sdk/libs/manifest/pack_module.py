import gzip
import tarfile

from pathlib import Path

from .split_tag import split_tag


def pack_module(tag: str, modules_dir: Path, out_dir: Path) -> Path:
    """The archive of the module a <module>-<version> tag names, the same bytes on every build."""
    name, _ = split_tag(tag, modules_dir)

    archive = Path(out_dir) / f'{tag}.tar.gz'
    archive.parent.mkdir(parents=True, exist_ok=True)

    with archive.open('wb') as raw, gzip.GzipFile(filename='', mode='wb', fileobj=raw, mtime=0) as zipped, \
            tarfile.open(fileobj=zipped, mode='w', format=tarfile.GNU_FORMAT) as tar:
        tar.add(Path(modules_dir) / name, arcname=name, filter=_normal)

    return archive


def _normal(info: tarfile.TarInfo) -> tarfile.TarInfo | None:
    if '__pycache__' in info.name.split('/') or info.name.endswith('.pyc'):
        return None

    info.mtime, info.uid, info.gid, info.uname, info.gname = 0, 0, 0, '', ''
    info.mode = 0o755 if info.isdir() or info.mode & 0o111 else 0o644

    return info
