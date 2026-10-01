from pathlib import Path

from ..yaml.load import load


def get_facts(node: str, module: str, facts_dir: Path) -> dict:
    return load(Path(facts_dir) / node / f'{module}.yaml') or {}
