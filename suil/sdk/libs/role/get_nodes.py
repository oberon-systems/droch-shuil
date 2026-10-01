from pathlib import Path

from ..yaml.load_data import load_data


def get_nodes(role: str, nodes_dir: Path) -> set[str]:
    nodes = set()

    for file in nodes_dir.glob('*.yaml'):

        if data := load_data(file):
            if data.get('role') == role:
                nodes.add(file.with_suffix('').name)

    return nodes
