from pathlib import Path

from .yaml_load import yaml_load


def node_get_role(node: str, nodes_dir: Path) -> str | None:
    data = yaml_load(nodes_dir / (node + '.yaml'))

    return data.get('role') if data else None
