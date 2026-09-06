from pathlib import Path

from pyinfra.api.deploy import add_deploy

from suil.errors import ModuleError

from .module_load_code import module_load_code


def module_run_code(state, host, module: str, config, diff, modules_dir: Path) -> bool:
    """Queue the module's operations for one host. False means a meta module.

    `diff` names what is out of step; None is the whole config, which only
    --force asks for.
    """
    code = module_load_code(module, modules_dir)

    if code is None:
        return False

    entry = getattr(code, 'deploy', None)

    if entry is None:
        raise ModuleError(f'modules/{module}/code/main.py declares no deploy()')

    add_deploy(state, entry, config, diff, host=host)

    return True
