import yaml

from pathlib import Path


def yaml_load(file: Path) -> dict | None:
    # A hierarchy layer is optional: a missing file is an empty layer.
    if not Path(file).is_file():
        return None

    with open(file) as stream:
        try:
            return yaml.safe_load(stream)
        except yaml.YAMLError:
            return None
