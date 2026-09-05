import questionary

from suil.config import cfg
from suil.deployment import deployment, deployment_targets
from suil.directory import directory
from suil.libs import roles_collect


def select(message: str, choices) -> list[str]:
    if not choices:
        return []

    return questionary.checkbox(
        message,
        sorted(choices),
        use_jk_keys=False,
        use_search_filter=True,
    ).ask() or []


def roles_select() -> list[str]:
    return select(
        'Please select roles for a list for run deployment:\n',
        roles_collect(cfg.roles_dir),
    )


def nodes_select(roles: list[str]) -> list[str]:
    return select(
        'Please select nodes to run the deployment against:\n',
        deployment_targets(roles=roles),
    )


def modules_select(nodes: list[str]) -> list[str]:
    modules = []

    for node in nodes:
        for module in directory.node(node).modules:
            if module not in modules:
                modules.append(module)

    return select('Please select modules to run:\n', modules)


def tui():
    questionary.print('\n=== Balor Suil: an infrastructure manager ===\n\n')

    roles = roles_select()
    nodes = nodes_select(roles)
    modules = modules_select(nodes)

    return deployment(nodes=nodes, modules=modules)
