import yaml

from suil.config import cfg
from suil.directory import directory
from suil.libs import role_get_nodes


def deployment_targets(roles=(), nodes=()) -> list[str]:
    targets = []

    for role in roles:
        for node in sorted(role_get_nodes(role, cfg.nodes_dir)):
            if node not in targets:
                targets.append(node)

    for node in nodes:
        if node not in targets:
            targets.append(node)

    return targets


def deployment(roles=(), nodes=(), modules=()) -> dict:
    catalogue = {}

    for name in deployment_targets(roles, nodes):
        node = directory.node(name)
        selected = [m for m in node.modules if not modules or m in modules]

        catalogue[name] = {
            'role': node.role,
            'deployment': node.deployment,
            'modules': selected,
            'configs': {module: node.configs[module] for module in selected},
        }

    print(yaml.safe_dump(catalogue, default_flow_style=False, sort_keys=False))

    # todo: run the modules through the pyinfra api, in requires order
    return catalogue
