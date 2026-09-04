from pathlib import Path

from .yaml_load import yaml_load

def role_get_nodes(role: str, nodes_dir: Path) -> set[str]:
    nodes = set()

    for file in nodes_dir.glob('*.yaml'):

        if data := yaml_load(file):
            if data.get('role') == role:
                nodes.add(file.with_suffix('').name)

    return nodes
