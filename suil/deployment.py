import click
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


def deployment_build(roles=(), nodes=(), modules=()) -> dict:
    catalogue = {}

    for name in deployment_targets(roles, nodes):
        node = directory.node(name)
        selected = [m for m in node.modules if not modules or m in modules]

        catalogue[name] = {
            'role': node.role,
            'deployment': node.deployment,
            'modules': selected,
        }

    return catalogue


def counted(count: int, word: str) -> str:
    return f"{count} {word}{'' if count == 1 else 's'}"


def deployment_show(catalogue: dict) -> None:
    seen = []

    print('\n=== deployment ===\n')

    for name, entry in catalogue.items():
        print(f"{name} ({entry['role']})")

        for module in entry['modules']:
            print(f'  {module}')

            if module not in seen:
                seen.append(module)

        print()

    print(f"{counted(len(catalogue), 'node')}, {counted(len(seen), 'module')}\n")


def deployment(roles=(), nodes=(), modules=(), force=False, confirm=False) -> dict:
    catalogue = deployment_build(roles, nodes, modules)

    if not catalogue:
        print('nothing to deploy')
        return {}

    deployment_show(catalogue)

    if not confirm and not click.confirm('Apply?', default=False):
        return {}

    print(yaml.safe_dump(catalogue, default_flow_style=False, sort_keys=False))

    # todo: run the modules through the pyinfra api, in requires order, force as the run gate
    return catalogue
