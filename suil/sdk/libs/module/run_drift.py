from pathlib import Path

from .diff_configs import diff_configs
from .load_code import load_code


def run_drift(module: str, config, facts: dict, modules_dir: Path) -> list[str]:
    """Every path where the facts still differ from what the module expects."""
    code = load_code(module, modules_dir)
    hook = getattr(code, 'expected', None) if code else None

    if not hook:
        return []

    return ['.'.join(map(str, path)) for path in diff_configs(hook(config), facts)]
