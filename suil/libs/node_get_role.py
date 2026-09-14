from pathlib import Path

from .yaml_load_data import yaml_load_data


def node_get_role(node: str, nodes_dir: Path) -> str | None:
    data = yaml_load_data(nodes_dir / (node + '.yaml'))

    return data.get('role') if data else None
