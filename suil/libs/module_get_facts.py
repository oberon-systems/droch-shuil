from pathlib import Path

from .yaml_load import yaml_load


def module_get_facts(node: str, module: str, facts_dir: Path) -> dict:
    return yaml_load(Path(facts_dir) / node / f'{module}.yaml') or {}
