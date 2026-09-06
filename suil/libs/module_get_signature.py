import hashlib

from pathlib import Path

# What the signature covers: everything that changes what the module does.
SIGNED = ('code', 'data', 'files', 'templates', 'facts')
SIGNED_FILES = ('requires.yaml',)


def module_get_signature(module: str, modules_dir: Path) -> str:
    root = Path(modules_dir) / module
    digest = hashlib.sha256()
    paths: list[Path] = []

    for name in SIGNED:
        directory = root / name

        if directory.is_dir():
            paths += [item for item in directory.rglob('*')
                      if item.is_file() and '__pycache__' not in item.parts]

    paths += [root / name for name in SIGNED_FILES if (root / name).is_file()]

    for path in sorted(paths, key=lambda item: item.relative_to(root).as_posix()):
        digest.update(path.relative_to(root).as_posix().encode())
        digest.update(b'\0')
        digest.update(path.read_bytes())
        digest.update(b'\0')

    return 'sha256:' + digest.hexdigest()
