import hashlib
import tempfile

from pathlib import Path

import yaml

from suil.sdk.errors import ManifestError
from suil.sdk.models import Release

from .get_module_version import get_module_version
from .load_index import load_index
from .pack_module import pack_module
from .split_tag import split_tag


def add_release(tag: str, base_dir: Path) -> Release:
    """Pack the module a tag names and record it in base_dir/index.yaml as its only release."""
    modules_dir, file = Path(base_dir) / 'modules', Path(base_dir) / 'index.yaml'
    name, version = split_tag(tag, modules_dir)

    if (current := get_module_version(modules_dir / name)) != version:
        raise ManifestError(f'{tag}: modules/{name}/.cz.yaml is at {current}, not {version}')

    with tempfile.TemporaryDirectory() as out_dir:
        digest = hashlib.sha256(pack_module(tag, modules_dir, Path(out_dir)).read_bytes()).hexdigest()

    index = load_index(file)
    release = Release(version=version, url=f'{tag}.tar.gz', sha256=digest)
    index.modules[name] = [release]
    file.write_text(yaml.safe_dump(index.model_dump(), sort_keys=False))

    return release
