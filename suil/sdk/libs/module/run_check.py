from pathlib import Path

from .load_code import load_code


def run_check(module: str, config, facts: dict, modules_dir: Path) -> list[str]:
    """What the module finds broken on the host, judged from the facts alone."""
    code = load_code(module, modules_dir)
    hook = getattr(code, 'check', None) if code else None

    return list(hook(config, facts)) if hook else []
