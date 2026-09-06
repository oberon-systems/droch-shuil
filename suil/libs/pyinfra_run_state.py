from pyinfra.api import Config, State
from pyinfra.api.connect import connect_all
from pyinfra.api.operations import run_ops
from pyinfra.api.state import StateStage

from pyinfra_cli.prints import print_meta, print_results


def pyinfra_make_state(inventory, sudo: bool = True) -> State:
    state = State(inventory, Config(SUDO=sudo))
    state.print_output = True
    state.set_stage(StateStage.Setup)

    return state


def pyinfra_connect(state: State) -> State:
    state.set_stage(StateStage.Connect)
    connect_all(state)
    state.set_stage(StateStage.Prepare)

    return state


def pyinfra_run_state(state: State, dry_run: bool = False) -> State:
    """Collected operations are what a dry run prints: pyinfra's own --dry is
    exactly this, everything up to run_ops and then nothing."""
    print_meta(state)

    if dry_run:
        return state

    state.set_stage(StateStage.Execute)
    run_ops(state)
    state.set_stage(StateStage.Disconnect)
    print_results(state)

    return state
