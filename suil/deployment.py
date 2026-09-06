import click
import yaml

from pyinfra.api.exceptions import PyinfraError

from suil.config import cfg
from suil.directory import directory
from suil.errors import DeploymentError, SuilError
from suil.libs import (module_collect_facts, module_diff_configs,
                       module_get_config, module_get_expected, module_get_facts,
                       module_get_public, module_get_signature, module_run_code, node_probe_os,
                       pyinfra_connect, pyinfra_make_inventory, pyinfra_make_state,
                       pyinfra_read_failures, pyinfra_run_state, role_get_nodes,
                       run_build_directory)
from suil.tui import bad, info, ok, warn


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


def deployment_connect(targets: list[str]):
    """Connect first, because the OS layer of the hierarchy is the one whose
    variables are not in the data - only the target knows them."""
    bootstrap = {name: directory.node(name).deployment for name in targets}
    state = pyinfra_connect(pyinfra_make_state(pyinfra_make_inventory(bootstrap)))

    for host in state.inventory.get_active_hosts():
        try:
            probe = node_probe_os(host, cfg.facts_dir)
        except PyinfraError as error:
            raise DeploymentError(pyinfra_read_failures(state) or str(error)) from error

        directory.probe(directory.node(host.name), probe['family'], probe['release'])

    return state


def deployment_build(targets, modules=()) -> dict:
    """The catalogue from local data alone: the OS layer comes from the cached
    probe, so the brief is printable before anything is connected to."""
    catalogue = {}

    for name in targets:
        node = directory.node(name)
        probe = module_get_facts(name, 'suil', cfg.facts_dir).get('facts') or {}

        if probe:
            directory.probe(node, probe['family'], probe['release'])

        selected = [item for item in node.modules if not modules or item in modules]
        configs = {item: module_get_config(item, node, cfg.modules_dir) for item in selected}

        catalogue[name] = {
            'role':       node.role,
            'family':     node.family,
            'release':    node.release,
            'facts':      bool(probe),
            'deployment': node.deployment,
            'modules':    selected,
            'configs':    configs,
            'public':     {item: module_get_public(item, node, configs[item])
                           for item in selected},
        }

    return catalogue


def counted(count: int, word: str) -> str:
    return f"{count} {word}{'' if count == 1 else 's'}"


def deployment_show(catalogue: dict) -> None:
    seen, blind = [], []

    info('\n=== deployment ===\n')

    for name, entry in catalogue.items():
        line = f"{name} ({entry['role']}, "

        if entry.get('facts'):
            info(line + f"{entry['family']} {entry['release']})")
        else:
            warn(line + 'no facts)')
            blind.append(name)

        for module in entry['modules']:
            info(f'  {module}')

            if module not in seen:
                seen.append(module)

        info('')

    info(f"{counted(len(catalogue), 'node')}, {counted(len(seen), 'module')}")

    if blind:
        warn('no facts for: ' + ', '.join(blind))
        warn('the modules above are provisional - the exact set and order '
             'are known only after the facts are collected')

    info('')


def deployment_gate(node: str, module: str, config, force: bool) -> tuple[bool, dict | None]:
    """What the module has to assert. None is the whole config, and only --force
    asks for that: a resource the facts already agree with stays out of the run."""
    if force:
        return True, None

    record = module_get_facts(node, module, cfg.facts_dir)
    diff = module_diff_configs(
        module_get_expected(module, config, cfg.modules_dir), record.get('facts') or {})

    if record.get('signature') != module_get_signature(module, cfg.modules_dir):
        return True, diff

    return bool(diff), diff


def deployment(roles=(), nodes=(), modules=(), force=False, confirm=False, dry_run=False) -> dict:
    targets = deployment_targets(roles, nodes)

    if not targets:
        warn('nothing to deploy')
        return {}

    catalogue = deployment_build(targets, modules)

    if not catalogue:
        warn('nothing to deploy')
        return {}

    deployment_show(catalogue)

    if not confirm and not click.confirm('Apply?', default=False):
        return {}

    state = deployment_connect(targets)
    catalogue = deployment_build(targets, modules)

    # Every run, not only the first: a record from last time describes the host
    # as it was, and the gate would call a machine converged that somebody has
    # since taken the accounts off.
    deployment_facts(state, catalogue)

    directory_path = run_build_directory(catalogue, cfg.runs_dir)
    info(f'run catalogue: {directory_path}\n')
    applied = []

    for host in state.inventory.get_active_hosts():
        entry = catalogue[host.name]

        for module in entry['modules']:
            config = entry['configs'][module]
            run, diff = deployment_gate(host.name, module, config, force)

            if not run:
                ok(f'{host.name}: {module} is converged, skipping')
                continue

            if diff:
                warn(f'{host.name}: {module} differs at '
                     + ', '.join(sorted('.'.join(path) for path in diff)))

            if module_run_code(state, host, module, config, diff, cfg.modules_dir):
                applied.append((host.name, module))

    pyinfra_run_state(state, dry_run=dry_run)

    if dry_run:
        warn('\ndry run: nothing applied\n')
    elif not applied:
        ok('\nnothing to apply, every module is converged\n')
    else:
        deployment_facts(state, catalogue, only=applied)
        ok(f"\napplied: {counted(len({node for node, _ in applied}), 'node')}, "
           f"{counted(len(applied), 'module')}\n")

    return catalogue


def deployment_facts(state, catalogue: dict, only=None) -> None:
    """Read the target. `only` narrows to the (node, module) pairs given."""
    info('\n--> Collecting facts...')

    for host in state.inventory.get_active_hosts():
        for module in catalogue[host.name]['modules']:
            if only is not None and (host.name, module) not in only:
                continue

            try:
                module_collect_facts(host, module, catalogue[host.name]['public'][module],
                                     cfg.modules_dir, cfg.facts_dir)
            except SuilError as error:
                bad(f'{host.name}: {module} facts not collected: {error}')


def deployment_config(roles=(), nodes=(), modules=()) -> dict:
    """The run catalogue and nothing else: resolve and print, never connect."""
    targets = deployment_targets(roles, nodes)

    if not targets:
        return {}

    catalogue = deployment_build(targets, modules)
    deployment_show(catalogue)

    for name, entry in catalogue.items():
        info(f'--- {name}')
        print(yaml.safe_dump(entry['public'], default_flow_style=False, sort_keys=False))

    return catalogue
