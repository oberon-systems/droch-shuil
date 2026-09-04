from suil.directory import directory

def node_get_role(node: str) -> str|None:
    return directory.node(node).get('role')
