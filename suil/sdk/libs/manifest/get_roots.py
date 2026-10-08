from pathlib import Path

from suil.sdk.models import Manifest, Root

from .get_checkout import get_checkout


def get_roots(manifest: Manifest, modules_dir: Path, cache_dir: Path) -> dict[str, Root]:
    roots = {}

    for repo in manifest.repos:
        base = Path(modules_dir) if repo.local else get_checkout(cache_dir, repo.repo, repo.version)

        for name in repo.modules:
            roots[name] = Root(name=name, path=base / name, repo=repo.repo, version=repo.version)

    return roots
