import hashlib
import shutil
import tarfile
import tempfile

from io import BytesIO
from pathlib import Path
from urllib.parse import urljoin

from suil.sdk.errors import ManifestError
from suil.sdk.models import Index

from .get_module_version import get_module_version
from .read_url import read_url


def _installed(module_dir: Path) -> str | None:
    try:
        return get_module_version(module_dir)
    except ManifestError:
        return None


def install_module(url: str, index: Index, name: str, version: str, modules_dir: Path, force: bool = False) -> bool:
    """Lay one module at its version from the source at `url` into modules/, replacing what is there;
    False, with nothing downloaded, when modules/ already holds that version and `force` is off."""
    if not (release := next((item for item in index.modules.get(name, []) if item.version == version), None)):
        raise ManifestError(f'modules.yaml: {name} {version} is not in the index of {url}; set a version it lists')

    if not force and _installed(Path(modules_dir) / name) == version:
        return False

    location = urljoin(f"{url.rstrip('/')}/", release.url)
    archive = read_url(location)

    if (digest := hashlib.sha256(archive).hexdigest()) != release.sha256:
        raise ManifestError(f'{location}: sha256 {digest}, the index says {release.sha256}; nothing installed')

    with tempfile.TemporaryDirectory(prefix='suil-install-') as temp:
        try:
            with tarfile.open(fileobj=BytesIO(archive)) as tar:
                tar.extractall(temp, filter='data')
        except (tarfile.TarError, OSError) as error:
            raise ManifestError(f'{location} is not a module archive: {error}') from error

        if [entry.name for entry in Path(temp).iterdir()] != [name] or not (Path(temp) / name).is_dir():
            raise ManifestError(f'{location} must hold {name}/ and nothing else; nothing installed')

        shutil.rmtree(Path(modules_dir) / name, ignore_errors=True)
        shutil.copytree(Path(temp) / name, Path(modules_dir) / name)

    return True
