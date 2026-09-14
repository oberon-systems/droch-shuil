from pathlib import Path

from .yaml_load_data import yaml_load_data


def role_get_nodes(role: str, nodes_dir: Path) -> set[str]:
    nodes = set()

    for file in nodes_dir.glob('*.yaml'):

        if data := yaml_load_data(file):
            if data.get('role') == role:
                nodes.add(file.with_suffix('').name)

    return nodes
