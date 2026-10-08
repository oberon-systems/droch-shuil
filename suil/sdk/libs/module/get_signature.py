import hashlib

from pathlib import Path

from suil.sdk.models import Root

# What the signature covers: everything that changes what the module does.
SIGNED = ('code', 'data', 'files', 'templates', 'facts')
SIGNED_FILES = ('requires.yaml',)


def get_signature(root: Root) -> str:
    digest = hashlib.sha256()

    # A local module has no version, and its digest stays what it was before modules.yaml.
    if root.version:
        digest.update(f'{root.repo}\0{root.version}\0'.encode())

    paths: list[Path] = []

    for name in SIGNED:
        directory = root.path / name

        if directory.is_dir():
            paths += [item for item in directory.rglob('*')
                      if item.is_file() and '__pycache__' not in item.parts]

    paths += [root.path / name for name in SIGNED_FILES if (root.path / name).is_file()]

    for path in sorted(paths, key=lambda item: item.relative_to(root.path).as_posix()):
        digest.update(path.relative_to(root.path).as_posix().encode())
        digest.update(b'\0')
        digest.update(path.read_bytes())
        digest.update(b'\0')

    return 'sha256:' + digest.hexdigest()
