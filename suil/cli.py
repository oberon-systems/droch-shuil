import click

from suil.config import cfg
from suil.deployment import (deployment, deployment_build, deployment_config,
                             deployment_connect, deployment_facts, deployment_targets)
from suil.errors import SuilError
from suil.libs import (module_get_names, module_get_order, module_get_requires,
                       node_get_role, nodes_collect, string_decrypt, string_encrypt)
from suil.tui import colored, info, tui, warn


def _selection(function):
    function = click.option('--role', 'roles', multiple=True,
                            help='Role to act on, repeatable.')(function)
    function = click.option('--node', 'nodes', multiple=True,
                            help='Node to act on, repeatable.')(function)

    return function


@click.group(invoke_without_command=True)
@click.pass_context
def main(ctx):
    """Balor Suil: an infrastructure manager."""
    if ctx.invoked_subcommand is None:
        tui()


@main.command()
@_selection
@click.option('--module', 'modules', multiple=True, help='Narrow the run to these modules.')
@click.option('--force', is_flag=True, help='Run the modules even when nothing changed.')
@click.option('--confirm', is_flag=True, help='Already confirmed: do not ask before applying.')
@click.option('--dry-run', is_flag=True, help='Show what would change and stop.')
def apply(roles, nodes, modules, force, confirm, dry_run):
    """Apply the modules of the selected roles and nodes."""
    if not roles and not nodes:
        raise click.UsageError('give at least one --role or --node')

    deployment(roles=roles, nodes=nodes, modules=modules,
               force=force, confirm=confirm, dry_run=dry_run)


@main.command()
@_selection
@click.option('--module', 'modules', multiple=True, help='Narrow the output to these modules.')
def config(roles, nodes, modules):
    """Print the run catalogue without applying anything."""
    if not roles and not nodes:
        raise click.UsageError('give at least one --role or --node')

    deployment_config(roles=roles, nodes=nodes, modules=modules)


@main.command()
@_selection
@click.option('--module', 'modules', multiple=True, help='Narrow the collection to these modules.')
def facts(roles, nodes, modules):
    """Collect facts, change nothing."""
    if not roles and not nodes:
        raise click.UsageError('give at least one --role or --node')

    targets = deployment_targets(roles, nodes)

    if not targets:
        warn('nothing to collect')
        return

    state = deployment_connect(targets)
    deployment_facts(state, deployment_build(targets, modules))


@main.command()
def nodes():
    """List the nodes and the role each declares."""
    for name in sorted(nodes_collect(cfg.nodes_dir)):
        info(f'{name}  ({node_get_role(name, cfg.nodes_dir) or "no role"})')


@main.command()
def modules():
    """List the modules and the requires graph."""
    names = module_get_names(cfg.modules_dir)

    for name in names:
        requires = module_get_requires(name, cfg.modules_dir)
        kind = 'meta' if not (cfg.modules_dir / name / 'code' / 'main.py').is_file() else 'module'
        info(f'{name}  [{kind}]')

        if requires:
            info('  requires: ' + ', '.join(requires))
            info('  order:    ' + ' -> '.join(module_get_order([name], cfg.modules_dir)))


@main.command('encrypt')
@click.argument('value')
def encrypt_command(value):
    """Encrypt a string to SUIL_AGE_RECIPIENT."""
    print(f'!ENC[{string_encrypt(value)}]')


@main.command('decrypt')
@click.argument('value')
def decrypt_command(value):
    """Decrypt a string with SUIL_AGE_KEY."""
    print(string_decrypt(value))


def cli():
    try:
        main()
    except SuilError as error:
        raise SystemExit(colored(f'suil: {error}', 'bad'))
