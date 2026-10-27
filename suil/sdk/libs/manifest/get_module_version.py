from pathlib import Path

import yaml

from suil.sdk.errors import ManifestError


def get_module_version(module_dir: Path) -> str:
    """The version of a module, `version:` of the commitizen config in its .cz.yaml."""
    file = Path(module_dir) / '.cz.yaml'

    try:
        version = (yaml.safe_load(file.read_text()) or {}).get('commitizen', {}).get('version')
    except (OSError, AttributeError, yaml.YAMLError) as error:
        raise ManifestError(f'{file} has no commitizen version: {error}') from error

    if not isinstance(version, str):
        raise ManifestError(f'{file} has no commitizen version')

    return version
