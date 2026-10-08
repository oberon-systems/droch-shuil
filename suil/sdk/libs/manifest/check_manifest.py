from pathlib import Path

from suil.sdk.errors import ManifestError, ModuleError
from suil.sdk.models import Config, Root

from ..module.check_facter import check_facter
from ..module.get_names import get_names
from ..module.get_order import get_order
from ..module.load_class import load_class
from ..module.load_code import load_code
from .get_checkout import get_checkout
from .get_revision import get_revision
from .get_roots import get_roots
from .read_manifest import read_manifest

# Everything a module with no code may hold.
META = {'requires.yaml', 'README.md', 'tests'}


def check_manifest(file: Path, modules_dir: Path, cache_dir: Path) -> dict[str, Root]:
    """Validate modules.yaml and every module it declares, offline; the root of each module."""
    manifest = read_manifest(file)

    for repo in manifest.repos:
        if not repo.local:
            checkout = get_checkout(cache_dir, repo.repo, repo.version)

            if not checkout.is_dir():
                raise ManifestError(f'{repo.repo} {repo.version} is not in the cache: run suil install')

            get_revision(checkout, repo)

    roots = get_roots(manifest, modules_dir, cache_dir)
    local = {name for repo in manifest.repos if repo.local for name in repo.modules}

    if undeclared := sorted(set(get_names(modules_dir)) - local):
        raise ManifestError(f"modules.yaml: modules/{', modules/'.join(undeclared)} not declared; "
                            f"add to the repo: local entry or remove")

    for root in roots.values():
        if not root.path.is_dir():
            where = 'modules/' if root.version is None else f'{root.repo} {root.version}'
            raise ManifestError(f'modules.yaml: module {root.name} is not in {where}; '
                                f'fix the name or drop it')

    get_order(sorted(roots), roots)

    for root in roots.values():
        _check_module(root)

    return roots


def _check_module(root: Root) -> None:
    if load_class(root) is None:
        if extra := sorted(entry.name for entry in root.path.iterdir() if entry.name not in META):
            raise ModuleError(f"modules/{root.name} has no code/main.py, so it is a meta module and holds only "
                              f"{', '.join(sorted(META))}; move or remove {', '.join(extra)}")

        if not (root.path / 'requires.yaml').is_file():
            raise ModuleError(f'modules/{root.name} is a meta module with no requires.yaml; add one')

        return

    config = getattr(load_code(root, part='config'), 'Config', None)

    if not (isinstance(config, type) and issubclass(config, Config)):
        raise ModuleError(f'modules/{root.name}/code/config.py must declare class Config(suil.sdk.Config)')

    check_facter(root)
