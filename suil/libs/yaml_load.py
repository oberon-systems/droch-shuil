import yaml

from pathlib import Path

def yaml_load(file: Path) -> dict | None:
    with open(file) as stream:
        try:
            return yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            return None

