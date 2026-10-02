import inspect

from pathlib import Path

from suil.sdk.errors import ModuleError

from ...protocols import Checks, DeclaresFiles, Deploys, Expects
from .load_code import load_code

PROTOCOLS = {'deploy': Deploys, 'expected': Expects, 'check': Checks, 'files': DeclaresFiles}
MANDATORY = ('deploy', 'expected')


def load_class(module: str, modules_dir: Path) -> type | None:
    """The one Module subclass of modules/<module>/code/main.py, None for a meta module."""
    # suil.sdk.module imports these libs, so Module cannot be imported at the top.
    from ...module import Module

    code = load_code(module, modules_dir)

    if code is None:
        return None

    source = f'modules/{module}/code/main.py'
    found = [
        value for value in vars(code).values()
        if isinstance(value, type) and issubclass(value, Module) and value is not Module
        and value.__module__ == code.__name__
    ]

    if len(found) != 1:
        names = ', '.join(sorted(value.__name__ for value in found)) or 'none'
        raise ModuleError(f'{source} must declare exactly one Module subclass, found: {names}')

    cls = found[0]

    for name in MANDATORY:
        if getattr(cls, name) is getattr(Module, name):
            raise ModuleError(f'{source}: {cls.__name__} does not override {name}()')

    for name, protocol in PROTOCOLS.items():
        expected = inspect.signature(getattr(protocol, name), eval_str=True)
        actual = inspect.signature(getattr(cls, name), eval_str=True)

        if actual != expected:
            raise ModuleError(f'{source}: {cls.__name__}.{name}{actual} must be {name}{expected}')

    return cls
