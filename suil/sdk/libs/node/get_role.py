from pathlib import Path

from ..yaml.load_data import load_data


def get_role(node: str, nodes_dir: Path) -> str | None:
    data = load_data(nodes_dir / (node + '.yaml'))

    return data.get('role') if data else None
