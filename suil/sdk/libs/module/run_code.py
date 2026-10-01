from pathlib import Path

from pyinfra.api.deploy import add_deploy

from suil.errors import ModuleError

from .load_code import load_code


def run_code(state, host, module: str, config, facts: dict, force: bool, modules_dir: Path) -> bool:
    """Queue the module's operations for one host. False means a meta module.

    `facts` is what the collector reported before the run, empty under --force.
    `force` asks for everything; what that means is the module's call.
    """
    code = load_code(module, modules_dir)

    if code is None:
        return False

    entry = getattr(code, 'deploy', None)

    if entry is None:
        raise ModuleError(f'modules/{module}/code/main.py declares no deploy()')

    add_deploy(state, entry, config, facts, force, host=host)

    return True
