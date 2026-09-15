from pathlib import Path

from .module_load_code import module_load_code


def module_run_check(module: str, config, facts: dict, modules_dir: Path) -> list[str]:
    """What the module finds broken on the host, judged from the facts alone."""
    code = module_load_code(module, modules_dir)
    hook = getattr(code, 'check', None) if code else None

    return list(hook(config, facts)) if hook else []
