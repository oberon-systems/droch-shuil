import logging

import click
import yaml

from suil.config import Config
from suil.deployment import Deployment
from suil.directory import Directory
from suil.errors import errors_handler
from suil.libs import module_get_names, module_get_order, module_get_requires, string_decrypt, string_encrypt
from suil.log import log_setup
from suil.tui import tui
from suil.workspace import Workspace

log = logging.getLogger(__name__)


def _selection(function):
    function = click.option('--role', help='Role to act on.')(function)
    function = click.option('--node', help='Node to act on.')(function)

    return function


@click.group(invoke_without_command=True)
@click.pass_context
def main(ctx):
    """Balor Suil: an infrastructure manager."""
    workspace = Workspace()
    settings = Config()
    log_setup(settings.log_color)

    if ctx.invoked_subcommand is None:
        tui(workspace, settings)
        return

    ctx.obj = (workspace, settings)


@main.command()
@_selection
@click.option('--force', is_flag=True, help='Run the modules even when nothing changed.')
@click.option('--confirm', is_flag=True, help='Apply; without it the run is only shown.')
@click.option('--dry-run', is_flag=True, help='Show what would change and stop.')
@click.pass_obj
def apply(obj, role, node, force, confirm, dry_run):
    """Apply the modules of the selected role or node."""
    workspace, settings = obj
    directory = Directory(workspace, role=role, node=node)
    directory.show()

    if not confirm:
        log.warning('not applied: give --confirm')
        return

    Deployment(settings, directory, force=force, dry_run=dry_run).run()


@main.command()
@_selection
@click.pass_obj
def config(obj, role, node):
    """Print the run without applying anything."""
    workspace, settings = obj
    directory = Directory(workspace, role=role, node=node)
    deployment = Deployment(settings, directory)
    directory.show()

    for item in directory.nodes:
        log.info(f'--- {item.name}')
        print(yaml.safe_dump(deployment.configs(item)[1], default_flow_style=False, sort_keys=False))


@main.command()
@_selection
@click.pass_obj
def facts(obj, role, node):
    """Collect facts, change nothing."""
    workspace, settings = obj
    directory = Directory(workspace, role=role, node=node)
    deployment = Deployment(settings, directory)

    for item in directory.nodes:
        _, host, probe = deployment.connect(item)
        item = directory.probe(item.name, probe['family'], probe['release'])
        deployment.facts(host, item, *deployment.configs(item))


@main.command()
@click.pass_obj
def nodes(obj):
    """List the nodes and the role each declares."""
    workspace, _ = obj

    for name, role in sorted(Directory(workspace).inventory.items()):
        log.info(f'{name}  ({role or "no role"})')


@main.command()
@click.pass_obj
def modules(obj):
    """List the modules and the requires graph."""
    workspace, _ = obj

    for name in module_get_names(workspace.modules_dir):
        requires = module_get_requires(name, workspace.modules_dir)
        kind = 'meta' if not (workspace.modules_dir / name / 'code' / 'main.py').is_file() else 'module'
        log.info(f'{name}  [{kind}]')

        if requires:
            log.info('  requires: ' + ', '.join(requires))
            log.info('  order:    ' + ' -> '.join(module_get_order([name], workspace.modules_dir)))


@main.command('encrypt')
@click.argument('value')
@click.pass_obj
def encrypt_command(obj, value):
    """Encrypt a string to SUIL_AGE_RECIPIENT."""
    _, settings = obj
    print(f'!ENC[{string_encrypt(value, settings.age_recipient)}]')


@main.command('decrypt')
@click.argument('value')
@click.pass_obj
def decrypt_command(obj, value):
    """Decrypt a string with SUIL_AGE_KEY."""
    _, settings = obj
    print(string_decrypt(value, settings.age_key))


@errors_handler
def cli():
    main()
