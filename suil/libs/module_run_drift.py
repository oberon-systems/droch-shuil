from pathlib import Path

from .module_diff_configs import module_diff_configs
from .module_load_code import module_load_code


def module_run_drift(module: str, config, facts: dict, modules_dir: Path) -> list[str]:
    """Every path where the facts still differ from what the module expects."""
    code = module_load_code(module, modules_dir)
    hook = getattr(code, 'expected', None) if code else None

    if not hook:
        return []

    return ['.'.join(map(str, path)) for path in module_diff_configs(hook(config), facts)]
