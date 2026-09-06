import logging

from pyinfra import logger
from pyinfra.api import Config, State
from pyinfra.api.connect import connect_all
from pyinfra.api.exceptions import PyinfraError
from pyinfra.api.operations import run_ops
from pyinfra.api.state import BaseStateCallback, StateStage

from pyinfra_cli.log import setup_logging
from pyinfra_cli.prints import print_meta, print_results

from suil.config import cfg
from suil.errors import DeploymentError


class Failures(BaseStateCallback):
    """pyinfra reports a failure by shrinking the inventory and raising much
    later, so the host and operation have to be caught as they happen."""

    def __init__(self):
        self.seen = []
        self.refused = []

    def operation_host_error(self, state, host, op_hash, retry_attempt=0, retries=0):
        if (host, op_hash) not in self.seen:
            self.seen.append((host, op_hash))

    def host_connect_error(self, state, host, error):
        self.refused.append((host, error))


def pyinfra_make_state(inventory, sudo: bool = True) -> State:
    # The API leaves its logger at WARNING, which hides the operation names and
    # the output of the command that failed - only "Error" survives.
    if not logger.handlers:
        setup_logging(logging.INFO)

    # Empty is not a password: an initial run against a cloud image sudo's with
    # none at all, and `or None` keeps that the same as leaving it unset.
    state = State(inventory, Config(SUDO=sudo, SUDO_PASSWORD=cfg.sudo_password or None))
    state.print_output = True
    state.add_callback_handler(Failures())
    state.set_stage(StateStage.Setup)

    return state


def pyinfra_connect(state: State) -> State:
    state.set_stage(StateStage.Connect)

    try:
        connect_all(state)
    except PyinfraError as error:
        raise DeploymentError(pyinfra_read_failures(state) or str(error)) from error

    state.set_stage(StateStage.Prepare)

    return state


def pyinfra_run_state(state: State, dry_run: bool = False) -> State:
    """Collected operations are what a dry run prints: pyinfra's own --dry is
    exactly this, everything up to run_ops and then nothing."""
    print_meta(state)

    if dry_run:
        return state

    state.set_stage(StateStage.Execute)

    try:
        run_ops(state)
    except PyinfraError as error:
        raise DeploymentError(pyinfra_read_failures(state) or str(error)) from error

    state.set_stage(StateStage.Disconnect)
    print_results(state)

    return state


def pyinfra_read_failures(state: State) -> str:
    """What actually went wrong, in the order it went wrong."""
    lines = []

    for handler in state.callback_handlers:
        if not isinstance(handler, Failures):
            continue

        for host, error in handler.refused:
            lines.append(f'{host.name}: cannot connect')
            lines.append(f'    {error}')

        for host, op_hash in handler.seen:
            name = ', '.join(sorted(state.get_op_meta(op_hash).names)) or op_hash
            lines.append(f'{host.name}: {name}')

            for line in _output(state, host, op_hash):
                lines.append(f'    {line}')

    failed = sorted(host.name for host in state.failed_hosts)

    if not lines:
        if not failed:
            return ''

        # A fact that could not be read fails the host without an operation to
        # blame; pyinfra has already logged which one above.
        lines.append('failed: ' + ', '.join(failed))

    remaining = sorted(host.name for host in state.active_hosts)
    lines.append('no node left to run on' if not remaining
                 else 'still running on: ' + ', '.join(remaining))

    return 'the run stopped\n\n' + '\n'.join(lines)


def _output(state: State, host, op_hash) -> list[str]:
    try:
        meta = state.get_op_data_for_host(host, op_hash).operation_meta
        reported = meta.stderr_lines or meta.stdout_lines
    except (KeyError, AssertionError, AttributeError):
        return ['the target reported nothing']

    return [line for line in reported if line.strip()] or ['the target reported nothing']
