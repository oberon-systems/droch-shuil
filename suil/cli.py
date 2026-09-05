import click

from suil.deployment import deployment
from suil.tui import tui


@click.group(invoke_without_command=True)
@click.pass_context
def main(ctx):
    """Balor Suil: an infrastructure manager."""
    if ctx.invoked_subcommand is None:
        tui()


@main.command()
@click.option('--role', 'roles', multiple=True, help='Role to deploy, repeatable.')
@click.option('--node', 'nodes', multiple=True, help='Node to deploy, repeatable.')
@click.option('--module', 'modules', multiple=True, help='Narrow the run to these modules.')
@click.option('--force', is_flag=True, help='Run the modules even when nothing changed.')
@click.option('--confirm', is_flag=True, help='Already confirmed: do not ask before applying.')
def apply(roles, nodes, modules, force, confirm):
    """Apply the modules of the selected roles and nodes."""
    if not roles and not nodes:
        raise click.UsageError('give at least one --role or --node')

    deployment(roles=roles, nodes=nodes, modules=modules, force=force, confirm=confirm)
