from pathlib import Path


def nodes_collect(nodes_dir: Path) -> set[str]:
    nodes = set()

    for file in nodes_dir.rglob('*.yaml'):
        nodes.add(file.with_suffix('').name)

    return nodes
