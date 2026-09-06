from pathlib import Path

from pyinfra.api.deploy import add_deploy

from suil.errors import ModuleError

from .module_load_code import module_load_code


def module_run_code(state, host, module: str, config, modules_dir: Path) -> bool:
    """Queue the module's operations for one host. False means a meta module."""
    code = module_load_code(module, modules_dir)

    if code is None:
        return False

    entry = getattr(code, 'deploy', None)

    if entry is None:
        raise ModuleError(f'modules/{module}/code/main.py declares no deploy()')

    add_deploy(state, entry, config, host=host)

    return True
