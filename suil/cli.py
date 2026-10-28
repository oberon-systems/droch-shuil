import logging

import click
import yaml

from suil.config import Config
from suil.deployment import Deployment
from suil.directory import Directory, counted
from suil.errors import errors_handler
from suil.log import OK, log_setup
from suil.sdk.libs.manifest import (add_release, check_manifest, get_latest_version, install_module, pack_release,
                                    read_index, read_manifest, set_versions)
from suil.sdk.libs.module import get_order, get_requires
from suil.sdk.libs.string import decrypt, encrypt
from suil.tui import tui
from suil.workspace import Workspace

log = logging.getLogger(__name__)


def _selection(function):
    function = click.option('--role', help='Role to act on.')(function)
    function = click.option('--node', help='Node to act on.')(function)

    return function


@click.group(invoke_without_command=True)
@click.version_option(package_name='droch-shuil', prog_name='suil')
@click.pass_context
def main(ctx):
    """Suil: an infrastructure manager."""
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
    roots = _roots(workspace)

    for name, root in sorted(roots.items()):
        requires = get_requires(root)
        kind = 'meta' if not (root.path / 'code' / 'main.py').is_file() else 'module'
        log.info(f'{name}  [{kind}]')

        if requires:
            log.info('  requires: ' + ', '.join(requires))
            log.info('  order:    ' + ' -> '.join(get_order([name], roots)))


@main.command()
@click.pass_obj
def install(obj):
    """Lay the modules of every source in modules.yaml into modules/."""
    workspace, _ = obj

    for repo in read_manifest(workspace.manifest).repos:
        if repo.local:
            continue

        index = read_index(repo.repo)

        for name, version in repo.modules.items():
            install_module(repo.repo, index, name, version, workspace.modules_dir)
            log.log(OK, f'{name} {version}: {repo.repo}')


@main.command()
@click.pass_obj
def autoupdate(obj):
    """Move every module of a source in modules.yaml to the newest version in its index."""
    workspace, _ = obj
    versions = {}

    for repo in read_manifest(workspace.manifest).repos:
        if repo.local:
            continue

        index = read_index(repo.repo)
        log.info(f'{repo.repo}: index.yaml modified {index.modified or "at an unknown time"}')

        for name, version in repo.modules.items():
            if not (latest := get_latest_version(index, name)):
                log.warning(f'{name}: not in the index of {repo.repo}, {version} kept')
            elif latest != version:
                log.info(f'{name}: {version} -> {latest}')
                versions[name] = latest

    if versions:
        workspace.manifest.write_text(set_versions(workspace.manifest.read_text(), versions))
        log.warning('modules.yaml updated: run suil install')
    else:
        log.log(OK, 'modules.yaml is up to date')


@main.command('index')
@click.argument('tag')
@click.pass_obj
def index_command(obj, tag):
    """Record the release a <module>-<version> TAG names in index.yaml; cz bump runs it before its commit."""
    workspace, _ = obj
    log.log(OK, f'index.yaml: {tag} {add_release(tag, workspace.base_dir).sha256}')


@main.command()
@click.argument('tag')
@click.pass_obj
def pack(obj, tag):
    """Pack the release a <module>-<version> TAG names into dist/, beside index.yaml, checked against it."""
    workspace, _ = obj
    log.log(OK, f'{tag}: {pack_release(tag, workspace.base_dir)}')


@main.command()
@click.pass_obj
def validate(obj):
    """Check modules.yaml and every module it declares, without connecting."""
    workspace, _ = obj
    log.log(OK, f"modules.yaml: {counted(len(_roots(workspace)), 'module')} valid")


@main.command()
@click.pass_obj
def init(obj):
    """Lay out an empty workspace in the current directory."""
    workspace, _ = obj
    workspace.init()
    log.log(OK, f'{workspace.base_dir}: workspace made, declare its modules in modules.yaml')


@main.command('encrypt')
@click.argument('value')
@click.pass_obj
def encrypt_command(obj, value):
    """Encrypt a string to SUIL_AGE_RECIPIENT."""
    _, settings = obj
    print(f'!ENC[{encrypt(value, settings.age_recipient)}]')


@main.command('decrypt')
@click.argument('value')
@click.pass_obj
def decrypt_command(obj, value):
    """Decrypt a string with SUIL_AGE_KEY."""
    _, settings = obj
    print(decrypt(value, settings.age_key))


def _roots(workspace):
    return check_manifest(workspace.manifest, workspace.modules_dir)


@errors_handler
def cli():
    main()
