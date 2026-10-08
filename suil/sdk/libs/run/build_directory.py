from datetime import datetime, timezone
from pathlib import Path

import yaml

from ..config.strip_secrets import strip_secrets

STAMP = '%Y-%m-%dT%H-%M-%SZ'


def build_directory(catalogue: dict, runs_dir: Path) -> Path:
    """Materialise the run catalogue on disk before anything is changed.

    Secrets go in as their digests: the directory exists to be read and diffed,
    which a plaintext password on disk would make impossible to leave lying about.
    """
    runs_dir = Path(runs_dir)
    directory = runs_dir / datetime.now(timezone.utc).strftime(STAMP)
    directory.mkdir(parents=True, exist_ok=True)

    for name, entry in catalogue.items():
        node_dir = directory / name
        node_dir.mkdir(exist_ok=True)

        (node_dir / 'node.yaml').write_text(yaml.safe_dump(
            {key: entry[key] for key in ('role', 'family', 'release', 'deployment', 'modules')},
            default_flow_style=False, sort_keys=False))

        for module, config in entry.get('public', {}).items():
            # The caller hands over the public view already, but a Secret that
            # slipped through would be written out here - and safe_dump would
            # refuse a str subclass rather than say why.
            (node_dir / f'{module}.yaml').write_text(yaml.safe_dump(
                strip_secrets(config), default_flow_style=False, sort_keys=False))

    latest = runs_dir / 'latest'
    latest.unlink(missing_ok=True)
    latest.symlink_to(directory.name)

    return directory


def read_directory(runs_dir: Path, name: str = 'latest') -> dict:
    directory = Path(runs_dir) / name
    catalogue: dict[str, dict] = {}

    if not directory.is_dir():
        return catalogue

    for node_dir in sorted(directory.iterdir()):
        if not node_dir.is_dir():
            continue

        entry = yaml.safe_load((node_dir / 'node.yaml').read_text()) or {}
        # `public`, not `configs`: what is on disk is the digested view, and
        # `configs` in a live catalogue means the models, secrets and all.
        entry['public'] = {
            item.stem: yaml.safe_load(item.read_text()) or {}
            for item in sorted(node_dir.glob('*.yaml')) if item.name != 'node.yaml'
        }
        catalogue[node_dir.name] = entry

    return catalogue
