from pathlib import Path

from .module_load_code import module_load_code


def module_get_files(module: str, config, modules_dir: Path) -> dict:
    """The files the module puts on the host, path to content, None for a file that must go."""
    code = module_load_code(module, modules_dir)
    hook = getattr(code, 'managed_files', None) if code else None

    return dict(hook(config)) if hook else {}
