from pathlib import Path

from .module_load_code import module_load_code


def module_get_expected(module: str, config, modules_dir: Path) -> dict:
    """What the collector should report on a converged host.

    A module without expected() is compared against its own config, which for a
    module whose facts do not share that shape simply means it always runs.
    """
    code = module_load_code(module, modules_dir)
    hook = getattr(code, 'expected', None) if code else None

    if hook is None:
        return config if isinstance(config, dict) else config.model_dump(exclude={'suil'})

    return hook(config)
