from collections.abc import Mapping

from suil.sdk.errors import ModuleError, ModuleOrderError
from suil.sdk.models import Root

from .get_requires import get_requires


def get_order(modules: list[str], roots: Mapping[str, Root]) -> list[str]:
    """Depth-first post-order over `requires`, so a dependency lands before its
    dependant and the order inside a requires list is the order of the run."""
    ordered: list[str] = []
    done: set[str] = set()
    path: list[str] = []

    def visit(name: str) -> None:
        if name in done:
            return

        if name in path:
            cycle = ' -> '.join(path[path.index(name):] + [name])
            raise ModuleOrderError(f'requires form a cycle: {cycle}')

        if name not in roots:
            through = f" (required by {path[-1]})" if path else ''
            raise ModuleError(f'module {name!r} is not declared in modules.yaml{through}')

        path.append(name)

        for requirement in get_requires(roots[name]):
            visit(requirement)

        path.pop()
        done.add(name)
        ordered.append(name)

    for module in modules:
        visit(module)

    return ordered
