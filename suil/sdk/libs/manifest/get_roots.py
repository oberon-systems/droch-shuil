from pathlib import Path

from suil.sdk.models import Manifest, Root


def get_roots(manifest: Manifest, modules_dir: Path) -> dict[str, Root]:
    return {name: Root(name=name, path=Path(modules_dir) / name) for repo in manifest.repos for name in repo.names}
