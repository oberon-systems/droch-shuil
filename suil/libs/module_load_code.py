import importlib.util
import sys

from pathlib import Path
from types import ModuleType

from suil.errors import ModuleError

# Modules are imported under a synthetic parent rather than off sys.path, so a
# module named `ssh` or `packages` cannot shadow an installed package.
NAMESPACE = 'suil_modules'


def _ensure_package(name: str, path: Path | None = None) -> ModuleType:
    if name in sys.modules:
        return sys.modules[name]

    package = ModuleType(name)
    package.__path__ = [str(path)] if path else []
    sys.modules[name] = package

    return package


def module_load_code(module: str, modules_dir: Path, part: str = 'main') -> ModuleType | None:
    """Import modules/<module>/code/<part>.py, or None when the module has no code."""
    code_dir = Path(modules_dir) / module / 'code'
    source = code_dir / f'{part}.py'

    if not source.is_file():
        return None

    _ensure_package(NAMESPACE, Path(modules_dir))
    _ensure_package(f'{NAMESPACE}.{module}', Path(modules_dir) / module)
    package = f'{NAMESPACE}.{module}.code'
    _ensure_package(package, code_dir)

    name = f'{package}.{part}'

    if name in sys.modules:
        return sys.modules[name]

    spec = importlib.util.spec_from_file_location(name, source)

    if spec is None or spec.loader is None:
        raise ModuleError(f'cannot import {source}')

    loaded = importlib.util.module_from_spec(spec)
    sys.modules[name] = loaded

    try:
        spec.loader.exec_module(loaded)
    except Exception as error:
        del sys.modules[name]
        raise ModuleError(f'{source} failed to import: {error}') from error

    return loaded
